"""Planted-truth readout (SPEC § 11): evaluation only, outside the loop. An Opus judge maps each admitted
decision to a quirk id or none; reports quirk recall, N1 admitted, P1 at org scope, decoy rejection."""

from __future__ import annotations


async def planted_map(run_id: str) -> dict[str, object]:
    raise NotImplementedError("M4")
