"""self_ref self-grade party (SPEC § 5). Owner: adjudication surface (M3)."""

from __future__ import annotations

from munchhausen.config import Settings
from munchhausen.domain.episode import Episode
from munchhausen.impl.parties import LLM
from munchhausen.ports.models import SelfGrade


async def run(llm: LLM, settings: Settings, episode: Episode) -> SelfGrade:
    raise NotImplementedError("M3: self_ref self-grade as 'the subject-matter expert'")
