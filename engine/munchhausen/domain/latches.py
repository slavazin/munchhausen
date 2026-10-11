"""The latch fan of an entry (SPEC § 10.2): hook, revisit, floor, retire, wiring.

Matching logic lives here as pure functions so the Atlas query plan (§ 20.3) and the in-process fallback
are tested against the same definition.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from munchhausen.domain.common import FireRole, Signature, Value
from munchhausen.domain.question import QuestionKeys


class KeySet(Value):
    terms: tuple[str, ...] = ()
    collections: tuple[str, ...] = ()
    persona: str | None = None

    def is_empty(self) -> bool:
        return not self.terms and not self.collections and self.persona is None


class NotThisRow(KeySet):
    contrast: str   # one instantiated case the hook matches and must not bind (§ 22.5)

    def all_present(self, keys: QuestionKeys) -> bool:
        """A `not_this` row binds when every one of its keys is present in the question's keys."""
        if self.is_empty():
            return False
        return (
            set(self.terms) <= keys.terms
            and set(self.collections) <= keys.collections
            and (self.persona is None or self.persona == keys.persona)
        )


class HookLatch(Value):
    type: Literal["hook"] = "hook"
    fires_when: KeySet
    not_this: tuple[NotThisRow, ...] = ()

    def matches(self, keys: QuestionKeys) -> bool:
        """`fires_when` intersects the question's keys, persona scope holds, and no `not_this` row binds."""
        fw = self.fires_when
        if fw.persona is not None and fw.persona != keys.persona:
            return False
        if not (set(fw.terms) & keys.terms or set(fw.collections) & keys.collections):
            return False
        return not any(row.all_present(keys) for row in self.not_this)


class Guard(Value):
    min_residuals: int
    window: int


class RevisitLatch(Value):
    type: Literal["revisit"] = "revisit"
    id: str
    signature: Signature
    guard: Guard
    role: FireRole = FireRole.DISPOSITIVE
    then: Literal["re-derive"] = "re-derive"


class FloorLatch(Value):
    type: Literal["floor"] = "floor"
    collection: str             # logical collection the view shadows
    match: dict[str, Any]       # the `$match` predicate prepended in the view


class MootWhen(Value):
    idle_episodes: int


class RetireLatch(Value):
    type: Literal["retire"] = "retire"
    id: str
    moot_when: MootWhen
    max_fires: int
    then: Literal["retire"] = "retire"


class WiringLatch(Value):
    type: Literal["wiring"] = "wiring"
    supersedes: str | None = None
    converged_from: tuple[str, ...] = ()
    related: tuple[str, ...] = ()
    edges: tuple[str, ...] = ()   # union of the three; the single `connectFromField` for $graphLookup

    @classmethod
    def build(
        cls, supersedes: str | None = None, converged_from: tuple[str, ...] = (), related: tuple[str, ...] = ()
    ) -> WiringLatch:
        edges = tuple(dict.fromkeys(([supersedes] if supersedes else []) + [*converged_from, *related]))
        return cls(supersedes=supersedes, converged_from=converged_from, related=related, edges=edges)


Latch = Annotated[HookLatch | RevisitLatch | FloorLatch | RetireLatch | WiringLatch, Field(discriminator="type")]
