"""Models port (SPEC § 21): one method per LLM party. Model ids come from config, never from callers.

Inputs are plain dataclasses assembled by the application; wire schemas for a provider live in `impl/`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from munchhausen.domain.common import Answer
from munchhausen.domain.decision import Decision, EntryContract
from munchhausen.domain.draft import Shape
from munchhausen.domain.episode import Episode, Proposal
from munchhausen.domain.observation import Observation, ObservationNote
from munchhausen.domain.question import Question, SchemaSummary
from munchhausen.ports.store import DocumentReader


@dataclass(frozen=True)
class ProposerInput:
    question: Question
    schema: SchemaSummary
    consulted: Sequence[Decision]                 # packed by hooks or retrieval; never the always-loaded set
    retry_figure: Answer = None                   # the authority's figure, on the unscored retry
    retry_phrasing: str | None = None
    arm: str = ""
    stage: str = "propose"                        # propose | retry | replay (spend accounting)


@dataclass(frozen=True)
class SelfGrade:
    correct: bool
    lesson: str | None = None


@dataclass(frozen=True)
class NominatorInput:
    shape: Shape
    sources: Sequence[Observation]
    episodes: Sequence[Episode]
    vocabulary: Sequence[str]
    world: DocumentReader                         # read-only world query tool (or the MCP server, § 20.2)
    neighbours: Sequence[Decision] = field(default_factory=tuple)


@runtime_checkable
class Models(Protocol):
    async def propose(self, inp: ProposerInput) -> Proposal: ...

    async def observe(self, episode: Episode) -> list[ObservationNote]:
        """Write blind: the observer never reads other observations (§ 23.1)."""
        ...

    async def nominate(self, inp: NominatorInput) -> tuple[EntryContract, tuple[str, ...]]:
        """Return the drafted entry and any escaped new terms."""
        ...

    async def self_grade(self, episode: Episode) -> SelfGrade:
        """self_ref only: the proposer grades itself as 'the subject-matter expert'."""
        ...

    async def planted_map(self, decision: Decision, pack_definitions: str) -> str | None:
        """Evaluation only: map an admitted decision to a quirk id, or None."""
        ...
