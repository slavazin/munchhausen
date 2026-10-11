"""The forward pass (SPEC § 6): one episode, end to end.

    question → consult → proposer → execute (through tool access) → judge
             → if miss ∧ authority: figure (+ phrasing) → proposer retry (unscored)
             → residuals per applied decision → revisit guards → write episode (+ fires)

Every collaborator is a port or an application service injected at construction (dependency inversion);
this class holds the sequence and nothing vendor- or dataset-specific.

Every state change is persisted and also emitted as a Trace event with its ids (`consultation_set`,
`view_resolved`, `guard_refusal`, `proposal_failed`, `episode_written`, `fire_raised`). Nothing on the
learning path reads Trace.

V-set episodes (`stream="v"`) are scored without the authority, never retried, never raise fires, and never
feed learning. Their `idx` is the negative ordinal `-(1 + k·V_SIZE + j)` (the episodes index is unique on
run, arm and idx); `at_idx` is the V point the world is evaluated at, carried in the episode id.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass

from munchhausen.agent.consultation import Consulter
from munchhausen.agent.execute import ExecutionError, execute
from munchhausen.agent.proposer import Proposer
from munchhausen.domain.arm import ArmSpec
from munchhausen.domain.common import Disposition, FireRole, Pipeline
from munchhausen.domain.decision import Decision
from munchhausen.domain.episode import Episode, Judgement, Proposal, confirmed_figure
from munchhausen.domain.fire import Fire, FireCause
from munchhausen.domain.ids import episode_id, fire_id
from munchhausen.domain.pipeline_guard import PipelineRefused
from munchhausen.domain.question import Question, SchemaSummary
from munchhausen.domain.scoring import matches
from munchhausen.loop.residuals import compute_residuals, guard_holds
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import Store
from munchhausen.ports.world import World

log = logging.getLogger(__name__)

STREAM, V = "stream", "v"


@dataclass(frozen=True)
class ForwardParams:
    max_time_ms: int
    rel_tol: float
    propose_attempts: int
    rounding_base: int
    fire_fetch_factor: int


@dataclass
class ForwardPass:
    run_id: str
    arm: ArmSpec
    world: World
    store: Store
    consulter: Consulter
    proposer: Proposer
    trace: Trace
    params: ForwardParams

    async def run(self, idx: int, question: Question, *, stream: str = STREAM, at_idx: int | None = None) -> Episode:
        t0 = time.monotonic()
        at = idx if at_idx is None else at_idx
        eid = episode_id(self.run_id, self.arm.name, at, stream=stream, question_id=question.id)
        authority = self.arm.authority and stream == STREAM
        ids = {"episode_id": eid, "arm": self.arm.name, "idx": idx, "stream": stream}
        self.trace.begin({**ids, "template": question.template})

        keys, consulted = await self.consulter.consult(self.run_id, self.arm.name, question)
        self.trace.event("consultation_set", {**ids, "terms": sorted(keys.terms),
                                              "decision_ids": [d.id for d in consulted]})
        view_map = await self.store.tool_access.view_map(self.run_id, self.arm.name)
        schema = self.world.schema_summary()

        answer, error = None, None
        proposed = await self._propose(question, schema, consulted, ids)
        if proposed is None:
            error, proposal = "proposer: no proposal", _empty_proposal(question)
        else:
            proposal = proposed
            answer, error = await self._execute(proposal, view_map, ids)

        judgement = await self.world.judge(question, answer, at, with_authority=authority)
        retry_pipeline, retry_correct = None, None
        if not judgement.correct and authority and judgement.figure is not None and proposed is not None:
            retry_pipeline, retry_correct = await self._retry(question, schema, consulted, view_map, judgement)

        residuals = ()
        if authority and not judgement.correct and judgement.figure is not None:
            phrasing_terms = await self.store.terms.extract(judgement.phrasing) if judgement.phrasing else frozenset()
            residuals = compute_residuals(eid, proposal.consulted, {d.id: d for d in consulted}, answer,
                                          judgement.figure, phrasing_terms, rounding_base=self.params.rounding_base)

        episode = Episode(
            _id=eid, run_id=self.run_id, arm=self.arm.name, idx=idx, question_id=question.id, text=question.text,
            template=question.template, persona=question.persona, terms=tuple(sorted(keys.terms)),
            world_version=self.world.world_version(at), consulted=proposal.consulted,
            collection=proposal.collection, pipeline=proposal.pipeline, answer_path=proposal.answer_path,
            view_map=view_map, answer=answer, anomalies=proposal.anomalies, confidence=proposal.confidence,
            rationale=proposal.rationale, correct=judgement.correct, figure=judgement.figure,
            phrasing=judgement.phrasing, confirmed_figure=confirmed_figure(answer, judgement)
            if authority else None, retry_pipeline=retry_pipeline, retry_correct=retry_correct,
            residuals=residuals, error=error, latency_ms=int((time.monotonic() - t0) * 1000), stream=stream,
            collections=question.collections,
        )
        await self.store.episodes.put(episode)
        self.trace.event("episode_written", {**ids, "correct": episode.correct, "error": error,
                                             "consulted": [c.decision_id for c in episode.consulted],
                                             "residual_ids": [r.id for r in residuals]})
        if stream == STREAM:
            await self._fires(episode, {d.id: d for d in consulted})
        self.trace.finish(answer)
        return episode

    async def _propose(self, question: Question, schema: SchemaSummary, consulted: Sequence[Decision],
                       ids: dict[str, object]) -> Proposal | None:
        """Up to `propose_attempts` calls; a proposer that never returns leaves an error episode (the index
        stays paired across arms) instead of a hole in the stream."""
        for attempt in range(1, self.params.propose_attempts + 1):
            try:
                return await self.proposer.propose(self.arm.name, question, schema, consulted)
            except Exception as e:   # model/API failures are data here: the episode records the error
                log.warning("proposer failed (%s, attempt %d): %s", ids["episode_id"], attempt, e)
                self.trace.event("proposal_failed", {**ids, "attempt": attempt, "error": f"{type(e).__name__}: {e}"})
        return None

    async def _execute(self, proposal: Proposal, view_map: dict[str, str],
                       ids: dict[str, object]) -> tuple[object, str | None]:
        target = view_map.get(proposal.collection, proposal.collection)
        self.trace.event("view_resolved", {**ids, "logical": proposal.collection, "resolved": target})
        try:
            ex = await execute(proposal, view_map, self.store.world(), max_time_ms=self.params.max_time_ms)
            return ex.answer, None
        except ExecutionError as e:
            if isinstance(e.__cause__, PipelineRefused):
                self.trace.event("guard_refusal", {**ids, "collection": target, "reason": str(e.__cause__)})
            return None, str(e)

    async def _retry(self, question: Question, schema: SchemaSummary, consulted: Sequence[Decision],
                     view_map: dict[str, str], judgement: Judgement) -> tuple[Pipeline | None, bool | None]:
        """Unscored retry; checked against the authority's figure, never against gold."""
        try:
            proposal = await self.proposer.retry(self.arm.name, question, schema, consulted,
                                                 judgement.figure, judgement.phrasing)
        except Exception as e:   # an unscored retry that fails leaves the retry fields empty
            log.warning("retry proposer failed (%s): %s", question.id, e)
            return None, None
        try:
            ex = await execute(proposal, view_map, self.store.world(), max_time_ms=self.params.max_time_ms)
        except ExecutionError:
            return proposal.pipeline, False
        return proposal.pipeline, matches(ex.answer, judgement.figure, rel_tol=self.params.rel_tol)

    async def _fires(self, episode: Episode, decisions: dict[str, Decision]) -> None:
        touched: set[str] = set()
        for r in episode.residuals:
            d = decisions[r.decision_id]
            open_latches = {f.latch for f in await self.store.fires.open_for(d.id) if f.role is FireRole.DISPOSITIVE}
            window = max((lt.guard.window for lt in d.revisits), default=0)
            recent = await self.store.episodes.consultations_of(self.run_id, self.arm.name, d.id,
                                                                window * self.params.fire_fetch_factor)
            for latch in d.revisits:
                if latch.id in open_latches:
                    continue
                holds, eids, rids = guard_holds(recent, d.id, latch.guard)
                if holds:
                    await self._fire(Fire(
                        _id=fire_id(d.id, latch.id, episode.idx), run_id=self.run_id, arm=self.arm.name,
                        decision_id=d.id, latch=latch.id, role=FireRole.DISPOSITIVE, cause=FireCause.RESIDUALS,
                        episode_ids=tuple(eids), residual_ids=tuple(rids), at_idx=episode.idx))
                    touched.add(d.id)
            if not r.attributable:
                await self._fire(Fire(
                    _id=fire_id(d.id, "unattributed", episode.idx), run_id=self.run_id, arm=self.arm.name,
                    decision_id=d.id, latch="residual", role=FireRole.CORROBORATING,
                    cause=FireCause.UNATTRIBUTED, episode_ids=(episode.id,), residual_ids=(r.id,),
                    at_idx=episode.idx))
        applied = [c.decision_id for c in episode.consulted if c.disposition is Disposition.APPLIED]
        for k, note in enumerate(episode.anomalies):
            for did in applied:
                await self._fire(Fire(
                    _id=fire_id(did, f"anomaly{k}", episode.idx), run_id=self.run_id, arm=self.arm.name,
                    decision_id=did, latch="anomaly", role=FireRole.CORROBORATING, cause=FireCause.ANOMALY,
                    episode_ids=(episode.id,), note=note, at_idx=episode.idx))
        for did in touched:
            await self.store.decisions.refresh_evidence_state(did)

    async def _fire(self, fire: Fire) -> None:
        await self.store.fires.put(fire)
        self.trace.event("fire_raised", {"fire_id": fire.id, "decision_id": fire.decision_id, "arm": fire.arm,
                                         "latch": fire.latch, "role": fire.role.value, "cause": fire.cause.value,
                                         "at_idx": fire.at_idx, "episode_ids": list(fire.episode_ids)})


def _empty_proposal(question: Question) -> Proposal:
    """The record of a proposer that returned nothing: no pipeline, no consultation, confidence 0."""
    return Proposal(collection=question.collections[0] if question.collections else "", pipeline=[],
                    answer_path="", confidence=0.0, rationale="")
