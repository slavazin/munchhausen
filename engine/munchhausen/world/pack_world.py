"""`PackWorld`: the World port composed from an adapter, a pack, a question bank and the authority."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any, Self

from munchhausen.domain.common import Answer
from munchhausen.domain.episode import Judgement
from munchhausen.domain.question import Question, SchemaSummary
from munchhausen.ports import registry
from munchhausen.ports.store import DocumentReader, Store
from munchhausen.truth.gold import PackGold
from munchhausen.world.authority import Authority
from munchhausen.world.pack import Pack, load_pack
from munchhausen.world.questions import QuestionBank


class PackWorld:
    """World = adapter + pack + question bank + authority. Composes the Truth implementation (`pack_gold`),
    exposed as `.truth` for the evaluation side (metrics, V set) — never through the World port."""

    @classmethod
    def create(cls, name: str, settings: Any, store: Store, *, truth_db: DocumentReader) -> Self:
        pack = load_pack(settings.pack_path())
        adapter = registry.resolve("adapter", pack.adapter).create(pack.adapter, settings, store)
        bank = QuestionBank(templates=(), personas=(), quirk_share=settings.quirk_share)   # M1: templates
        truth = PackGold(pack, bank, store.world(), truth_db, settings.execute_max_time_ms)
        authority = Authority(truth, pack, bank, settings.authority_level, settings.authority_poison_rate,
                              settings.score_rel_tol, settings.score_abs_tol_rounded, settings.world_seed)
        drift_at = {d: getattr(settings, spec["at_knob"].lower()) for d, spec in pack.drift_schedule.items()}
        world = cls(adapter, pack, bank, authority, drift_at, settings.v_seed, settings.v_size)
        world.truth = truth
        return world

    def __init__(self, adapter: Any, pack: Pack, bank: QuestionBank, authority: Authority,
                 drift_at: dict[str, int], v_seed: int, v_size: int) -> None:
        self.id = f"{adapter.name}+{pack.id}"
        self._adapter, self._pack, self._bank, self._authority = adapter, pack, bank, authority
        self._drift_at = drift_at            # drift id → stream index, resolved from knobs
        self._v_seed, self._v_size = v_seed, v_size
        self._schema: SchemaSummary | None = None

    async def build(self, seed: int) -> dict[str, int]:
        counts = await self._adapter.build(self._pack, seed)
        self._schema = await self._adapter.schema_summary()
        return counts

    def schema_summary(self) -> SchemaSummary:
        if self._schema is None:
            raise RuntimeError("world not built or summary not loaded")
        return self._schema

    def questions(self, seed: int) -> Iterator[Question]:
        return self._bank.stream(seed)

    def v_set(self) -> Sequence[Question]:
        return self._bank.v_set(self._v_seed, self._v_size)

    def world_version(self, idx: int) -> str:
        """`v0`, then one suffix per drift whose index has passed: e.g. `v0+D1`, `v0+D1+D2`."""
        passed = [d for d, at in sorted(self._drift_at.items(), key=lambda kv: kv[1]) if idx >= at]
        return "+".join(["v0", *passed])

    async def judge(self, question: Question, answer: Answer, idx: int, *, with_authority: bool) -> Judgement:
        return await self._authority.judge(question, answer, self.world_version(idx), idx,
                                           with_authority=with_authority)
