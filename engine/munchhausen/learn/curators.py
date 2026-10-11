"""Curators (SPEC § 21): what turns a draft into a decision, as an ordered list of layers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from munchhausen.domain.common import LayerRole
from munchhausen.domain.draft import Draft, LayerOutcome, Route, Verdict
from munchhausen.learn.layers import DirectAdmit
from munchhausen.ports.curation import CurationContext, Layer


@dataclass
class LayeredCurator:
    name: str
    layers: Sequence[Layer]
    owner_required: bool = False   # hitl: a dispositive admit waits for the owner port (L5)

    @property
    def governed(self) -> bool:
        return any(layer.role is LayerRole.DISPOSITIVE for layer in self.layers)

    async def curate(self, draft: Draft, ctx: CurationContext) -> list[LayerOutcome]:
        """A routing layer's route is applied to the draft the later layers see (`routed`), so the
        backtest reads a supersede's population and context, not the nominator's original route."""
        out: list[LayerOutcome] = []
        for layer in self.layers:
            outcome = await layer.check(draft, ctx)
            if outcome.verdict is Verdict.ADMIT and layer.role is not LayerRole.DISPOSITIVE and self.governed:
                raise RuntimeError(f"{layer.name}: only a dispositive layer may admit under a governed curator")
            if outcome.verdict is Verdict.ADMIT and self.owner_required:
                outcome = outcome.model_copy(update={"verdict": Verdict.HOLD,
                                                     "detail": {**outcome.detail, "awaiting": "owner"}})
            out.append(outcome)
            draft = routed(draft, [outcome])
            if outcome.verdict is not Verdict.PASS:
                break
        return out


def routed(draft: Draft, outcomes: Sequence[LayerOutcome]) -> Draft:
    """The draft with the last routing layer's route applied (`supersedes` set for a supersede)."""
    for o in reversed(outcomes):
        if o.role is LayerRole.ROUTING and o.route is not None:
            supersedes = o.neighbour_id if o.route is Route.SUPERSEDE else None
            if (draft.route, draft.supersedes) == (o.route, supersedes):
                return draft
            return draft.model_copy(update={"route": o.route, "supersedes": supersedes})
    return draft


def governed(l0: Layer, l1: Layer, l2: Layer, l3: Layer, l4: Layer) -> LayeredCurator:
    return LayeredCurator("governed", [l0, l1, l2, l3, l4])


def hitl(l0: Layer, l1: Layer, l2: Layer, l3: Layer, l4: Layer) -> LayeredCurator:
    """L0–L4, then the owner is required (L5): an L4 admit becomes a hold awaiting the owner port."""
    return LayeredCurator("hitl", [l0, l1, l2, l3, l4], owner_required=True)


def ungated(l0: Layer) -> LayeredCurator:
    """The ablation that isolates the gate: governed's nominator, bar and hooks, admitted at L0.
    `governed` minus `ungated` reads what L2–L4 add; every other difference between them is zero."""
    return LayeredCurator("ungated", [l0, DirectAdmit()])


def naive(l0: Layer) -> LayeredCurator:
    """Lessons admitted directly. Pass `LessonShape()` as L0 (a lesson carries no entry-contract slots)."""
    return LayeredCurator("naive", [l0, DirectAdmit()])


def self_ref(l0: Layer) -> LayeredCurator:
    """Self-graded lessons admitted directly. Pass `LessonShape()` as L0."""
    return LayeredCurator("self_ref", [l0, DirectAdmit()])
