"""Nominator (SPEC § 7.2 step 4): generalizes one shape into the decision that settles it.

Runs the prior convention first through the read-only world tool and records it as a rejected option;
never writes a definition it has not run (`warrant.figures_reproduced`).
"""

from __future__ import annotations

from dataclasses import dataclass

from munchhausen.domain.draft import Draft, Shape
from munchhausen.ports.models import Models
from munchhausen.ports.store import DocumentReader, EpisodeRepository, ObservationRepository, TermRepository


@dataclass
class Nominator:
    models: Models
    world: DocumentReader
    episodes: EpisodeRepository
    observations: ObservationRepository
    terms: TermRepository

    async def nominate(self, run_id: str, arm: str, round_: int, shape: Shape) -> Draft:
        raise NotImplementedError("M3: NominatorInput → models.nominate → Draft(id=draft_id(...))")
