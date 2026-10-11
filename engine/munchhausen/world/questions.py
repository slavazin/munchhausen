"""Question templates and the seeded stream (SPEC § 4.3).

About 12 templates × parameters (year, quarter, ticker set, tier, persona). 65% touch ≥ 1 quirk, 35% are
controls. Hidden tags (quirk ids) stay in `QuestionBank`; only `Question` crosses the World port.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from munchhausen.domain.question import Question


@dataclass(frozen=True)
class Template:
    id: str
    text: str                                  # format string over params
    collections: tuple[str, ...]
    quirks: tuple[str, ...]                    # hidden tags
    params: dict[str, tuple[Any, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class Hidden:
    quirks: tuple[str, ...]
    params: dict[str, Any]


class QuestionBank:
    """Generates questions and remembers each one's hidden tags for gold and the authority."""

    def __init__(self, templates: tuple[Template, ...], personas: tuple[str, ...], quirk_share: float) -> None:
        self._templates, self._personas, self._share = templates, personas, quirk_share
        self._hidden: dict[str, Hidden] = {}

    def stream(self, seed: int) -> Iterator[Question]:
        raise NotImplementedError("M1: seeded draw honouring QUIRK_SHARE; ids stable per (seed, i)")

    def v_set(self, seed: int, size: int) -> tuple[Question, ...]:
        raise NotImplementedError("M1: sealed V set from its own seed, disjoint from the stream")

    def hidden(self, question_id: str) -> Hidden:
        return self._hidden[question_id]
