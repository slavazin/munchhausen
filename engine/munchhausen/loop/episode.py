"""The forward pass (SPEC § 6): one episode, end to end.

    question → consult → proposer → execute (through tool access) → judge
             → if miss ∧ authority: figure (+ phrasing) → proposer retry (unscored)
             → residuals per applied decision → revisit guards → write episode (+ fires)

Every collaborator is a port or an application service injected at construction (dependency inversion);
this class holds the sequence and nothing vendor- or dataset-specific.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass

from munchhausen.agent.consultation import Consulter
from munchhausen.agent.execute import ExecutionError, execute
from munchhausen.agent.proposer import Proposer
from munchhausen.domain.arm import ArmSpec
from munchhausen.domain.common import Disposition, FireRole, Pipeline
from munchhausen.domain.decision import Decision
from munchhausen.domain.episode import Episode, Judgement, confirmed_figure
from munchhausen.domain.fire import Fire, FireCause
from munchhausen.domain.ids import episode_id, fire_id
from munchhausen.domain.question import Question, SchemaSummary
from munchhausen.domain.scoring import matches
from munchhausen.loop.residuals import compute_residuals, guard_holds
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import Store
from munchhausen.ports.world import World


@dataclass(frozen=True)
class ForwardParams:
    max_time_ms: int
    rel_tol: float


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

    async def run(self, idx: int, question: Question, *, stream: str = "stream") -> Episode:
        t0 = time.monotonic()
        eid = episode_id(self.run_id, self.arm.name, idx, stream=stream, question_id=question.id)
        self.trace.begin({"arm": self.arm.name, "idx": idx, "template": question.template})

        keys, consulted = await self.consulter.consult(self.run_id, self.arm.name, question)
        view_map = await self.store.tool_access.view_map(self.run_id, self.arm.name)
        schema = self.world.schema_summary()
        proposal = await self.proposer.propose(self.arm.name, question, schema, consulted)

        answer, error = None, None
        try:
            answer = (await execute(proposal, view_map, self.store.world(), max_time_ms=self.params.max_time_ms)).answer
        except ExecutionError as e:
            error = str(e)

        judgement = await self.world.judge(question, answer, idx, with_authority=self.arm.authority)
        retry_pipeline, retry_correct = None, None
        if not judgement.correct and self.arm.authority and judgement.figure is not None:
            retry_pipeline, retry_correct = await self._retry(question, schema, consulted, view_map, judgement)

        residuals = ()
        if not judgement.correct and judgement.figure is not None:
            phrasing_terms = await self.store.terms.extract(judgement.phrasing) if judgement.phrasing else frozenset()
            residuals = compute_residuals(eid, proposal.consulted, {d.id: d for d in consulted},
                                          answer, judgement.figure, phrasing_terms)

        episode = Episode(
            _id=eid, run_id=self.run_id, arm=self.arm.name, idx=idx, question_id=question.id, text=question.text,
            template=question.template, persona=question.persona, terms=tuple(sorted(keys.terms)),
            world_version=self.world.world_version(idx), consulted=proposal.consulted,
            collection=proposal.collection, pipeline=proposal.pipeline, answer_path=proposal.answer_path,
            view_map=view_map, answer=answer, anomalies=proposal.anomalies, confidence=proposal.confidence,
            rationale=proposal.rationale, correct=judgement.correct, figure=judgement.figure,
            phrasing=judgement.phrasing, confirmed_figure=confirmed_figure(answer, judgement)
            if self.arm.authority else None, retry_pipeline=retry_pipeline, retry_correct=retry_correct,
            residuals=residuals, error=error, latency_ms=int((time.monotonic() - t0) * 1000), stream=stream,
            collections=question.collections,
        )
        await self.store.episodes.put(episode)
        if stream == "stream":
            await self._fires(episode, {d.id: d for d in consulted})
        self.trace.finish(answer)
        return episode

    async def _retry(self, question: Question, schema: SchemaSummary, consulted: Sequence[Decision],
                     view_map: dict[str, str], judgement: Judgement) -> tuple[Pipeline, bool]:
        """Unscored retry; checked against the authority's figure, never against gold."""
        proposal = await self.proposer.retry(self.arm.name, question, schema, consulted,
                                             judgement.figure, judgement.phrasing)
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
            recent = await self.store.episodes.consultations_of(self.run_id, self.arm.name, d.id, max(
                (lt.guard.window for lt in d.revisits), default=0))
            for latch in d.revisits:
                if latch.id in open_latches:
                    continue
                holds, eids, rids = guard_holds(recent, d.id, latch.guard)
                if holds:
                    await self.store.fires.put(Fire(
                        _id=fire_id(d.id, latch.id, episode.idx), run_id=self.run_id, arm=self.arm.name,
                        decision_id=d.id, latch=latch.id, role=FireRole.DISPOSITIVE, cause=FireCause.RESIDUALS,
                        episode_ids=tuple(eids), residual_ids=tuple(rids), at_idx=episode.idx))
                    touched.add(d.id)
            if not r.attributable:
                await self.store.fires.put(Fire(
                    _id=fire_id(d.id, "unattributed", episode.idx), run_id=self.run_id, arm=self.arm.name,
                    decision_id=d.id, latch="residual", role=FireRole.CORROBORATING,
                    cause=FireCause.UNATTRIBUTED, episode_ids=(episode.id,), residual_ids=(r.id,),
                    at_idx=episode.idx))
        for k, note in enumerate(episode.anomalies):
            applied = [c.decision_id for c in episode.consulted if c.disposition is Disposition.APPLIED]
            for did in applied:
                await self.store.fires.put(Fire(
                    _id=fire_id(did, f"anomaly{k}", episode.idx), run_id=self.run_id, arm=self.arm.name,
                    decision_id=did, latch="anomaly", role=FireRole.CORROBORATING, cause=FireCause.ANOMALY,
                    episode_ids=(episode.id,), note=note, at_idx=episode.idx))
        for did in touched:
            await self.store.decisions.refresh_evidence_state(did)
