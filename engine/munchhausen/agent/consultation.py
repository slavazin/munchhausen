"""Consultation (SPEC § 6.2, § 20.3): which decisions reach the proposer, and in what order.

Strategy per arm (`ConsultationMode`): hooks (governed), semantic top-k (naive, self_ref), none (frozen).
The always-loaded set holds the schema summary and tool contract only; learned content arrives here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from munchhausen.agent.terms import STOPWORDS, tokens
from munchhausen.domain.arm import ArmSpec, ConsultationMode
from munchhausen.domain.common import LifecycleStatus
from munchhausen.domain.decision import Decision
from munchhausen.domain.question import Question, QuestionKeys
from munchhausen.ports.representation import Representation, Reranker, Similarity
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
        keys = QuestionKeys(terms=await self.terms.extract(question.text, run_id=run_id),
                            collections=frozenset(question.collections), persona=question.persona)
        matched = await self.decisions.match_hooks(run_id, arm, keys)
        return keys, await pack(question.text, matched, self.reranker, self.budget_tokens)


@dataclass
class SemanticConsulter:
    """Top-k retrieval: the shape of off-the-shelf agent memory (SPEC § 5 premise names the confound).

    Representation → Similarity.knn over the arm's admitted decisions → rerank → pack. Under the null
    representation (no embedding key) it ranks by token overlap between the question and each decision's
    title and payload, so the forward pass keeps working offline; the fallback is the port's null
    implementation, recorded in `runs.ports`, never a silent swap."""

    decisions: DecisionRepository
    terms: TermRepository
    representation: Representation
    similarity: Similarity
    reranker: Reranker
    top_k: int
    budget_tokens: int

    async def consult(self, run_id: str, arm: str, question: Question) -> tuple[QuestionKeys, list[Decision]]:
        keys = QuestionKeys(terms=await self.terms.extract(question.text, run_id=run_id),
                            collections=frozenset(question.collections), persona=question.persona)
        admitted = {d.id: d for d in await self.decisions.admitted(run_id, arm)}
        if not admitted:
            return keys, []
        vec = await self.representation.embed([question.text], "query")
        if vec is None:
            ranked = lexical_top_k(question.text, list(admitted.values()), self.top_k)
        else:
            hits = await self.similarity.knn("decisions", [float(x) for x in vec[0]], self.top_k,
                                             {"run_id": run_id, "arm": arm,
                                              "lifecycle.status": LifecycleStatus.ADMITTED.value})
            ranked = [admitted[i] for i, _ in hits if i in admitted]
        return keys, await pack(question.text, ranked, self.reranker, self.budget_tokens)


def lexical_top_k(text: str, decisions: Sequence[Decision], k: int) -> list[Decision]:
    """Rank by the share of the question's tokens present in title + payload; ties keep store order."""
    q = set(tokens(text)) - STOPWORDS
    scored = [(len(q & set(tokens(f"{d.title} {d.payload}"))) / (len(q) or 1), i, d)
              for i, d in enumerate(decisions)]
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [d for score, _, d in scored[:k] if score > 0]


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


def consulter_for(spec: ArmSpec, *, decisions: DecisionRepository, terms: TermRepository,
                  representation: Representation, similarity: Similarity, reranker: Reranker,
                  top_k: int, budget_tokens: int) -> Consulter:
    """The arm's consultation, chosen by `ArmSpec.consultation` (never by the arm's name)."""
    if spec.consultation is ConsultationMode.HOOKS:
        return HookConsulter(decisions, terms, reranker, budget_tokens)
    if spec.consultation is ConsultationMode.SEMANTIC:
        return SemanticConsulter(decisions, terms, representation, similarity, reranker, top_k, budget_tokens)
    return NoConsulter()
