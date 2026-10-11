"""Models port (SPEC § 21): one method per LLM party. Model ids come from config, never from callers.

Inputs are plain dataclasses assembled by the application; wire schemas for a provider live in `impl/`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from munchhausen.domain.common import Answer
from munchhausen.domain.decision import Decision, EntryContract
from munchhausen.domain.draft import Shape
from munchhausen.domain.episode import Episode, Proposal, Residual
from munchhausen.domain.lesson import Lesson
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
    lesson: Lesson | None = None


@dataclass(frozen=True)
class NominatorInput:
    """What the nominator sees. Episodes are the shape's own and nothing else: the backtest population's
    confirmed figures stay unseen, so the held-out read stays held out. Neighbours (the admitted decisions
    nearest the shape) and their residuals are filled before drafting, so the nominator drafts against the
    current store and where it loses, not blind."""

    shape: Shape
    sources: Sequence[Observation]
    episodes: Sequence[Episode]
    vocabulary: Sequence[str]
    world: DocumentReader                         # read-only world query tool (or the MCP server, § 20.2)
    neighbours: Sequence[Decision] = field(default_factory=tuple)
    neighbour_residuals: Mapping[str, Sequence[Residual]] = field(default_factory=dict)   # decision id → recent

    def __post_init__(self) -> None:
        outside = {e.id for e in self.episodes} - set(self.shape.episode_ids)
        if outside:
            raise ValueError(f"nominator input holds episodes outside its shape: {sorted(outside)}")
        foreign = {o.id for o in self.sources} - set(self.shape.observation_ids)
        if foreign:
            raise ValueError(f"nominator input holds observations outside its shape: {sorted(foreign)}")


@runtime_checkable
class Models(Protocol):
    async def propose(self, inp: ProposerInput) -> Proposal: ...

    async def observe(self, episode: Episode) -> list[ObservationNote]:
        """Write blind: the observer never reads other observations (§ 23.1)."""
        ...

    async def nominate(self, inp: NominatorInput) -> tuple[EntryContract, tuple[str, ...]]:
        """Return the drafted entry and any escaped new terms."""
        ...

    async def lesson(self, episode: Episode, observation: Observation) -> Lesson:
        """naive only: one lesson per reducible observation. Sees the episode, the authority's figure and
        phrasing, and the retry pipeline with `retry_correct` — the off-the-shelf reflection step. Model:
        NAIVE_LESSON_MODEL (default: the nominator's model, so the payload's author is not a confound)."""
        ...

    async def self_grade(self, episode: Episode) -> SelfGrade:
        """self_ref only: the proposer grades itself as 'the subject-matter expert'."""
        ...

    async def planted_map(self, decision: Decision, pack_definitions: str) -> str | None:
        """Evaluation only: map an admitted decision to a quirk id, or None."""
        ...
