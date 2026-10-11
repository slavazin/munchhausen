"""The proposer: the agent being improved (SPEC § 6.1). A thin service over the Models port that holds
the tool contract and the consultation-language framing (§ 22.6)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from munchhausen.domain.common import Answer
from munchhausen.domain.decision import Decision
from munchhausen.domain.episode import Proposal
from munchhausen.domain.question import Question, SchemaSummary
from munchhausen.ports.models import Models, ProposerInput


@dataclass
class Proposer:
    models: Models

    async def propose(self, arm: str, question: Question, schema: SchemaSummary,
                      consulted: Sequence[Decision], *, stage: str = "propose") -> Proposal:
        return await self.models.propose(ProposerInput(question=question, schema=schema, consulted=consulted,
                                                       arm=arm, stage=stage))

    async def retry(self, arm: str, question: Question, schema: SchemaSummary, consulted: Sequence[Decision],
                    figure: Answer, phrasing: str | None) -> Proposal:
        return await self.models.propose(ProposerInput(question=question, schema=schema, consulted=consulted,
                                                       retry_figure=figure, retry_phrasing=phrasing,
                                                       arm=arm, stage="retry"))
