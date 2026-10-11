"""Nominator (SPEC § 7.2 step 4): generalizes one shape into the decision that settles it.

Before drafting, the nominator is shown the current store where it bears on the shape: the NEIGHBOUR_K
admitted decisions nearest the shape, with their recent residuals. A nominator that drafts blind
rediscovers what the store already holds. Those neighbours are handed on to L2 in the curation context,
so the nearest-neighbour read runs once per draft.

Runs the prior convention first through the read-only world tool and records it as a rejected option;
never writes a definition it has not run (`warrant.figures_reproduced` is computed from the tool's run log).

Reads only the shape's own episodes and observations (`NominatorInput` refuses anything else), so the
backtest population's confirmed figures stay unseen.

Supersede (minimum-configuration L2 exception, CARRY_FORWARD § 3a): a draft may declare `supersedes` only
against a neighbour whose evidence state is `contested` (an open dispositive fire). Anything else is routed
`new`, and the stripped declaration is traced.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from munchhausen.domain.common import EvidenceState, LifecycleStatus
from munchhausen.domain.decision import Decision, EntryContract
from munchhausen.domain.draft import Draft, Route, Shape
from munchhausen.domain.episode import Episode, Residual
from munchhausen.domain.ids import decision_id, draft_id, latch_id
from munchhausen.domain.latches import RetireLatch, RevisitLatch, WiringLatch
from munchhausen.domain.observation import Observation
from munchhausen.ports.models import Models, NominatorInput
from munchhausen.ports.representation import Representation, Similarity
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import DecisionRepository, DocumentReader, EpisodeRepository, TermRepository

DECISIONS_STORE = "decisions"   # the Similarity port's store name for the decision store


@dataclass(frozen=True)
class Nomination:
    draft: Draft
    neighbours: tuple[tuple[Decision, float], ...]


def shape_text(members: Sequence[Observation]) -> str:
    """The query a shape's neighbours are read with: its members' noticings."""
    return "\n".join(o.noticed for o in members)


def with_latch_ids(entry: EntryContract, did: str) -> EntryContract:
    """Party latch ids are placeholders until the draft id (hence the decision id) exists."""
    out, k = [], 0
    for lt in entry.latches:
        if isinstance(lt, (RevisitLatch, RetireLatch)):
            k += 1
            lt = lt.model_copy(update={"id": latch_id(did, k)})
        out.append(lt)
    return entry.model_copy(update={"latches": tuple(out)})


def without_supersede(entry: EntryContract) -> EntryContract:
    latches = tuple(WiringLatch.build() if isinstance(lt, WiringLatch) else lt for lt in entry.latches)
    return entry.model_copy(update={"latches": latches})


@dataclass
class Nominator:
    models: Models
    world: DocumentReader
    episodes: EpisodeRepository
    terms: TermRepository
    decisions: DecisionRepository
    representation: Representation
    similarity: Similarity
    neighbour_k: int
    residual_window: int
    trace: Trace | None = None
    stripped: list[str] = field(default_factory=list)   # draft ids whose undeclarable supersede was stripped

    async def neighbours(self, run_id: str, arm: str, shape: Shape,
                         members: Sequence[Observation]) -> list[tuple[Decision, float]]:
        """`neighbour_k` admitted decisions nearest the shape. With no representation, the admitted decisions
        whose hook shares a term or collection with the shape stand in (score = shared-key share)."""
        vec = await self.representation.embed([shape_text(members)], "query")
        if vec is not None and len(vec):
            hits = await self.similarity.knn(DECISIONS_STORE, vec[0].tolist(), self.neighbour_k,
                                             {"run_id": run_id, "arm": arm,
                                              "lifecycle.status": LifecycleStatus.ADMITTED.value})
            found = [(await self.decisions.get(i), s) for i, s in hits]
            return [(d, s) for d, s in found if d is not None and d.is_admitted]
        keys = set(shape.terms) | {o.surfaces.collection for o in members if o.surfaces.collection}
        scored = []
        for d in await self.decisions.admitted(run_id, arm):
            fw = d.hook.fires_when
            hook_keys = set(fw.terms) | set(fw.collections)
            shared = keys & hook_keys
            if shared:
                scored.append((d, len(shared) / len(keys | hook_keys)))
        scored.sort(key=lambda p: (-p[1], p[0].id))
        return scored[: self.neighbour_k]

    async def residuals(self, run_id: str, arm: str, decision: Decision) -> tuple[list[Residual], list[str]]:
        """A neighbour's recent residuals, and the episodes they come from (the nominator has seen those)."""
        eps = await self.episodes.consultations_of(run_id, arm, decision.id, self.residual_window)
        rows = [(r, e.id) for e in eps for r in e.residuals if r.decision_id == decision.id]
        return [r for r, _ in rows], sorted({eid for _, eid in rows})

    async def nominate(self, run_id: str, arm: str, round_: int, shape: Shape, members: Sequence[Observation],
                       neighbours: Sequence[tuple[Decision, float]] | None = None) -> Nomination:
        episodes: list[Episode] = [e for e in [await self.episodes.get(i) for i in shape.episode_ids] if e]
        if neighbours is None:
            neighbours = await self.neighbours(run_id, arm, shape, members)
        residuals: dict[str, tuple[Residual, ...]] = {}
        seen: set[str] = set(shape.episode_ids)
        for d, _ in neighbours:
            rs, eids = await self.residuals(run_id, arm, d)
            residuals[d.id] = tuple(rs)
            seen.update(eids)
        inp = NominatorInput(
            shape=shape, sources=tuple(members), episodes=tuple(episodes),
            vocabulary=tuple(t.term for t in await self.terms.all(run_id=run_id)), world=self.world,
            neighbours=tuple(d for d, _ in neighbours), neighbour_residuals=residuals)
        try:
            entry, new_terms = await self.models.nominate(inp)
        finally:
            for row in inp.run_log:   # every world-tool run, accepted or not
                self._event("nominator.run", {"arm": arm, "round": round_, "shape_id": shape.id, **row})

        did_ = draft_id(run_id, arm, round_, shape.id)
        entry = with_latch_ids(entry, decision_id(did_))
        supersedes = entry.wiring.supersedes
        contested = {d.id for d, _ in neighbours if d.evidence_state is EvidenceState.CONTESTED}
        if supersedes is not None and supersedes not in contested:
            self.stripped.append(did_)
            self._event("draft.supersede_stripped", {"draft_id": did_, "declared": supersedes,
                                                     "contested": sorted(contested)})
            entry, supersedes = without_supersede(entry), None
        draft = Draft(
            _id=did_, run_id=run_id, arm=arm, **{f: getattr(entry, f) for f in EntryContract.model_fields},
            shape_id=shape.id, source_observation_ids=shape.observation_ids, new_terms=tuple(new_terms),
            route=Route.SUPERSEDE if supersedes else Route.NEW, supersedes=supersedes, round=round_,
            nominator_seen_episode_ids=tuple(sorted(seen)))
        return Nomination(draft=draft, neighbours=tuple(neighbours))

    def _event(self, name: str, payload: dict[str, object]) -> None:
        if self.trace is not None:
            self.trace.event(name, payload)
