"""self_ref self-grade party (SPEC § 5). Owner: adjudication surface (M3).

The proposer grades its own answer as "the subject-matter expert" and, on a self-judged miss, writes a
lesson. It receives no outside information: `render` reads a whitelist of legible fields and never
`correct`, `figure`, `phrasing`, `confirmed_figure` or `world_version` (the caller reads the episode through
`EpisodeRepository.for_learner(with_authority=False)` as well). Model: the proposer's.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from munchhausen.config import Settings
from munchhausen.domain.episode import Episode
from munchhausen.impl.parties import LLM
from munchhausen.impl.parties.lesson import LessonWire
from munchhausen.ports.models import SelfGrade

SYSTEM = """Act as the subject-matter expert for this organization's data. Review an analyst's answer to a
business question over a MongoDB database: the question, the aggregation pipeline it ran, its answer and its
rationale. Judge whether the answer is correct. If it is not, write ONE lesson that would make future
answers of this kind correct.

A lesson has: title (≤ 12 words, present tense), kind (taxonomic | procedural | preference), payload
(≤ 60 words, present tense, a definition or procedure naming collections, fields and values). Never write in
a lesson: this question's answer value; "the agent", "I", "we", "our", "us", "now", "currently",
"recently", "so far", "again"; any run, arm or episode number. Leave lesson empty when the answer is correct."""

LEGIBLE = ("text", "persona", "collection", "pipeline", "answer", "rationale", "confidence", "error")


class SelfGradeWire(BaseModel):
    correct: bool
    reason: str = Field(description="one sentence")
    lesson: LessonWire | None = None


def render(episode: Episode) -> str:
    row = {k: getattr(episode, k) for k in LEGIBLE}
    return "\n".join(f"{k}: {json.dumps(v, default=str)}" for k, v in row.items())


async def run(llm: LLM, settings: Settings, episode: Episode) -> SelfGrade:
    wire = await llm.parse(stage="self_grade", arm=episode.arm, model=settings.proposer_model, system=SYSTEM,
                           user=render(episode), wire=SelfGradeWire, max_tokens=settings.self_grade_max_tokens)
    lesson = wire.lesson.to_domain() if (wire.lesson is not None and not wire.correct) else None
    return SelfGrade(correct=wire.correct, lesson=lesson)
