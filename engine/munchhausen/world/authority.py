"""The authority: the stakeholder simulator (SPEC § 4.4). Deterministic templates, no LLM.

On a wrong first attempt, in arms that receive it: `terse` (figure), `term` (figure + one phrasing naming
the question's quirk, never its definition), or `rule` (control only). Every question touches at most one
quirk (`world/questions.py`), so the phrasing names the concept the answer actually missed — never a
co-occurring quirk the answer got right. A control question's miss gets the figure alone: there is no
concept to name. N1 swaps in a poisoned figure under the same phrasing with probability
AUTHORITY_POISON_RATE, drawn under (seed, idx) so every arm meets the same lie at the same stream index.
A poison variant exists only for quirks the pack's poison bank names; controls are never poisoned.
"""

from __future__ import annotations

from typing import Any

from munchhausen.domain.common import Answer, AuthorityLevel, Signature
from munchhausen.domain.episode import Judgement
from munchhausen.domain.question import Question
from munchhausen.domain.scoring import matches
from munchhausen.truth.gold import PackGold
from munchhausen.world.pack import Pack
from munchhausen.world.questions import QuestionBank
from munchhausen.world.transforms import stable_bucket, stable_unit


class Authority:
    def __init__(self, truth: PackGold, pack: Pack, bank: QuestionBank, level: AuthorityLevel,
                 poison_rate: float, rel_tol: float, abs_tol_rounded: float, seed: int) -> None:
        self._truth, self._pack, self._bank = truth, pack, bank
        self._level, self._poison_rate = level, poison_rate
        self._rel_tol, self._abs_tol_rounded, self._seed = rel_tol, abs_tol_rounded, seed

    async def judge(self, question: Question, answer: Answer, world_version: str, idx: int, *,
                    with_authority: bool) -> Judgement:
        gold = await self._truth.gold(question, world_version)
        correct = matches(answer, gold, rel_tol=self._rel_tol, abs_tol=self._abs_tol_for(question))
        if correct or not with_authority:
            return Judgement(correct=correct)
        return Judgement(correct=False, figure=await self._figure(question, gold, idx, world_version),
                         phrasing=self._phrasing(question, idx))

    def _quirk(self, question: Question) -> Any:
        quirks = self._bank.hidden(question.id).quirks
        return self._pack.quirk(quirks[0]) if quirks else None

    def _abs_tol_for(self, question: Question) -> float:
        q = self._quirk(question)
        return self._abs_tol_rounded if q is not None and q.signature == Signature.ROUNDING else 0.0

    def poison_index(self, question: Question, idx: int) -> int | None:
        """The poison bank index applied at (seed, idx) for this question, or None (deterministic)."""
        q = self._quirk(question)
        if q is None or stable_unit(f"poison:{idx}", self._seed) >= self._poison_rate:
            return None
        ks = [k for k, v in enumerate(self._pack.poison_bank) if v.params.get("quirk") == q.id]
        if not ks:
            return None
        return ks[stable_bucket(f"poison-variant:{idx}", self._seed) % len(ks)]

    def poison_variant(self, question: Question, idx: int) -> dict[str, Any] | None:
        k = self.poison_index(question, idx)
        return None if k is None else dict(self._pack.poison_bank[k].params)

    async def _figure(self, question: Question, gold: Answer, idx: int, world_version: str) -> Answer:
        v = self.poison_variant(question, idx)
        if v is None:
            return gold
        params = {k: val for k, val in v.items() if k != "quirk"}
        return await self._truth.variant(question, world_version, v["quirk"], params)

    def _phrasing(self, question: Question, idx: int) -> str | None:
        q = self._quirk(question)
        if self._level == AuthorityLevel.TERSE or q is None or not q.authority_phrasings:
            return None
        phrasing = q.authority_phrasings[stable_bucket(f"phrasing:{idx}", self._seed) % len(q.authority_phrasings)]
        if self._level == AuthorityLevel.RULE and q.definition:
            return f"{phrasing} {q.definition}"
        return phrasing
