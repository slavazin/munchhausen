"""Consultation (SPEC § 6.2, § 20.3): which decisions reach the proposer, and in what order.

Strategy per arm (`ConsultationMode`): hooks (governed), semantic top-k (naive, self_ref), none (frozen).
The always-loaded set holds the schema summary and tool contract only; learned content arrives here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from munchhausen.domain.arm import ConsultationMode
from munchhausen.domain.decision import Decision
from munchhausen.domain.question import Question, QuestionKeys
from munchhausen.ports.representation import Reranker
from munchhausen.ports.store import DecisionRepository, TermRepository


class Consulter(Protocol):
    async def consult(self, run_id: str, arm: str, question: Question) -> tuple[QuestionKeys, list[Decision]]: ...


@dataclass
class HookConsulter:
    decisions: DecisionRepository
    terms: TermRepository
    reranker: Reranker
    budget_tokens: int

    async def consult(self, run_id: str, arm: str, question: Question) -> tuple[QuestionKeys, list[Decision]]:
        keys = QuestionKeys(terms=await self.terms.extract(question.text),
                            collections=frozenset(question.collections), persona=question.persona)
        matched = await self.decisions.match_hooks(run_id, arm, keys)
        return keys, await pack(question.text, matched, self.reranker, self.budget_tokens)


@dataclass
class SemanticConsulter:
    """Top-k retrieval: the shape of off-the-shelf agent memory (SPEC § 5 premise names the confound)."""

    top_k: int

    async def consult(self, run_id: str, arm: str, question: Question) -> tuple[QuestionKeys, list[Decision]]:
        raise NotImplementedError("M2: embed question → Similarity.knn over decisions → rerank → pack")


@dataclass
class NoConsulter:
    async def consult(self, run_id: str, arm: str, question: Question) -> tuple[QuestionKeys, list[Decision]]:
        return QuestionKeys(terms=frozenset(), collections=frozenset(question.collections),
                            persona=question.persona), []


async def pack(query: str, decisions: Sequence[Decision], reranker: Reranker, budget_tokens: int) -> list[Decision]:
    """Order by rerank relevance; pack to CONTEXT_BUDGET_TOKENS (≈ 4 chars per token)."""
    if not decisions:
        return []
    order = await reranker.rerank(query, [f"{d.title}\n{d.payload}" for d in decisions])
    out, used = [], 0
    for i, _ in order:
        d = decisions[i]
        cost = (len(d.title) + len(d.payload)) // 4 + 8
        if used + cost > budget_tokens:
            break
        out.append(d)
        used += cost
    return out


def consulter_for(mode: ConsultationMode, **deps: object) -> Consulter:
    raise NotImplementedError("M2: build from ArmSpec.consultation (composition root wires deps)")
