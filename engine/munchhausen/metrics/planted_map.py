"""Planted-truth readout (SPEC § 11): evaluation only, outside the loop. A judge (the `Models.planted_map`
party, Opus) given the pack's definitions maps each admitted decision to a quirk id or none. Readings over
the map (quirk recall, N1 admitted, P1 at org scope) live in `metrics/readings.py`.

Population: every record in `decisions` for the run (admitted at some index, whatever its lifecycle since).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any

from munchhausen.domain.decision import Decision
from munchhausen.domain.registers import PlantedMapping

Judge = Callable[[Decision], Awaitable[str | None]]


def pack_definitions(quirks: Iterable[Any]) -> str:
    """The judge's view of the pack: id, kind, prior trap, gold transform and drift, one block per quirk."""
    lines = []
    for q in quirks:
        gold = f"{q.gold.transform} {q.gold.params}" if q.gold is not None else "-"
        drift = "; ".join(f"from {d.at_idx}: {d.gold_params}" for d in q.drift) or "-"
        lines.append(f"- id: {q.id}\n  kind: {q.kind}\n  prior_trap: {q.prior_trap or '-'}\n"
                     f"  definition (gold): {gold}\n  drift: {drift}")
    return "\n".join(lines)


def scope_of(decision: Decision) -> str:
    return "persona" if decision.hook.fires_when.persona is not None else "org"


async def planted_map(decisions: Sequence[Decision], judge: Judge, quirk_ids: Iterable[str], *, model: str,
                      concurrency: int) -> list[PlantedMapping]:
    """Map each decision. A judge answer outside the pack's ids is recorded as none (never coerced)."""
    known = set(quirk_ids)
    sem = asyncio.Semaphore(concurrency)

    async def one(d: Decision) -> PlantedMapping:
        async with sem:
            q = await judge(d)
        return PlantedMapping(_id=f"PM-{d.id}", run_id=d.run_id, arm=d.arm, decision_id=d.id,
                              quirk=q if q in known else None, scope=scope_of(d), model=model,  # type: ignore[arg-type]
                              at=datetime.now(UTC))

    return list(await asyncio.gather(*(one(d) for d in decisions)))
