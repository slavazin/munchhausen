"""Question templates and the seeded stream (SPEC § 4.3).

About 12 templates × parameters (year, quarter, ticker set, tier, persona). 65% touch a quirk, 35% are
controls. Hidden tags (quirk ids) stay in `QuestionBank`; only `Question` crosses the World port.

**One quirk per question.** A quirk-bearing template touches exactly one quirk; a preference persona (P1,
Dana) is drawn on control templates only. With binary scoring, a question touching two quirks rewards a
correct decision for one of them with nothing until the other is admitted too, so the backtest can't
credit it, the nominator can't reproduce its figures, and the authority's phrasing can name the quirk the
answer got right. The pack's materialization places overlapping populations where the other quirks'
definitions already exclude them; a gold test asserts each quirk template's gold is unchanged by every
other quirk's gold transform.
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


def hidden_quirks(template: Template, persona: str, persona_quirks: dict[str, str]) -> tuple[str, ...]:
    """The quirk ids a (template, persona) question touches; refuses any pairing that touches two."""
    quirks = (*template.quirks, *((persona_quirks[persona],) if persona in persona_quirks else ()))
    if len(quirks) > 1:
        raise ValueError(f"{template.id} as {persona} touches {quirks}: one quirk per question")
    return quirks


class QuestionBank:
    """Generates questions and remembers each one's hidden tags for gold and the authority.

    `persona_quirks` maps a preference persona to its quirk (Dana → P1); such a persona is drawn only on
    control templates."""

    def __init__(self, templates: tuple[Template, ...], personas: tuple[str, ...], quirk_share: float,
                 persona_quirks: dict[str, str] | None = None) -> None:
        self._templates, self._personas, self._share = templates, personas, quirk_share
        self._persona_quirks = dict(persona_quirks or {})
        bad = [t.id for t in templates if len(t.quirks) > 1]
        if bad:
            raise ValueError(f"templates touching more than one quirk: {bad}")
        self._hidden: dict[str, Hidden] = {}

    def stream(self, seed: int) -> Iterator[Question]:
        raise NotImplementedError("M1: seeded draw honouring QUIRK_SHARE; preference personas on controls "
                                  "only; hidden_quirks per question; ids stable per (seed, i)")

    def v_set(self, seed: int, size: int) -> tuple[Question, ...]:
        raise NotImplementedError("M1: sealed V set from its own seed, disjoint from the stream")

    def hidden(self, question_id: str) -> Hidden:
        return self._hidden[question_id]
