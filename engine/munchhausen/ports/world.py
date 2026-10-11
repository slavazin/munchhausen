"""World and Truth ports (SPEC § 21).

`World` abstracts the dataset adapter, quirk pack, question stream and authority. The engine imports no
adapter module; it receives a `World` from the composition root.

`Truth` is evaluation-only. It may be imported from `metrics/`, `world/` and tests — never from
`learn/`, `agent/` or `loop/`. An architecture test enforces this, and Atlas roles enforce it at the
database (§ 20.2).
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, runtime_checkable

from munchhausen.domain.common import Answer
from munchhausen.domain.episode import Judgement
from munchhausen.domain.question import Question, SchemaSummary


@runtime_checkable
class World(Protocol):
    id: str   # "<adapter>+<pack>"

    async def build(self, seed: int) -> dict[str, int]:
        """Materialize the `world` database deterministically; return document counts per collection."""
        ...

    def schema_summary(self) -> SchemaSummary: ...

    def questions(self, seed: int) -> Iterator[Question]:
        """The unbounded stream (SPEC § 4.3). Index i of the iterator is stream index i."""
        ...

    def v_set(self) -> Sequence[Question]:
        """The sealed V set: fixed seed, never in the stream."""
        ...

    def world_version(self, idx: int) -> str:
        """Derived from the stream index and the pack's drift schedule."""
        ...

    async def judge(self, question: Question, answer: Answer, idx: int, *, with_authority: bool) -> Judgement:
        """Score the first attempt; on a miss and `with_authority`, return the authority's figure and phrasing."""
        ...


@runtime_checkable
class Truth(Protocol):
    async def gold(self, question: Question, world_version: str) -> Answer: ...
