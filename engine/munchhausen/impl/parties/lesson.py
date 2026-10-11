"""naive lesson writer party (SPEC § 5 Lessons). Owner: adjudication surface (M3)."""

from __future__ import annotations

from munchhausen.config import Settings
from munchhausen.domain.episode import Episode
from munchhausen.domain.lesson import Lesson
from munchhausen.domain.observation import Observation
from munchhausen.impl.parties import LLM


async def run(llm: LLM, settings: Settings, episode: Episode, observation: Observation) -> Lesson:
    raise NotImplementedError("M3: naive lesson writer (NAIVE_LESSON_MODEL) → Lesson")
