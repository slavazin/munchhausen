"""Observer (SPEC § 7.1, § 23.1): one observation per noticing on each miss, written blind.

The noise filter classifies each miss as reducible or irreducible; irreducible observations are stored
with disposition `noise` and never join a shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from munchhausen.domain.episode import Episode
from munchhausen.domain.observation import Observation
from munchhausen.ports.models import Models
from munchhausen.ports.representation import Representation
from munchhausen.ports.store import ObservationRepository


@dataclass
class Observer:
    models: Models
    representation: Representation
    observations: ObservationRepository

    async def observe(self, episode: Episode, round_: int) -> list[Observation]:
        raise NotImplementedError(
            "M3: models.observe(episode) → ObservationNote[] → lint_language → embed `noticed` "
            "(EMBED_MASK) → Observation(disposition=noise if irreducible) → put")
