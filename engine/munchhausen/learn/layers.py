"""Adjudication layers, cheapest first (SPEC § 7.3). Each declares its role; only L4 is dispositive."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from munchhausen.domain.common import DecisionKind, LayerRole
from munchhausen.domain.draft import Draft, LayerOutcome, Verdict
from munchhausen.domain.lesson import lesson_violations
from munchhausen.lint_language import lint_entry
from munchhausen.ports.curation import CurationContext, LensPanel
from munchhausen.ports.store import LensRepository, TermRepository


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
    """The corroborating panel. In `record` mode (LENS_MODE, the default) it scores and passes every draft,
    so every draft reaches the backtest and labels the lens fit; the seed weights are unwarranted (§ 23.2)
    and a gate on them would hide its own errors. `gate` mode refuses below LENS_THRESHOLD except an
    explore share LENS_EXPLORE_EPS, drawn deterministically per draft."""

    panel: LensPanel
    weights: LensRepository
    mode: Literal["record", "gate"]
    threshold: float
    explore_eps: float
    seed: int
    name: str = "L3"
    role: LayerRole | None = LayerRole.CORROBORATING

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        p = await self.panel.score(draft, ctx.sources, [d for d, _ in ctx.neighbours])
        score = (await self.weights.current_weights()).score(p)
        below = score < self.threshold
        explore = below and self.mode == "gate" and _unit(f"{self.seed}:{draft.id}") < self.explore_eps
        refuse = below and self.mode == "gate" and not explore
        return LayerOutcome(layer=self.name, role=self.role, verdict=Verdict.REFUSE if refuse else Verdict.PASS,
                            score=score, explore=explore, detail={"lens": p, "mode": self.mode, "below": below})


def _unit(key: str) -> float:
    return int(hashlib.sha256(key.encode()).hexdigest()[:12], 16) / 16**12


@dataclass
class L4Backtest:
    """The dispositive layer. Delegates to `learn.backtest.Backtester`."""

    backtester: object
    name: str = "L4"
    role: LayerRole | None = LayerRole.DISPOSITIVE

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        raise NotImplementedError("M3: Backtester.run(draft) → ADMIT or REFUSE with the backtest id")


@dataclass
class LessonShape:
    """L0 for lessons (naive, self_ref): the checks a lesson can carry, plus the language lint. A lesson
    has no rejected option, revisit latch or vocabulary hook, so the entry-contract L0 would refuse every
    one; that refusal would measure the contract, not the arm."""

    name: str = "L0"
    role: LayerRole | None = None

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        figures = [x for o in ctx.sources for x in (o.answer, o.figure) if isinstance(x, (int, float))]
        problems = lesson_violations(draft, figures) + lint_entry(draft)
        verdict = Verdict.REFUSE if problems else Verdict.PASS
        return LayerOutcome(layer=self.name, role=self.role, verdict=verdict, detail={"problems": problems})


@dataclass
class DirectAdmit:
    """naive/self_ref/ungated: admit after L0. Declared corroborating — these curators have no dispositive
    layer, so every readout reports them as ungoverned."""

    name: str = "admit"
    role: LayerRole | None = LayerRole.CORROBORATING

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        return LayerOutcome(layer=self.name, role=self.role, verdict=Verdict.ADMIT)
