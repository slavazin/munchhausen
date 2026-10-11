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
from munchhausen.world.questions import QuestionBank, bank_from_pack


class PackWorld:
    """World = adapter + pack + question bank + authority. Composes the Truth implementation (`pack_gold`),
    exposed as `.truth` for the evaluation side (metrics, V set) — never through the World port.

    Evaluation-side extras (never reached from `learn/ agent/ loop/`): `pack_hash`, `inventory()`,
    `counts()`, `instances()`, `is_quirk_bearing()`, `bank`."""

    @classmethod
    def create(cls, name: str, settings: Any, store: Store, *, truth_db: DocumentReader | None = None) -> Self:
        pack = load_pack(settings.pack_path())
        adapter = registry.resolve("adapter", pack.adapter).create(pack.adapter, settings, store)
        bank = bank_from_pack(pack, settings.quirk_share, sealed=(settings.v_seed, settings.v_size))
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
        self.pack_hash = pack.content_hash()

    async def build(self, seed: int) -> dict[str, int]:
        counts = await self._adapter.build(self._pack, seed)
        self._schema = await self._adapter.schema_summary()
        return counts

    async def load_schema(self) -> SchemaSummary:
        """Read the schema summary of an already-built `world` (a run that did not build it)."""
        self._schema = await self._adapter.schema_summary()
        return self._schema

    def schema_summary(self) -> SchemaSummary:
        if self._schema is None:
            raise RuntimeError("world not built or summary not loaded (await world.load_schema())")
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

    # --- evaluation side (evidence, injection beat, pilot) -----------------------------------------

    @property
    def bank(self) -> QuestionBank:
        return self._bank

    @property
    def pack(self) -> Pack:
        return self._pack

    async def counts(self) -> dict[str, int]:
        """Document counts per `world` collection (the run record's world build counts)."""
        return await self._adapter.counts()

    def instances(self, template_id: str, seed: int, n: int) -> tuple[Question, ...]:
        return self._bank.instances(template_id, seed, n)

    def is_quirk_bearing(self, question_id: str) -> bool:
        return bool(self._bank.hidden(question_id).quirks)

    def inventory(self) -> dict[str, Any]:
        """The pack's inventory for the run record: quirks, templates, phrasings, drift indices. Evaluation
        side only: definitions and gold params are not in it, and the learning path never reads it."""
        quirks = [{"id": q.id, "kind": q.kind, "signature": q.signature, "persona": q.persona,
                   "templates": list(q.templates), "phrasings": list(q.authority_phrasings),
                   "drifts": [d for d, spec in self._pack.drift_schedule.items() if spec.get("quirk") == q.id]}
                  for q in self._pack.quirks]
        templates = [{"id": t.id, "collections": list(t.collections), "quirk": t.quirks[0] if t.quirks else None,
                      "combos": _combos(t.params)} for t in self._bank.templates]
        return {"world": self.id, "pack": self._pack.id, "pack_hash": self.pack_hash,
                "quirks": quirks, "templates": templates, "personas": list(self._pack.personas),
                "drift_at": dict(self._drift_at), "poison_variants": len(self._pack.poison_bank),
                "v_seed": self._v_seed, "v_size": self._v_size}


def _combos(params: dict[str, tuple[Any, ...]]) -> int:
    n = 1
    for v in params.values():
        n *= len(v)
    return n
