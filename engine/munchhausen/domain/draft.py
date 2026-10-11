"""Drafts, shapes and adjudication outcomes (SPEC § 7.2–7.3)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from munchhausen.domain.common import LayerRole, Record, Value
from munchhausen.domain.decision import EntryContract


class Shape(Value):
    """A group of observations located by a grouper and passing the coherence guard. Proposes no rule."""

    id: str
    observation_ids: tuple[str, ...]
    episode_ids: tuple[str, ...]
    templates: frozenset[str]
    personas: frozenset[str]
    terms: frozenset[str]
    source: str = "internal"   # internal | external (SignalSource)


class Route(StrEnum):
    """L2 routing of a draft against its nearest admitted neighbour."""

    NEW = "new"
    REFINE = "refine"
    SUPERSEDE = "supersede"
    DUPLICATE = "duplicate"


class Verdict(StrEnum):
    PASS = "pass"      # continue to the next layer
    HOLD = "hold"      # wait for more observations (L1)
    REFUSE = "refuse"
    ADMIT = "admit"    # only a dispositive layer, or the owner, may return this


class LayerOutcome(Value):
    layer: str                  # L0 … L5
    role: LayerRole | None      # None for the structural gates L0/L1
    verdict: Verdict
    route: Route | None = None
    neighbour_id: str | None = None
    score: float | None = None
    explore: bool = False
    detail: dict[str, Any] = Field(default_factory=dict)


class DraftStatus(StrEnum):
    PENDING = "pending"
    HELD = "held"
    REFUSED = "refused"
    ADMITTED = "admitted"


class Draft(EntryContract, Record):
    shape_id: str
    source_observation_ids: tuple[str, ...]
    new_terms: tuple[str, ...] = ()          # the vocabulary escape: other(<term>): <gloss> (§ 22.4)
    adjudication: dict[str, LayerOutcome] = Field(default_factory=dict)   # keyed L0 … L5
    explore: bool = False
    route: Route = Route.NEW
    supersedes: str | None = None
    status: DraftStatus = DraftStatus.PENDING
    round: int
