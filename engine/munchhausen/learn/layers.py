"""Adjudication layers, cheapest first (SPEC § 7.3). Each declares its role; only L4 is dispositive."""

from __future__ import annotations

from dataclasses import dataclass

from munchhausen.domain.common import DecisionKind, LayerRole
from munchhausen.domain.draft import Draft, LayerOutcome, Verdict
from munchhausen.lint_language import lint_entry
from munchhausen.ports.curation import CurationContext, LensPanel
from munchhausen.ports.store import TermRepository


@dataclass
class L0Shape:
    """Structural gate: the entry contract's L0 additions plus the language lint. Refuses only."""

    terms: TermRepository
    name: str = "L0"
    role: LayerRole | None = None

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        figures = [x for o in ctx.sources for x in (o.answer, o.figure) if isinstance(x, (int, float))]
        problems = draft.l0_violations(figures)
        known = {t.term for t in await self.terms.all()} | set(draft.new_terms)
        unknown = sorted(set(draft.hook.fires_when.terms) - known)
        if unknown:
            problems.append(f"hook terms outside the vocabulary: {unknown}")
        source_ids = {o.id for o in ctx.sources}
        dangling = sorted(set(draft.warrant.source_observation_ids) - source_ids)
        if dangling:
            problems.append(f"dangling warrant anchors: {dangling}")
        problems += lint_entry(draft)
        verdict = Verdict.REFUSE if problems else Verdict.PASS
        return LayerOutcome(layer=self.name, role=self.role, verdict=verdict, detail={"problems": problems})


@dataclass
class L1Bar:
    min_templates: int
    min_templates_floor: int
    name: str = "L1"
    role: LayerRole | None = None

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        need = self.min_templates_floor if draft.kind is DecisionKind.FLOOR else self.min_templates
        have = len({o.template for o in ctx.sources})
        verdict = Verdict.PASS if have >= need else Verdict.HOLD
        return LayerOutcome(layer=self.name, role=self.role, verdict=verdict, detail={"templates": have, "need": need})


@dataclass
class L2Neighbours:
    threshold: float
    name: str = "L2"
    role: LayerRole | None = LayerRole.ROUTING

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        raise NotImplementedError("M3: top-5 $vectorSearch → rerank-3 ≥ NEIGHBOUR_RERANK → refine/supersede/duplicate")


@dataclass
class L3Lenses:
    panel: LensPanel
    threshold: float
    explore_eps: float
    name: str = "L3"
    role: LayerRole | None = LayerRole.CORROBORATING

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        raise NotImplementedError("M3: panel.score → LensWeights.score → refuse below threshold unless explore")


@dataclass
class L4Backtest:
    """The dispositive layer. Delegates to `learn.backtest.Backtester`."""

    backtester: object
    name: str = "L4"
    role: LayerRole | None = LayerRole.DISPOSITIVE

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        raise NotImplementedError("M3: Backtester.run(draft) → ADMIT or REFUSE with the backtest id")


@dataclass
class DirectAdmit:
    """naive/self_ref: admit after L0. Declared corroborating — these curators have no dispositive layer."""

    name: str = "admit"
    role: LayerRole | None = LayerRole.CORROBORATING

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        return LayerOutcome(layer=self.name, role=self.role, verdict=Verdict.ADMIT)
