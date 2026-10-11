"""Curator, Layer and LensPanel ports (SPEC § 7.3, § 21).

A curator is an ordered list of layers, each declaring its role. A curator with no dispositive layer is
reported as ungoverned — that is how `naive` and `self_ref` differ from `governed` in every readout.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from munchhausen.domain.common import LayerRole
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Draft, LayerOutcome
from munchhausen.domain.observation import Observation


@dataclass(frozen=True)
class CurationContext:
    """What a layer may read. Built by the application; layers do not fetch beyond it, except the
    dispositive backtest, which replays against the case store through its own injected services."""

    run_id: str
    arm: str
    at_idx: int
    sources: Sequence[Observation]
    neighbours: Sequence[tuple[Decision, float]] = field(default_factory=tuple)


@runtime_checkable
class Layer(Protocol):
    name: str                    # L0 … L5
    role: LayerRole | None

    async def check(self, draft: Draft, ctx: CurationContext) -> LayerOutcome: ...


@runtime_checkable
class Curator(Protocol):
    name: str
    layers: Sequence[Layer]

    @property
    def governed(self) -> bool:
        """True iff some layer is dispositive."""
        ...

    async def curate(self, draft: Draft, ctx: CurationContext) -> list[LayerOutcome]:
        """Run layers cheapest first; stop at the first hold, refuse or admit."""
        ...


@runtime_checkable
class LensPanel(Protocol):
    """The corroborating panel. Reads only the fields its lens entries' `pointer` names (§ 23.2)."""

    id: str

    async def score(self, draft: Draft, sources: Sequence[Observation],
                    neighbours: Sequence[Decision]) -> dict[str, float]: ...


@runtime_checkable
class Adjudicator(Protocol):
    """Where a draft goes after nomination: the arm's curator, then the lifecycle on admit, then the
    draft's and its source observations' dispositions. Built by the composition root (`bootstrap_learn`);
    the episodic pass and the injection control hand drafts here and never call the curator directly."""

    async def adjudicate(self, draft: Draft, ctx: CurationContext) -> list[LayerOutcome]: ...
