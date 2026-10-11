"""Questions as the harness sees them.

A `Question` carries only legible fields. The quirk ids a question touches are hidden tags held on the
world side of the boundary (`world/`); they never enter the domain, the stores the learner reads, or the
proposer's prompt (SPEC § 4.3).
"""

from __future__ import annotations

from munchhausen.domain.common import Value


class Question(Value):
    id: str
    text: str
    template: str
    persona: str
    collections: tuple[str, ...]   # the template's logical collections


class QuestionKeys(Value):
    """The keys a hook is evaluated against (SPEC § 6.2): extracted terms, collections, persona."""

    terms: frozenset[str]
    collections: frozenset[str]
    persona: str | None = None


class SchemaSummary(Value):
    """Field names and types per logical collection; never meanings (SPEC § 4.1)."""

    collections: dict[str, dict[str, str]]
