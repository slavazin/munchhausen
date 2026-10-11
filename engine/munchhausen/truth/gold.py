"""`PackGold`: gold answers from the pack's gold transforms, per world version (SPEC § 4.3).

Gold for a question = the template's measure over the materialized `world` documents, with the slots of
the question's one hidden quirk overridden by that quirk's gold transform at `world_version` (`v0`,
`v0+D1`, `v0+D1+D2`: each drift merges its `gold_params` over the quirk's). Drift is gold-only; `world`
is never mutated after build. Never imported under `learn/`, `agent/` or `loop/`.

`truth` (the evaluator-role handle on the `truth` database) is held for the definitions register; gold is
computed from the pack, so the handle is not read on the scoring path.
"""

from __future__ import annotations

import asyncio
from typing import Any

from munchhausen.domain.common import Answer
from munchhausen.domain.question import Question
from munchhausen.ports.store import DocumentReader
from munchhausen.world.pack import Pack
from munchhausen.world.questions import QuestionBank
from munchhausen.world.transforms import GOLD, MEASURE, Data, Slots, compose

WORLD_COLLECTIONS = ("customers", "accounts", "transactions")


def version_drifts(world_version: str) -> tuple[str, ...]:
    """`v0+D1+D2` → ("D1", "D2")."""
    return tuple(world_version.split("+")[1:])


class PackGold:
    def __init__(self, pack: Pack, bank: QuestionBank, world: DocumentReader, truth: DocumentReader | None,
                 max_time_ms: int) -> None:
        self._pack, self._bank, self._world, self._truth = pack, bank, world, truth
        self._max_time_ms = max_time_ms
        self._data: Data | None = None
        self._lock = asyncio.Lock()

    async def gold(self, question: Question, world_version: str) -> Answer:
        return self.compute(question, world_version, await self.data())

    async def variant(self, question: Question, world_version: str, quirk_id: str,
                      params: dict[str, Any]) -> Answer:
        """Gold with one quirk's gold params overridden (N1's poison bank)."""
        return self.compute(question, world_version, await self.data(), variant=(quirk_id, params))

    async def data(self) -> Data:
        async with self._lock:
            if self._data is None:
                self._data = {c: await self._world.find(c) for c in WORLD_COLLECTIONS}
        return self._data

    # --- pure part (tests drive this over fixtures) -------------------------------------------------

    def quirk_params(self, quirk_id: str, world_version: str) -> dict[str, Any]:
        """The quirk's gold params at a world version: base params, then each passed drift's gold_params."""
        q = self._pack.quirk(quirk_id)
        if q.gold is None:
            return {}
        params = dict(q.gold.params)
        for d in version_drifts(world_version):
            spec = self._pack.drift_schedule.get(d, {})
            if spec.get("quirk") != quirk_id:
                continue
            for drift in q.drift:
                if drift.at_idx == spec.get("at_knob"):
                    params.update(drift.gold_params)
        return params

    def slots_for(self, quirk_ids: tuple[str, ...], world_version: str,
                  variant: tuple[str, dict[str, Any]] | None = None, *, convention: bool = False) -> Slots:
        overrides = []
        for qid in quirk_ids:
            q = self._pack.quirk(qid)
            if convention:                      # the prior trap's figure (checks only): base slots if none
                if q.convention is not None:
                    overrides.append(GOLD[q.convention.transform](dict(q.convention.params)))
                continue
            if q.gold is None:
                continue
            params = self.quirk_params(qid, world_version)
            if variant is not None and variant[0] == qid:
                params = {**params, **variant[1]}
            overrides.append(GOLD[q.gold.transform](params))
        return compose(*overrides)

    def compute(self, question: Question, world_version: str, data: Data, *,
                variant: tuple[str, dict[str, Any]] | None = None,
                extra_quirks: tuple[str, ...] = (), convention: bool = False) -> Answer:
        """`extra_quirks` applies further quirks' gold transforms (the gold isolation test only);
        `convention` computes the prior trap's figure instead of gold (the poison check only)."""
        hidden = self._bank.hidden(question.id)
        tpl = self._bank.template(question.template)
        slots = self.slots_for((*hidden.quirks, *extra_quirks), world_version, variant, convention=convention)
        value = MEASURE[tpl.measure](data, slots, hidden.params, tpl.args)
        return slots["present"](value)
