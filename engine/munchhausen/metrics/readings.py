"""Per-arm, per-round readings computed in Atlas (`$setWindowFields`, `$merge` into `rounds`)."""

from __future__ import annotations


async def close_round(run_id: str, arm: str, round_: int) -> None:
    raise NotImplementedError("M3: $merge pipeline over episodes → rounds (acc, self-assessed, calibration gap)")
