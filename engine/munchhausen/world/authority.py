"""The authority: the stakeholder simulator (SPEC § 4.4). Deterministic templates, no LLM.

On a wrong first attempt, in arms that receive it: `terse` (figure), `term` (figure + one phrasing naming
the question's quirk, never its definition), or `rule` (control only). Every question touches at most one
quirk (`world/questions.py`), so the phrasing names the concept the answer actually missed — never a
co-occurring quirk the answer got right. N1 swaps in a poisoned figure under the same phrasing with
probability AUTHORITY_POISON_RATE.
"""

from __future__ import annotations

from munchhausen.domain.common import Answer, AuthorityLevel
from munchhausen.domain.episode import Judgement
from munchhausen.domain.question import Question
from munchhausen.domain.scoring import matches
from munchhausen.ports.world import Truth
from munchhausen.world.pack import Pack
from munchhausen.world.questions import QuestionBank


class Authority:
    def __init__(self, truth: Truth, pack: Pack, bank: QuestionBank, level: AuthorityLevel,
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
        return Judgement(correct=False, figure=self._figure(question, gold, idx),
                         phrasing=self._phrasing(question, idx))

    def _abs_tol_for(self, question: Question) -> float:
        raise NotImplementedError("M1: absolute tolerance after Dana rounding (P1), else 0")

    def _figure(self, question: Question, gold: Answer, idx: int) -> Answer:
        raise NotImplementedError("M1: N1 poison draw under (seed, idx), else gold")

    def _phrasing(self, question: Question, idx: int) -> str | None:
        raise NotImplementedError("M1: the question's one quirk (bank.hidden); phrasing per AUTHORITY_LEVEL")
