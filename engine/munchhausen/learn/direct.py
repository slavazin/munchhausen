"""The direct write path (SPEC § 5): `naive` and `self_ref`, no episodic pass.

`naive`: for each reducible observation, `Models.lesson(episode, observation)` writes one `Lesson`;
`self_ref`: `Models.self_grade(episode)` returns one on a self-judged miss, reading the episode blind (no
`correct`, figure, phrasing or confirmed figure: `EpisodeRepository.for_learner(with_authority=False)`).
`lesson_entry` fills the entry contract mechanically; the curator (`LessonShape` → `DirectAdmit`) admits it
through the same `Adjudicator` every arm uses.

**Merge** (`NAIVE_MERGE_COSINE`): a lesson whose embedding lies within the cosine of an admitted decision is
merged into it, the off-the-shelf memory's update step. A decision is frozen at admission, so a merge is a
successor, never an edit: the lesson is admitted with route `refine` and `converged_from` the merged
decision, which flips to `converged` with `converged_into` (a tombstone per merge). The successor carries
the new lesson's title and payload (latest wins, as an update-in-place memory does), the union of both
hooks' keys and both warrants' anchors. Both ungoverned arms merge, so they differ only in their signal.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from munchhausen.domain.common import emb_key
from munchhausen.domain.decision import Decision, Warrant
from munchhausen.domain.draft import Draft, Route
from munchhausen.domain.episode import EVALUATION_ONLY_FIELDS, Episode
from munchhausen.domain.ids import draft_id
from munchhausen.domain.latches import HookLatch, KeySet, WiringLatch
from munchhausen.domain.lesson import Lesson, lesson_entry
from munchhausen.domain.observation import Observation, ObservationClass, ObservationDisposition
from munchhausen.learn.adjudicate import decision_text
from munchhausen.ports.curation import Adjudicator, CurationContext
from munchhausen.ports.models import Models
from munchhausen.ports.representation import Representation
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import DecisionRepository, ObservationRepository

# Placeholders for the evaluation-only fields a blind episode never carries. The self-grade party renders a
# whitelist of legible fields (`impl/parties/self_grade.py`) and never these.
_BLIND = {"correct": False, "world_version": "", "figure": None, "phrasing": None, "confirmed_figure": None}


def blind(doc: dict[str, Any]) -> Episode:
    """An episode read through `for_learner(with_authority=False)`; refuses a doc that still holds any
    evaluation-only field, so a wrong read path fails loudly instead of leaking."""
    leaked = sorted(EVALUATION_ONLY_FIELDS & set(doc))
    if leaked:
        raise ValueError(f"blind read holds evaluation-only fields: {leaked}")
    return Episode.model_validate({**doc, **_BLIND})


def lesson_draft(lesson: Lesson, *, run_id: str, arm: str, round_: int, episode: Episode, key: str,
                 observation_ids: Sequence[str]) -> Draft:
    entry = lesson_entry(lesson, terms=episode.terms, collections=episode.collections or (episode.collection,),
                         observation_ids=observation_ids, episode_ids=(episode.id,), templates=1)
    return Draft(_id=draft_id(run_id, arm, round_, key), run_id=run_id, arm=arm, shape_id=f"L-{key}",
                 source_observation_ids=tuple(observation_ids), round=round_, **entry.model_dump())


def merged_draft(draft: Draft, into: Decision) -> Draft:
    """The lesson as a successor of `into`: route refine, `converged_from` it, keys and anchors unioned."""
    old, new = into.hook.fires_when, draft.hook.fires_when
    hook = HookLatch(fires_when=KeySet(terms=tuple(dict.fromkeys((*old.terms, *new.terms))),
                                       collections=tuple(dict.fromkeys((*old.collections, *new.collections)))))
    w = draft.warrant
    warrant = Warrant(
        source_observation_ids=tuple(dict.fromkeys((*into.warrant.source_observation_ids, *w.source_observation_ids))),
        source_episode_ids=tuple(dict.fromkeys((*into.warrant.source_episode_ids, *w.source_episode_ids))),
        templates=into.warrant.templates + w.templates,     # an upper bound: templates are not re-read
        falsifier=w.falsifier)
    return draft.model_copy(update={"latches": (hook, WiringLatch.build(converged_from=(into.id,))),
                                    "warrant": warrant, "route": Route.REFINE})


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    va, vb = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    den = float(np.linalg.norm(va) * np.linalg.norm(vb))
    return float(va @ vb) / den if den else 0.0


@dataclass
class DirectWriter:
    models: Models
    adjudicator: Adjudicator
    decisions: DecisionRepository
    observations: ObservationRepository | None = None   # naive's sources: spent once adjudicated
    representation: Representation | None = None
    merge: bool = True
    merge_cosine: float = 0.92
    concurrency: int = 4
    trace: Trace | None = None
    failures: list[tuple[str, str, str]] = field(default_factory=list)   # (stage, episode id, error)
    _sem: asyncio.Semaphore | None = field(default=None, init=False, repr=False)

    async def write(self, episode: Episode, observations: Sequence[Observation], *, round_: int,
                    at_idx: int | None = None) -> list[str]:
        """naive: one lesson per reducible open observation of the episode, admitted or merged."""
        todo = [o for o in observations if o.cls is ObservationClass.REDUCIBLE
                and o.disposition is ObservationDisposition.OPEN]
        lessons = await asyncio.gather(*(self._bounded(self.models.lesson(episode, o)) for o in todo),
                                       return_exceptions=True)
        out = []
        for o, lesson in zip(todo, lessons, strict=True):
            if isinstance(lesson, BaseException):   # loud and recorded; the observation stays open for a re-run
                self._failed("lesson", episode, lesson, observation_id=o.id)
                continue
            d = lesson_draft(lesson, run_id=episode.run_id, arm=episode.arm, round_=round_, episode=episode,
                             key=o.id, observation_ids=(o.id,))
            out.append(await self._admit(d, (o,), at_idx if at_idx is not None else episode.idx))
            if self.observations is not None:   # this path owns its sources: admitted, merged or refused
                await self.observations.dispose((o.id,), ObservationDisposition.SPENT, by=d.id)
        return out

    async def grade(self, episodes: Sequence[Episode], *, round_: int, at_idx: int) -> list[str]:
        """self_ref: every episode of the round is self-graded blind; a self-judged miss writes a lesson."""
        grades = await asyncio.gather(*(self._bounded(self.models.self_grade(e)) for e in episodes),
                                      return_exceptions=True)
        out = []
        for e, g in zip(episodes, grades, strict=True):
            if isinstance(g, BaseException):
                self._failed("self_grade", e, g)
                continue
            self._event("self_grade", {"episode_id": e.id, "arm": e.arm, "self_correct": g.correct,
                                       "lesson": g.lesson is not None})
            if g.correct or g.lesson is None:
                continue
            d = lesson_draft(g.lesson, run_id=e.run_id, arm=e.arm, round_=round_, episode=e, key=e.id,
                             observation_ids=())
            out.append(await self._admit(d, (), at_idx))
        return out

    async def _admit(self, draft: Draft, sources: Sequence[Observation], at_idx: int) -> str:
        target, score = await self._merge_target(draft) if self.merge else (None, None)
        if target is not None:
            draft = merged_draft(draft, target)
            self._event("direct.merge", {"draft_id": draft.id, "into": target.id, "cosine": score})
        ctx = CurationContext(run_id=draft.run_id, arm=draft.arm, at_idx=at_idx, sources=tuple(sources),
                              neighbours=((target, score),) if target is not None and score is not None else ())
        outcomes = await self.adjudicator.adjudicate(draft, ctx)
        return f"{draft.id}:{outcomes[-1].verdict.value if outcomes else 'none'}"

    async def _merge_target(self, draft: Draft) -> tuple[Decision | None, float | None]:
        if self.representation is None:
            return None, None
        vecs = await self.representation.embed([decision_text(draft)], "decision")
        if vecs is None or len(vecs) == 0:
            return None, None
        k = emb_key(self.representation.id)
        best: tuple[Decision | None, float | None] = (None, None)
        for d in await self.decisions.admitted(draft.run_id, draft.arm):
            if k in d.emb:
                c = cosine(vecs[0], d.emb[k])
                if best[1] is None or c > best[1]:
                    best = (d, c)
        if best[1] is None or best[1] < self.merge_cosine:
            return None, best[1]
        return best

    async def _bounded(self, coro: Any) -> Any:
        if self._sem is None:
            self._sem = asyncio.Semaphore(max(1, self.concurrency))
        async with self._sem:
            return await coro

    def _failed(self, stage: str, e: Episode, exc: BaseException, **extra: Any) -> None:
        self.failures.append((stage, e.id, f"{type(exc).__name__}: {exc}"))
        print(f"[direct] {stage} failed on {e.id}: {type(exc).__name__}: {exc}", file=sys.stderr)
        self._event(f"{stage}.failed", {"episode_id": e.id, "arm": e.arm, "error": f"{type(exc).__name__}: {exc}",
                                        **extra})

    def _event(self, name: str, payload: dict[str, Any]) -> None:
        if self.trace is not None:
            self.trace.event(name, payload)
