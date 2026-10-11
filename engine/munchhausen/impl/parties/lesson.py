"""naive lesson writer party (SPEC § 5 Lessons). Owner: adjudication surface (M3).

The off-the-shelf reflection step: one missed question in, one lesson out. It reads the episode, the
observation's `noticed`, the authority's figure and phrasing, and the retry pipeline with `retry_correct`.
Model `NAIVE_LESSON_MODEL` (= the nominator's model, so the payload's author is not a confound). The prompt
states the lesson voice of `corpus/LANGUAGE.md` § 5 so the language lint at L0 measures the arm, not the
prompt.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from munchhausen.config import Settings
from munchhausen.domain.common import DecisionKind
from munchhausen.domain.episode import Episode
from munchhausen.domain.lesson import Lesson
from munchhausen.domain.observation import Observation
from munchhausen.impl.parties import LLM

SYSTEM = """You keep a memory of lessons for a data analyst who answers business questions by writing MongoDB
aggregation pipelines. You are shown one question the analyst answered differently from the stakeholder,
the pipeline it ran, the stakeholder's expected figure and remark, and a retry. Write ONE lesson that would
help answer future questions of this kind correctly.

Write the lesson as:
- title: the constraint in at most 12 words, present tense.
- kind: taxonomic (what a business term means in the data), procedural (how to compute something), or
  preference (how one requester wants answers presented).
- payload: at most 60 words, present tense, a definition or procedure naming collections, fields and values.

Never write in a payload or title: any number that is this question's answer or the stakeholder's figure;
the words "the agent", "I", "we", "our", "us", "now", "currently", "recently", "so far", "again"; any run,
arm or episode number. State the rule, not the story of this question."""


class LessonWire(BaseModel):
    title: str = Field(description="≤ 12 words, present tense")
    kind: Literal["taxonomic", "procedural", "preference"]
    payload: str = Field(description="≤ 60 words, a definition or procedure")

    def to_domain(self) -> Lesson:
        return Lesson(title=self.title.strip(), kind=DecisionKind(self.kind), payload=self.payload.strip())


def render(episode: Episode, observation: Observation) -> str:
    return "\n".join([
        f"Question: {episode.text}",
        f"Requester: {episode.persona}",
        f"Collection: {episode.collection}",
        f"Pipeline run: {json.dumps(episode.pipeline, default=str)}",
        f"Analyst's answer: {json.dumps(episode.answer, default=str)}",
        f"Stakeholder's expected figure: {json.dumps(episode.figure, default=str)}",
        f"Stakeholder's remark: {episode.phrasing or '(none)'}",
        f"What was noticed: {observation.noticed}",
        f"Retry pipeline: {json.dumps(episode.retry_pipeline, default=str)}",
        f"Retry matched the expected figure: {episode.retry_correct}",
    ])


async def run(llm: LLM, settings: Settings, episode: Episode, observation: Observation) -> Lesson:
    wire = await llm.parse(stage="lesson", arm=episode.arm, model=settings.naive_lesson_model, system=SYSTEM,
                           user=render(episode, observation), wire=LessonWire, max_tokens=settings.lesson_max_tokens)
    return wire.to_domain()
