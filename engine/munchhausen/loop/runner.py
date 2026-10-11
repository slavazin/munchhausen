"""Arm runner (SPEC § 10.4): workers claim indices from `cursors`, hold TTL leases, and close rounds.

Round barrier: all episodes of round r are written before round r's episodic pass, and round r+1 starts
after it. Consultation at index i then depends only on (seed, i), not on worker timing — which keeps
arms comparable and backtest replays meaningful.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from munchhausen.loop.episode import ForwardPass
from munchhausen.ports.store import Store
from munchhausen.ports.world import World

RoundHook = Callable[[int, tuple[int, int]], Awaitable[None]]   # (round, idx_range) → episodic pass


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

    async def run(self) -> None:
        raise NotImplementedError(
            "M2: resume from cursor; re-issue orphaned indices; per round: claim → lease → ForwardPass.run "
            "with `workers` concurrency → await round barrier → on_round_close; V set at v_offset + k·v_every")
