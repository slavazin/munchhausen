"""Nominator (SPEC § 7.2 step 4): generalizes one shape into the decision that settles it.

Before drafting, the nominator is shown the current store where it bears on the shape: the NEIGHBOUR_K
admitted decisions nearest the shape, with their recent residuals. A nominator that drafts blind
rediscovers what the store already holds. Those neighbours are handed on to L2 in the curation context,
so the nearest-neighbour read runs once per draft.

Runs the prior convention first through the read-only world tool and records it as a rejected option;
never writes a definition it has not run (`warrant.figures_reproduced`).

Reads only the shape's own episodes and observations (`NominatorInput` refuses anything else), so the
backtest population's confirmed figures stay unseen.
"""

from __future__ import annotations

from dataclasses import dataclass

from munchhausen.domain.draft import Draft, Shape
from munchhausen.ports.models import Models
from munchhausen.ports.representation import Representation, Similarity
from munchhausen.ports.store import (
    DecisionRepository,
    DocumentReader,
    EpisodeRepository,
    ObservationRepository,
    TermRepository,
)


@dataclass
class Nominator:
    models: Models
    world: DocumentReader
    episodes: EpisodeRepository
    observations: ObservationRepository
    terms: TermRepository
    decisions: DecisionRepository
    representation: Representation
    similarity: Similarity
    neighbour_k: int

    async def nominate(self, run_id: str, arm: str, round_: int, shape: Shape) -> Draft:
        raise NotImplementedError(
            "M3: shape episodes/observations by id → neighbours = similarity.knn(admitted, shape text, "
            "neighbour_k) + their residuals (consultations_of) → NominatorInput → models.nominate "
            "→ Draft(id=draft_id(...))")
