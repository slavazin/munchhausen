"""Adjudication layers, cheapest first (SPEC § 7.3). Each declares its role; only L4 is dispositive."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from munchhausen import lint_language
from munchhausen.domain import pipeline_guard
from munchhausen.domain.backtest import BacktestVerdict
from munchhausen.domain.common import DecisionKind, FireDisposition, FireRole, LayerRole
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Draft, LayerOutcome, Route, Verdict
from munchhausen.domain.lesson import lesson_violations
from munchhausen.learn.backtest import Backtester
from munchhausen.lint_language import lint_entry
from munchhausen.ports.curation import CurationContext, LensPanel
from munchhausen.ports.store import (
    DecisionRepository,
    DocumentReader,
    FireRepository,
    LensRepository,
    TermRepository,
)


@dataclass
class L0Shape:
    """Structural gate: the entry contract's L0 additions plus the language lint. Refuses only.

    A floor's spec must compile to a `$match` stage the world sandbox accepts (`pipeline_guard.check`), on a
    collection that exists in `world` (`world` given: its collection names)."""

    terms: TermRepository
    world: DocumentReader | None = None
    name: str = "L0"
    role: LayerRole | None = None

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        figures = [x for o in ctx.sources for x in (o.answer, o.figure) if isinstance(x, (int, float))]
        problems = draft.l0_violations(figures)
        known = {t.term.lower() for t in await self.terms.all()} | escaped_terms(draft.new_terms)
        unknown = sorted({t.lower() for t in draft.hook.fires_when.terms} - known)
        if unknown:
            problems.append(f"hook terms outside the vocabulary: {unknown}")
        source_ids = {o.id for o in ctx.sources}
        dangling = sorted(set(draft.warrant.source_observation_ids) - source_ids)
        if dangling:
            problems.append(f"dangling warrant anchors: {dangling}")
        problems += lint_entry(draft)
        problems += await self._floor(draft)
        verdict = Verdict.REFUSE if problems else Verdict.PASS
        return LayerOutcome(layer=self.name, role=self.role, verdict=verdict, detail={"problems": problems})

    async def _floor(self, draft: Draft) -> list[str]:
        floor = draft.floor
        if floor is None:
            return []
        out = []
        names = await self.world.collection_names() if self.world is not None else None
        if names is not None and floor.collection not in names:
            out.append(f"floor collection {floor.collection!r} is not a world collection")
        if FLOOR_VIEW.search(floor.collection):
            out.append(f"floor collection {floor.collection!r} is itself a floor view")
        try:
            pipeline_guard.check([{"$match": floor.match}], targets=names or ())
        except pipeline_guard.PipelineRefused as e:
            out.append(f"floor match refused by the sandbox: {e}")
        return out


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
    """Routing (minimum configuration, CARRY_FORWARD § 3a): every draft routes `new`, except a supersede the
    nominator declared against a **contested** neighbour (an open dispositive fire). A declared supersede
    against a clear or non-admitted neighbour is refused: nothing in the store says the predecessor's
    grounds moved, and the backtest's population (after the fire) would not exist. A declared duplicate is
    refused; a declared refine routes `new` (refine routing is the full L2, not built).

    `route_contested` (knob L2_ROUTE_CONTESTED, off by default) adds one routing the nominator did not
    declare: a `new` draft sharing a hook term with exactly one contested neighbour of its kind routes as a
    supersede of it. The backtest still decides; this only lets a successor be tried against its predecessor.
    Full rerank routing (refine/duplicate at NEIGHBOUR_RERANK) is not built."""

    threshold: float
    decisions: DecisionRepository | None = None
    fires: FireRepository | None = None
    route_contested: bool = False
    name: str = "L2"
    role: LayerRole | None = LayerRole.ROUTING

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        out = await self._route(draft, ctx)
        floor = draft.floor
        if out.verdict is Verdict.PASS and floor is not None and self.decisions is not None:
            replaced = out.neighbour_id if out.route is Route.SUPERSEDE else None
            clash = [d.id for d in await self.decisions.admitted(draft.run_id, draft.arm)
                     if d.floor is not None and d.floor.collection == floor.collection and d.id != replaced]
            if clash:
                return self._out(Verdict.REFUSE, out.route or Route.NEW, clash[0],
                                 reason=f"a floor on {floor.collection} is admitted ({clash[0]}); only a supersede "
                                        "of it may replace it")
        return out

    async def _route(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        if draft.route is Route.DUPLICATE:
            return self._out(Verdict.REFUSE, Route.DUPLICATE, draft.supersedes, reason="declared duplicate")
        if draft.route is Route.SUPERSEDE:
            target = draft.supersedes
            pred = await self._get(target, ctx) if target else None
            if pred is None or not pred.is_admitted:
                return self._out(Verdict.REFUSE, Route.SUPERSEDE, target,
                                 reason="supersede target is not an admitted decision")
            if not await self._contested(pred.id):
                return self._out(Verdict.REFUSE, Route.SUPERSEDE, target,
                                 reason="supersede against a clear neighbour (no open dispositive fire)")
            return self._out(Verdict.PASS, Route.SUPERSEDE, target, reason="declared supersede, contested")
        if self.route_contested:
            terms = set(draft.hook.fires_when.terms)
            hits = [d for d, _ in ctx.neighbours if d.is_admitted and d.kind is draft.kind
                    and terms & set(d.hook.fires_when.terms) and await self._contested(d.id)]
            if len(hits) == 1:
                return self._out(Verdict.PASS, Route.SUPERSEDE, hits[0].id,
                                 reason="one contested neighbour shares a hook term")
        reason = "declared refine routes new (full L2 not built)" if draft.route is Route.REFINE else "new"
        return self._out(Verdict.PASS, Route.NEW, None, reason=reason)

    def _out(self, verdict: Verdict, route: Route, neighbour: str | None, *, reason: str) -> LayerOutcome:
        return LayerOutcome(layer=self.name, role=self.role, verdict=verdict, route=route, neighbour_id=neighbour,
                            detail={"reason": reason})

    async def _get(self, decision_id: str, ctx: CurationContext) -> Decision | None:
        for d, _ in ctx.neighbours:
            if d.id == decision_id:
                return d
        return await self.decisions.get(decision_id) if self.decisions is not None else None

    async def _contested(self, decision_id: str) -> bool:
        if self.fires is None:
            return False
        return any(f.role is FireRole.DISPOSITIVE and f.disposition is FireDisposition.OPEN
                   for f in await self.fires.open_for(decision_id))


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


_ESCAPE = re.compile(r"^\s*other\(\s*(?P<term>[^()]+?)\s*\)\s*:\s*(?P<gloss>\S.*)$")


def escaped_terms(items: Iterable[str]) -> set[str]:
    """Terms a draft brings through the escape `other(<term>): <gloss>` (LANGUAGE.md § 4). Delegates to
    `lint_language.escaped_terms` (the shaping surface's one definition) where it exists."""
    shared = getattr(lint_language, "escaped_terms", None)
    if shared is not None:
        return set(shared(items))
    return {m.group("term").strip().lower() for m in map(_ESCAPE.match, items) if m}


FLOOR_VIEW = re.compile(r"__D-[0-9a-f]+$")


def _unit(key: str) -> float:
    return int(hashlib.sha256(key.encode()).hexdigest()[:12], 16) / 16**12


@dataclass
class L4Backtest:
    """The dispositive layer. Delegates to `learn.backtest.Backtester` (paired replay, § 7.4). Admits on
    `fixed ≥ min ∧ fixed − broken ≥ min ∧ fixed_heldout ≥ min ∧ broken ≤ max`; refuses otherwise, always with
    the backtest id. A read with fewer than BACKTEST_MIN_N scored pairs HOLDs (`reason: insufficient`): a
    backtest that could not score never refuses. The outcome's `label` (1 admitted, 0 refused, None held) is
    the lens fit's label (§ 9); the fit itself is cut."""

    backtester: Backtester
    name: str = "L4"
    role: LayerRole | None = LayerRole.DISPOSITIVE

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome:
        run = await self.backtester.run(draft, ctx)
        if run.insufficient:
            return LayerOutcome(layer=self.name, role=self.role, verdict=Verdict.HOLD,
                                detail={**run.detail(), "reason": "insufficient", "label": None})
        admit = run.backtest.verdict is BacktestVerdict.ADMIT
        return LayerOutcome(layer=self.name, role=self.role, verdict=Verdict.ADMIT if admit else Verdict.REFUSE,
                            detail={**run.detail(), "label": int(admit)})


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
