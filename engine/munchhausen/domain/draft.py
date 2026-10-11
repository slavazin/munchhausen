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


class DirectionRead(Value):
    """E4, part of the bar: the miss rate over every episode the shape's presentation matches, hits
    included, against the miss rate outside it. A shape formed from misses agrees with itself by
    construction; only a gap over the whole matched population says the shape marks where answers fail."""

    misses_in: int
    n_in: int
    misses_out: int
    n_out: int

    @property
    def gap(self) -> float:
        rate_in = self.misses_in / self.n_in if self.n_in else 0.0
        rate_out = self.misses_out / self.n_out if self.n_out else 0.0
        return rate_in - rate_out


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
    # Every episode id the nominator was shown: the shape's own episodes plus the episodes behind the
    # neighbours' residuals. The backtest population excludes them, so the held-out read stays held out.
    nominator_seen_episode_ids: tuple[str, ...] = ()
    # Where the draft's evidence came from: "stream" (the episodic pass) or "injection" (the operator's
    # false-figure beat, `loop/inject.py`). Round records and the owner port read it (additive, S6).
    source: str = "stream"
