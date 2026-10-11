"""Planted-truth readout (SPEC § 11): evaluation only, outside the loop. A judge (the planted-map party) given
the pack's definitions maps each admitted decision — and each backtested draft, for the § 12 premise join — to
a quirk id or none. Readings over the map live in `metrics/readings.py`.

Failures are per subject: the primary model is tried, then the fallback model; a subject both fail on gets no
row and is counted in the result (`failed`), never coerced to none. Rows are persisted as they arrive, so an
interrupted map keeps what it read.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from munchhausen.domain.registers import PlantedMapping

Judge = Callable[[Any, str], Awaitable[str | None]]       # (subject, model) → quirk id or None
Sink = Callable[[PlantedMapping], Awaitable[None]]


def pack_definitions(quirks: Iterable[Any]) -> str:
    """The judge's view of the pack: id, kind, prior trap, gold transform and drift, one block per quirk."""
    lines = []
    for q in quirks:
        gold = f"{q.gold.transform} {q.gold.params}" if q.gold is not None else "-"
        drift = "; ".join(f"from {d.at_idx}: {d.gold_params}" for d in q.drift) or "-"
        lines.append(f"- id: {q.id}\n  kind: {q.kind}\n  prior_trap: {q.prior_trap or '-'}\n"
                     f"  definition (gold): {gold}\n  drift: {drift}")
    return "\n".join(lines)


def scope_of(subject: Any) -> str:
    return "persona" if subject.hook.fires_when.persona is not None else "org"


@dataclass
class MapResult:
    mapped: list[PlantedMapping] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)      # subject id → last error class
    by_model: dict[str, int] = field(default_factory=dict)


async def planted_map(subjects: Sequence[tuple[str, Any]], judge: Judge, quirk_ids: Iterable[str], *,
                      models: Sequence[str], concurrency: int, sink: Sink) -> MapResult:
    """`subjects` = [(kind, record)], kind `decision` or `draft`. A judge answer outside the pack's ids is
    recorded as none. Each row is handed to `sink` as soon as it is read."""
    known = set(quirk_ids)
    sem = asyncio.Semaphore(concurrency)
    res = MapResult()

    async def one(kind: str, subj: Any) -> None:
        last = ""
        for model in models:
            try:
                async with sem:
                    q = await judge(subj, model)
            except Exception as e:  # noqa: BLE001 - one subject's failure never stops the map
                last = type(e).__name__
                continue
            row = PlantedMapping(_id=f"PM-{subj.id}", run_id=subj.run_id, arm=subj.arm, decision_id=subj.id,
                                 quirk=q if q in known else None, scope=scope_of(subj),  # type: ignore[arg-type]
                                 model=model, at=datetime.now(UTC), subject=kind)
            await sink(row)
            res.mapped.append(row)
            res.by_model[model] = res.by_model.get(model, 0) + 1
            return
        res.failed[subj.id] = last

    await asyncio.gather(*(one(k, s) for k, s in subjects))
    return res
