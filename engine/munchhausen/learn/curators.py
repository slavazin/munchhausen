"""Curators (SPEC § 21): what turns a draft into a decision, as an ordered list of layers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from munchhausen.domain.common import LayerRole
from munchhausen.domain.draft import Draft, LayerOutcome, Verdict
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
        out: list[LayerOutcome] = []
        for layer in self.layers:
            outcome = await layer.check(draft, ctx)
            if outcome.verdict is Verdict.ADMIT and layer.role is not LayerRole.DISPOSITIVE and self.governed:
                raise RuntimeError(f"{layer.name}: only a dispositive layer may admit under a governed curator")
            if outcome.verdict is Verdict.ADMIT and self.owner_required:
                outcome = outcome.model_copy(update={"verdict": Verdict.HOLD, "detail": {"awaiting": "owner"}})
            out.append(outcome)
            if outcome.verdict is not Verdict.PASS:
                break
        return out


def governed(l0: Layer, l1: Layer, l2: Layer, l3: Layer, l4: Layer) -> LayeredCurator:
    return LayeredCurator("governed", [l0, l1, l2, l3, l4])


def hitl(l0: Layer, l1: Layer, l2: Layer, l3: Layer, l4: Layer) -> LayeredCurator:
    """L0–L4, then the owner is required (L5): an L4 admit becomes a hold awaiting the owner port."""
    return LayeredCurator("hitl", [l0, l1, l2, l3, l4], owner_required=True)


def naive(l0: Layer) -> LayeredCurator:
    return LayeredCurator("naive", [l0, DirectAdmit()])


def self_ref(l0: Layer) -> LayeredCurator:
    return LayeredCurator("self_ref", [l0, DirectAdmit()])
