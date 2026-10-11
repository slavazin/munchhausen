"""Arm runner (SPEC § 10.4): workers claim indices from `cursors`, hold TTL leases, and close rounds.

Round barrier: all episodes of round r are written before round r's episodic pass, and round r+1 starts
after it. Consultation at index i then depends only on (seed, i), not on worker timing — which keeps
arms comparable and backtest replays meaningful.

Per round r over stream indices [lo, hi):
  1. re-issue: indices below the cursor with no episode (orphaned by a kill); a dead worker's lease is taken
     over once its TTL has passed;
  2. claim → lease → `ForwardPass.run`, with `workers` concurrency, until the cursor reaches `hi`;
  3. barrier: every index in [lo, hi) has an episode, or the arm stops loudly (a resume re-issues the rest);
  4. V set at each V point p = v_offset + k·v_every in [lo, hi), scored against `world_version(p)` under the
     store as it stands during round r (`stream="v"`, never feeds learning);
  5. `on_round_close(r, (lo, hi))`, then the cursor's round advances to r + 1.
A kill anywhere resumes from the cursor's round: puts are idempotent upserts and the round close is
idempotent per (arm, round).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from collections import deque
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from itertools import islice

from munchhausen.domain.question import Question
from munchhausen.loop.episode import STREAM, ForwardPass, V
from munchhausen.ports.store import Store
from munchhausen.ports.world import World

log = logging.getLogger(__name__)

RoundHook = Callable[[int, tuple[int, int]], Awaitable[None]]   # (round, idx_range) → episodic pass


class RoundIncomplete(RuntimeError):
    """A round's barrier found indices without an episode after every attempt; the arm stops so a resume
    re-issues them, rather than closing a round with a hole in the paired stream."""


def v_points(lo: int, hi: int, v_offset: int, v_every: int) -> list[int]:
    """V points p = v_offset + k·v_every with lo ≤ p < hi."""
    return [p for p in range(max(lo, v_offset), hi) if (p - v_offset) % v_every == 0]


def v_index(point: int, j: int, v_offset: int, v_every: int, v_size: int) -> int:
    """A V episode's idx: the negative ordinal -(1 + k·v_size + j), disjoint from stream indices."""
    return -(1 + ((point - v_offset) // v_every) * v_size + j)


@dataclass
class ArmRunner:
    run_id: str
    forward: ForwardPass
    world: World
    store: Store
    workers: int
    round_size: int
    run_length: int
    v_every: int
    v_offset: int            # V reads at v_offset, v_offset + v_every, …: never on a drift index
    on_round_close: RoundHook
    stream_seed: int
    stream: bool             # ArmSpec.stream: false runs the V set only
    attempts: int            # EPISODE_ATTEMPTS
    poll_interval_s: float
    lease_wait_s: float      # how long a worker waits for a dead worker's lease to expire (≈ LEASE_TTL_S)
    worker_prefix: str = field(default_factory=lambda: f"{os.getpid()}-{uuid.uuid4().hex[:6]}")

    @property
    def arm(self) -> str:
        return self.forward.arm.name

    async def run(self, length: int | None = None) -> dict[str, int]:
        limit = min(length or self.run_length, self.run_length)
        questions = list(islice(self.world.questions(self.stream_seed), limit)) if self.stream else []
        cursor = await self.store.cursors.get(self.run_id, self.arm)
        stats = {"rounds_closed": 0, "episodes": 0, "reissued": 0, "v_episodes": 0, "start_round": cursor.round}
        n_rounds = -(-limit // self.round_size)
        for r in range(cursor.round, n_rounds):
            lo, hi = r * self.round_size, min((r + 1) * self.round_size, limit)
            if self.stream:
                await self._stream_round(lo, hi, questions, stats)
            await self._v_points(lo, hi, stats)
            await self.on_round_close(r, (lo, hi))
            await self.store.cursors.set_round(self.run_id, self.arm, r + 1)
            self.forward.trace.event("round_closed", {"arm": self.arm, "round": r, "idx_range": [lo, hi]})
            stats["rounds_closed"] += 1
        return stats

    # --- the stream ------------------------------------------------------------------------------------

    async def _stream_round(self, lo: int, hi: int, questions: Sequence[Question], stats: dict[str, int]) -> None:
        cursor = await self.store.cursors.get(self.run_id, self.arm)
        orphans = [i for i in range(lo, min(cursor.next_idx, hi))
                   if not await self.store.episodes.exists(self.run_id, self.arm, i)]
        if orphans:
            log.warning("[%s] re-issuing %d orphaned indices: %s", self.arm, len(orphans), orphans)
            stats["reissued"] += len(orphans)
        queue: deque[int] = deque(orphans)

        async def worker(k: int) -> None:
            wid = f"{self.worker_prefix}-{k}"
            while True:
                if queue:
                    idx = queue.popleft()
                else:
                    claimed = await self.store.cursors.claim_next(self.run_id, self.arm, limit=hi)
                    if claimed is None:
                        return
                    idx = claimed
                if await self._episode(idx, questions[idx], wid):
                    stats["episodes"] += 1

        await asyncio.gather(*(worker(k) for k in range(self.workers)))
        missing = [i for i in range(lo, hi) if not await self.store.episodes.exists(self.run_id, self.arm, i)]
        if missing:
            raise RoundIncomplete(f"[{self.arm}] round [{lo}, {hi}) misses episodes {missing}; resume re-issues them")

    async def _episode(self, idx: int, question: Question, worker: str) -> bool:
        if not await self._lease(idx, worker):
            log.error("[%s] idx %d: lease held elsewhere past %.0fs; left for the barrier", self.arm, idx,
                      self.lease_wait_s)
            return False
        try:
            if await self.store.episodes.exists(self.run_id, self.arm, idx):   # finished before a kill
                return False
            for attempt in range(1, self.attempts + 1):
                try:
                    await self.forward.run(idx, question)
                    return True
                except Exception as e:
                    log.exception("[%s] idx %d attempt %d failed: %s", self.arm, idx, attempt, e)
                    self.forward.trace.event("episode_failed", {"arm": self.arm, "idx": idx, "attempt": attempt,
                                                                "error": f"{type(e).__name__}: {e}"})
            return False
        finally:
            await self.store.leases.release(self.run_id, self.arm, idx)

    async def _lease(self, idx: int, worker: str) -> bool:
        deadline = time.monotonic() + self.lease_wait_s
        while True:
            if await self.store.leases.acquire(self.run_id, self.arm, idx, worker):
                return True
            if await self.store.leases.take_over(self.run_id, self.arm, idx, worker):
                return True
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(self.poll_interval_s)

    # --- the V set -------------------------------------------------------------------------------------

    async def _v_points(self, lo: int, hi: int, stats: dict[str, int]) -> None:
        points = v_points(lo, hi, self.v_offset, self.v_every)
        if not points:
            return
        v_set = list(self.world.v_set())
        gate = asyncio.Semaphore(self.workers)

        async def one(point: int, j: int, q: Question) -> None:
            vidx = v_index(point, j, self.v_offset, self.v_every, len(v_set))
            async with gate:
                if await self.store.episodes.exists(self.run_id, self.arm, vidx):
                    return
                for attempt in range(1, self.attempts + 1):
                    try:
                        await self.forward.run(vidx, q, stream=V, at_idx=point)
                        stats["v_episodes"] += 1
                        return
                    except Exception as e:
                        log.exception("[%s] V %d/%d attempt %d failed: %s", self.arm, point, j, attempt, e)

        for point in points:
            await asyncio.gather(*(one(point, j, q) for j, q in enumerate(v_set)))


__all__ = ["STREAM", "V", "ArmRunner", "RoundHook", "RoundIncomplete", "v_index", "v_points"]
