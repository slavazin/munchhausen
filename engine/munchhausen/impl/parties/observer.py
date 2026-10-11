"""Observer party (SPEC § 7.1, § 23.1). Owner: backward-pass shaping surface (M3)."""

from __future__ import annotations

from munchhausen.config import Settings
from munchhausen.domain.episode import Episode
from munchhausen.domain.observation import ObservationNote
from munchhausen.impl.parties import LLM


async def run(llm: LLM, settings: Settings, episode: Episode) -> list[ObservationNote]:
    raise NotImplementedError("M3: observer prompt compiled from § 23.1; noise filter; written blind")
