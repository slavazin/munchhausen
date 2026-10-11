"""`PackGold`: gold answers from the pack's gold transforms, per world version (SPEC § 4.3).

Holds the only handle on the `truth` database (definitions per world version) and runs gold pipelines
over `world`. Never imported under `learn/`, `agent/` or `loop/`.
"""

from __future__ import annotations

from munchhausen.domain.common import Answer
from munchhausen.domain.question import Question
from munchhausen.ports.store import DocumentReader
from munchhausen.world.pack import Pack
from munchhausen.world.questions import QuestionBank


class PackGold:
    def __init__(self, pack: Pack, bank: QuestionBank, world: DocumentReader, truth: DocumentReader,
                 max_time_ms: int) -> None:
        self._pack, self._bank, self._world, self._truth = pack, bank, world, truth
        self._max_time_ms = max_time_ms

    async def gold(self, question: Question, world_version: str) -> Answer:
        raise NotImplementedError("M1: compose GOLD transforms for the question's hidden quirks at world_version")
