"""Arm runner (S2, SPEC § 10.4): cursor claim → TTL lease → forward pass → round barrier → round close,
the V set at its points, and resume after a kill. Offline: the fakes of `test_forward`."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from munchhausen.loop.runner import ArmRunner, RoundIncomplete, v_index, v_points
from tests.test_forward import FakeStore, FakeWorld, arm, forward

RUN_LENGTH, ROUND, V_EVERY, V_OFFSET = 12, 4, 6, 3


class Blocking:
    """A forward pass that stops completing after `budget` episodes: the in-flight ones hang, as a killed
    process leaves them."""

    def __init__(self, inner: Any, budget: int) -> None:
        self.inner, self.budget, self.blocked = inner, budget, 0
        self.arm, self.trace = inner.arm, inner.trace

    async def run(self, idx: int, question: Any, **kw: Any) -> Any:
        if self.budget <= 0:
            self.blocked += 1
            await asyncio.Event().wait()
        self.budget -= 1
        return await self.inner.run(idx, question, **kw)


def runner(store: FakeStore, world: FakeWorld, fp: Any, closes: list[tuple[int, tuple[int, int]]],
           **over: Any) -> ArmRunner:
    async def close(r: int, rng: tuple[int, int]) -> None:
        closes.append((r, rng))

    kw: dict[str, Any] = dict(run_id="r", forward=fp, world=world, store=store, workers=3, round_size=ROUND,
                              run_length=RUN_LENGTH, v_every=V_EVERY, v_offset=V_OFFSET, on_round_close=close,
                              stream_seed=11, stream=True, attempts=2, poll_interval_s=0.001, lease_wait_s=0.05)
    kw.update(over)
    return ArmRunner(**kw)


def stream_idx(store: FakeStore) -> list[int]:
    return sorted(e.idx for e in store.episodes.docs.values() if e.stream == "stream")


def test_v_points_and_indices() -> None:
    assert v_points(0, 900, 75, 150) == [75, 225, 375, 525, 675, 825]
    assert v_points(60, 90, 75, 150) == [75] and v_points(90, 120, 75, 150) == []
    assert v_index(75, 0, 75, 150, 40) == -1 and v_index(225, 39, 75, 150, 40) == -80


def test_rounds_close_in_order_after_their_barrier_with_v_at_its_points() -> None:
    store, world, closes = FakeStore(), FakeWorld(), []
    fp, _ = forward(store, arm("frozen", authority=False))
    stats = asyncio.run(runner(store, world, fp, closes).run())
    assert stream_idx(store) == list(range(RUN_LENGTH))
    assert closes == [(0, (0, 4)), (1, (4, 8)), (2, (8, 12))]
    v = sorted((e.idx, e.id.rsplit(":", 1)[1]) for e in store.episodes.docs.values() if e.stream == "v")
    assert [i for i, _ in v] == [-6, -5, -4, -3, -2, -1] and {p for _, p in v} == {"3", "9"}
    assert stats["rounds_closed"] == 3 and stats["v_episodes"] == 6
    assert asyncio.run(store.cursors.get("r", "frozen")).round == 3
    assert not store.leases.rows


def test_a_v_only_arm_runs_the_v_set_and_closes_rounds() -> None:
    store, world, closes = FakeStore(), FakeWorld(), []
    fp, _ = forward(store, arm("frozen", authority=False))
    asyncio.run(runner(store, world, fp, closes, stream=False).run())
    assert stream_idx(store) == [] and len(closes) == 3
    assert sum(e.stream == "v" for e in store.episodes.docs.values()) == 6


def test_resume_after_a_kill_reissues_orphans_and_reruns_the_open_round() -> None:
    store, world, closes = FakeStore(), FakeWorld(), []
    fp, _ = forward(store, arm())
    blocking = Blocking(fp, budget=9)          # round 0: 4 stream + 3 V; round 1: idx 4, 5 complete

    async def killed() -> None:
        task = asyncio.create_task(runner(store, world, blocking, closes).run())
        while blocking.blocked < 2:
            await asyncio.sleep(0)
        leases = dict(store.leases.rows)        # a kill releases nothing
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        store.leases.rows = leases
        assert leases, "in-flight indices hold leases at the kill"

    asyncio.run(killed())
    before = stream_idx(store)
    assert before == list(range(6)) and closes == [(0, (0, 4))]
    cursor = asyncio.run(store.cursors.get("r", "hooks"))
    assert cursor.round == 1 and cursor.next_idx == 8

    # the dead process's leases have not expired: the resumed worker waits for the TTL, then takes over
    for k, (w, _) in store.leases.rows.items():
        store.leases.rows[k] = (w, datetime.now(UTC) + timedelta(milliseconds=20))
    stats = asyncio.run(runner(store, world, fp, closes).run())
    assert stats["start_round"] == 1 and stats["reissued"] == 2
    assert stream_idx(store) == list(range(RUN_LENGTH))
    assert closes == [(0, (0, 4)), (1, (4, 8)), (2, (8, 12))]
    assert not store.leases.rows
    assert asyncio.run(store.cursors.get("r", "hooks")).round == 3

    # resuming a finished run is a no-op
    puts = store.episodes.puts
    asyncio.run(runner(store, world, fp, closes).run())
    assert store.episodes.puts == puts and len(closes) == 3


def test_a_round_with_a_persistent_failure_stops_the_arm_without_closing() -> None:
    store, world, closes = FakeStore(), FakeWorld(), []
    fp, _ = forward(store, arm())

    class Broken:
        arm, trace = fp.arm, fp.trace

        async def run(self, idx: int, question: Any, **kw: Any) -> Any:
            if idx == 2:
                raise RuntimeError("world unavailable")
            return await fp.run(idx, question, **kw)

    with pytest.raises(RoundIncomplete):
        asyncio.run(runner(store, world, Broken(), closes).run())
    assert closes == [] and asyncio.run(store.cursors.get("r", "hooks")).round == 0
    asyncio.run(runner(store, world, fp, closes).run())       # resume re-issues idx 2
    assert stream_idx(store) == list(range(RUN_LENGTH)) and len(closes) == 3
