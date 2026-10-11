"""Composition root, evidence half (ORCHESTRATION.md § Evidence): the run record at start and the round
record at each round close. Composition-level, so it may read git, the store's capabilities and the
config. Owner: telemetry surface (S5). Called by `bootstrap`/the `run` command (S2)."""

from __future__ import annotations

from typing import Any

from munchhausen.domain.registers import RunRecord


async def start_run(h: Any) -> RunRecord:
    """Write `runs` before the first episode: git sha + dirty, knobs, ports per arm, capabilities,
    isolation mode, model ids, party prompt hashes, pack hash, world counts, forecasts. Idempotent on
    resume (returns the stored record; forecasts are never edited after the first episode)."""
    raise NotImplementedError("M4: run record (S5)")


async def close_round(h: Any, arm: str, round_: int, idx_range: tuple[int, int]) -> None:
    """`$merge` the round's record over `episodes` (and lifecycle/fire/spend counts) into `rounds`."""
    raise NotImplementedError("M4: round record via $merge (S5)")
