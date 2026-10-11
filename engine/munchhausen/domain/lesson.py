"""Lessons: the write unit of the ungoverned arms (SPEC § 5).

`naive` writes one lesson per reducible observation; `self_ref` writes one per self-judged miss. A lesson is
what off-the-shelf agent memory stores: a title and a payload, admitted directly. It becomes a decision only
by admission, through `lesson_entry`, which fills the entry contract mechanically so every arm's store holds
one record shape. The filled slots are disclosed as ungoverned: one chosen option and no rejected row, a hook
copied from the source episode's legible keys (it scopes residual attribution only; these arms consult by
semantic retrieval), no revisit latch.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Literal

from munchhausen.domain.common import DecisionKind, Value
from munchhausen.domain.decision import EntryContract, Option, Warrant, leaked_figures
from munchhausen.domain.latches import HookLatch, KeySet

UNGOVERNED_RESIDUE = "admitted without a backtest, a rejected option or a revisit latch; nothing checks it"
UNGOVERNED_FALSIFIER = "none: no dispositive latch"


class Lesson(Value):
    """What the lesson writer emits. Never a floor: an ungoverned arm rewires no tool access."""

    title: str
    kind: Literal[DecisionKind.TAXONOMIC, DecisionKind.PROCEDURAL, DecisionKind.PREFERENCE]
    payload: str


def lesson_entry(lesson: Lesson, *, terms: Sequence[str], collections: Sequence[str],
                 observation_ids: Sequence[str], episode_ids: Sequence[str], templates: int) -> EntryContract:
    return EntryContract(
        title=lesson.title, kind=lesson.kind, payload=lesson.payload,
        options=(Option(definition=lesson.payload, verdict="chosen"),),
        forecloses="",
        latches=(HookLatch(fires_when=KeySet(terms=tuple(terms), collections=tuple(collections))),),
        residue=UNGOVERNED_RESIDUE,
        warrant=Warrant(source_observation_ids=tuple(observation_ids), source_episode_ids=tuple(episode_ids),
                        templates=templates, falsifier=UNGOVERNED_FALSIFIER),
    )


def lesson_violations(entry: EntryContract, source_figures: Iterable[float]) -> list[str]:
    """The L0 a lesson can carry: a title, a payload, and no source figure in the payload."""
    out = []
    if not entry.title.strip() or not entry.payload.strip():
        out.append("a lesson needs a title and a payload")
    leaked = leaked_figures(entry.payload, source_figures)
    if leaked:
        out.append(f"payload contains a source figure: {leaked}")
    return out
