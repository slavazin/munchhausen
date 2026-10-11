"""Injection (SPEC § 1 live beat, § 17 pane 4): an operator feeds the agent a false authority figure and
watches the backtest refuse the draft that results.

    fresh questions on the chosen templates
      → governed forward passes over `InjectedWorld` (its `judge` returns the operator's figure and phrasing)
      → observations (via=injection)
      → the injection shape → coherence guard → the bar's observation/template minimum
      → nominate → Adjudicator (L0–L4 always run) → the backtest record

The direction read (E4) is skipped for an injection shape: every matched episode was scored against the
operator's figure, so a miss-rate gap would read the injection, not the world. The draft records the skip
under `adjudication["bar"]`. The backtest still replays the case store's stream episodes against their
confirmed figures, which is where a false figure is refused.

Injection episodes are written with `stream="injection"` and the next free `idx` at or below
INJECT_IDX_BASE (stream indices are ≥ 0, V indices are -(1 + k·V_SIZE + j), and `episodes` is unique on
run/arm/idx), so no stream reading, curve or backtest population counts them. Each forward pass runs at the
arm's current stream index (`at_idx`), so `world_version` is right after a drift. Their `correct` is scored
against the operator's figure and means nothing else.

Containment: the draft carries `source="injection"`; every exit (hold, refuse, admit, failure) marks the
injection's observations `spent`, disposed by the job; the organic episodic pass never opens `via=injection`
observations (`open_for_pass` excludes them); the proposer's spend is recorded under INJECT_STAGE (rounds
exclude it). Residue: the observer, nominator and backtest replays record spend under their own stages.

Application layer: ports and application services only (no store, impl or world imports).
"""

from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Awaitable, Callable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from munchhausen.domain.backtest import Backtest
from munchhausen.domain.common import Answer, LayerRole
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Draft, LayerOutcome, Shape, Verdict
from munchhausen.domain.episode import Episode, Judgement
from munchhausen.domain.ids import backtest_id, observation_id
from munchhausen.domain.observation import (
    Observation,
    ObservationClass,
    ObservationDisposition,
    ObservationNote,
    Surfaces,
    Via,
)
from munchhausen.domain.question import Question, SchemaSummary
from munchhausen.domain.scoring import matches, ratio_delta
from munchhausen.learn.episodic import Bar, coherence_guard, shape_of
from munchhausen.ports.curation import Adjudicator, CurationContext
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import (
    BacktestRepository,
    CursorRepository,
    DraftRepository,
    EpisodeRepository,
    ObservationRepository,
)
from munchhausen.ports.world import World

INJECTION_STREAM = "injection"
DIRECTION_SKIPPED = {"direction_read": "skipped",
                     "why": "injection shape: every matched episode was scored against the operator's figure"}


class ForwardRunner(Protocol):
    async def run(self, idx: int, question: Question, *, stream: str = "stream",
                  at_idx: int | None = None) -> Episode: ...


class NominationLike(Protocol):
    """`learn/nominate.Nomination`: the draft and the neighbours it was drafted against (handed to L2)."""

    draft: Draft
    neighbours: tuple[tuple[Decision, float], ...]


class ShapeNominator(Protocol):
    async def nominate(self, run_id: str, arm: str, round_: int, shape: Shape,
                       members: Sequence[Observation]) -> NominationLike: ...


Observe = Callable[[Episode], Awaitable[list[ObservationNote]]]
Step = Callable[[str, dict[str, Any]], Any]


@dataclass(frozen=True)
class InjectionRequest:
    run_id: str
    arm: str
    templates: tuple[str, ...]
    figure: Answer
    phrasing: str
    per_template: int
    job_id: str = ""                    # disposer of the injection's observations on every exit


@dataclass(frozen=True)
class InjectParams:
    seed: int
    scan_max: int
    rel_tol: float
    idx_base: int = -1_000_000          # INJECT_IDX_BASE
    max_templates: int = 3              # INJECT_MAX_TEMPLATES


class InjectedWorld:
    """A `World` whose authority says what the operator says. Everything else delegates to the real world."""

    def __init__(self, base: World, figure: Answer, phrasing: str, rel_tol: float) -> None:
        self._base, self._figure, self._phrasing, self._rel_tol = base, figure, phrasing, rel_tol
        self.id = f"{base.id}+injection"

    async def build(self, seed: int) -> dict[str, int]:
        raise RuntimeError("an injected world never builds the world database")

    def schema_summary(self) -> SchemaSummary:
        return self._base.schema_summary()

    def questions(self, seed: int) -> Iterator[Question]:
        return self._base.questions(seed)

    def v_set(self) -> Sequence[Question]:
        return self._base.v_set()

    def world_version(self, idx: int) -> str:
        return self._base.world_version(idx)

    async def judge(self, question: Question, answer: Answer, idx: int, *, with_authority: bool) -> Judgement:
        correct = matches(answer, self._figure, rel_tol=self._rel_tol)
        if correct or not with_authority:
            return Judgement(correct=correct)
        return Judgement(correct=False, figure=self._figure, phrasing=self._phrasing)


@dataclass
class InjectionResult:
    request: InjectionRequest
    questions: list[Question] = field(default_factory=list)
    episodes: list[Episode] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    shape: Shape | None = None
    bar_cleared: bool = False
    draft: Draft | None = None
    outcomes: list[LayerOutcome] = field(default_factory=list)
    backtest: Backtest | None = None
    stopped: str | None = None          # why the beat ended before the backtest, if it did

    def summary(self) -> dict[str, Any]:
        return {
            "templates": list(self.request.templates), "figure": self.request.figure,
            "phrasing": self.request.phrasing,
            "episodes": [{"id": e.id, "template": e.template, "answer": e.answer, "correct": e.correct}
                         for e in self.episodes],
            "observations": [o.id for o in self.observations],
            "shape": None if self.shape is None else self.shape.id, "bar_cleared": self.bar_cleared,
            "draft": None if self.draft is None else self.draft.id,
            "outcomes": [o.model_dump(mode="json") for o in self.outcomes],
            "backtest": None if self.backtest is None else {
                "id": self.backtest.id, "verdict": self.backtest.verdict.value, "fixed": self.backtest.fixed,
                "fixed_heldout": self.backtest.fixed_heldout, "broken": self.backtest.broken,
                "n": len(self.backtest.sampled)},
            "stopped": self.stopped,
        }


@runtime_checkable
class InstanceSource(Protocol):
    """A world that poses rebuildable instances of one template (S1 `PackWorld.instances`: ids
    `t-<template>-<seed>-<k>`, which any process can rebuild, so a later backtest replay finds them)."""

    def instances(self, template_id: str, seed: int, n: int) -> tuple[Question, ...]: ...


def pick_questions(world: World, templates: Sequence[str], per_template: int, *, seed: int,
                   scan_max: int) -> list[Question]:
    """Fresh question instances on the chosen templates, from a seed the stream never uses."""
    if isinstance(world, InstanceSource):
        out = [q for t in templates for q in world.instances(t, seed, per_template)]
        missing = sorted(set(templates) - {q.template for q in out})
        if missing:
            raise ValueError(f"no question instances found for templates {missing}")
        return out
    want = {t: per_template for t in templates}
    out: list[Question] = []
    for k, q in enumerate(world.questions(seed)):
        if k >= scan_max or not any(want.values()):
            break
        if want.get(q.template, 0) > 0:
            out.append(q)
            want[q.template] -= 1
    missing = sorted(t for t, n in want.items() if n > 0)
    if missing:
        raise ValueError(f"no question instances found for templates {missing} within {scan_max} questions")
    return out


def injection_observation(episode: Episode, note: ObservationNote | None, k: int, round_: int,
                          figure: Answer, phrasing: str) -> Observation:
    """Wrap one noticing (the observer's, or a mechanical one when the observer offers none) as
    `via=injection`. The authority surface is the operator's phrasing, verbatim."""
    ratio, delta = ratio_delta(episode.answer, figure)
    if note is None:
        note = ObservationNote(
            cls=ObservationClass.REDUCIBLE,
            noticed=(f"The answer {episode.answer!r} differs from the authority's figure {figure!r}; "
                     f"the authority names: {phrasing}"),
            surfaces=Surfaces(terms=episode.terms, collection=episode.collection, phrasing=phrasing))
    surfaces = note.surfaces.model_copy(update={"phrasing": phrasing,
                                                "terms": note.surfaces.terms or episode.terms,
                                                "collection": note.surfaces.collection or episode.collection})
    return Observation(
        _id=observation_id(episode.id, k), run_id=episode.run_id, arm=episode.arm, episode_id=episode.id,
        via=Via.INJECTION, cls=note.cls, noticed=note.noticed, surfaces=surfaces,
        template=episode.template, persona=episode.persona, answer=episode.answer, figure=figure,
        ratio=ratio, delta=delta, pipeline=episode.pipeline, retry_pipeline=episode.retry_pipeline,
        retry_correct=episode.retry_correct, signature_guess=note.signature_guess,
        re_check_when=note.re_check_when, round=round_)


def injection_shape(observations: Sequence[Observation]) -> Shape:
    """The shape the episodic pass would build from these observations, marked as an injection's."""
    return shape_of(observations).model_copy(update={"source": INJECTION_STREAM})


SKIP_OUTCOME = LayerOutcome(layer="bar", role=None, verdict=Verdict.PASS, detail=DIRECTION_SKIPPED)


def mark_injection(draft: Draft) -> Draft:
    """`source="injection"` and the direction-read skip, recorded on the draft before adjudication."""
    return draft.model_copy(update={"adjudication": {**draft.adjudication, "bar": SKIP_OUTCOME},
                                    "source": INJECTION_STREAM})


def capped_templates(templates: Sequence[str], cap: int) -> tuple[str, ...]:
    """Distinct templates in the operator's order, at most `cap` (each costs forward passes and replays)."""
    out = tuple(dict.fromkeys(t for t in templates if t))
    if not out:
        raise ValueError("choose at least one template")
    if len(out) > cap:
        raise ValueError(f"at most {cap} templates per injection (INJECT_MAX_TEMPLATES); got {len(out)}")
    return out


class InjectionModels:
    """The Models port with the proposer's spend recorded under the injection stage (`ProposerInput.stage`).
    Every other method delegates unchanged."""

    def __init__(self, base: Any, stage: str) -> None:
        self._base, self._stage = base, stage

    async def propose(self, inp: Any) -> Any:
        return await self._base.propose(dataclasses.replace(inp, stage=self._stage))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._base, name)


@dataclass
class Injector:
    world: World
    forward_for: Callable[[World], ForwardRunner]   # a governed forward pass over the given world
    nominator: ShapeNominator
    adjudicator: Adjudicator
    observations: ObservationRepository
    drafts: DraftRepository
    backtests: BacktestRepository
    cursors: CursorRepository
    episodes: EpisodeRepository                     # only to find a free injection index
    bar: Bar
    params: InjectParams
    observe: Observe | None = None                  # the observer party; None: mechanical noticing only
    trace: Trace | None = None

    async def _free_idx(self, req: InjectionRequest) -> int:
        idx = self.params.idx_base
        while await self.episodes.exists(req.run_id, req.arm, idx):
            idx -= 1
        return idx

    def _event(self, name: str, payload: dict[str, Any]) -> None:
        if self.trace is not None:
            self.trace.event(name, payload)

    async def run(self, req: InjectionRequest, on_step: Step | None = None) -> InjectionResult:
        req = dataclasses.replace(req, templates=capped_templates(req.templates, self.params.max_templates))
        res = InjectionResult(request=req)
        self._event("injection.started", {"job": req.job_id, "run_id": req.run_id, "arm": req.arm,
                                          "templates": list(req.templates), "per_template": req.per_template})
        try:
            return await self._run(req, res, on_step)
        finally:
            # containment on every exit: injected evidence is spent, by this job, whatever the verdict
            ids = [o.id for o in res.observations]
            if ids:
                await self.observations.dispose(ids, ObservationDisposition.SPENT, by=f"injection:{req.job_id}")
            self._event("injection.finished", {"job": req.job_id, "arm": req.arm,
                                               "draft_id": res.draft.id if res.draft else None,
                                               "verdict": res.backtest.verdict.value if res.backtest else None,
                                               "stopped": res.stopped, "observations": ids})

    async def _run(self, req: InjectionRequest, res: InjectionResult, on_step: Step | None) -> InjectionResult:
        async def step(name: str, **payload: Any) -> None:
            if on_step is not None:
                r = on_step(name, payload)
                if inspect.isawaitable(r):
                    await r

        cursor = await self.cursors.get(req.run_id, req.arm)
        at_idx, round_ = (0, 0) if cursor is None else (cursor.next_idx, cursor.round)
        res.questions = pick_questions(self.world, req.templates, req.per_template,
                                       seed=self.params.seed, scan_max=self.params.scan_max)
        await step("questions", questions=[{"id": q.id, "template": q.template, "text": q.text}
                                           for q in res.questions], at_idx=at_idx)

        forward = self.forward_for(InjectedWorld(self.world, req.figure, req.phrasing, self.params.rel_tol))
        for q in res.questions:
            ep = await forward.run(await self._free_idx(req), q, stream=INJECTION_STREAM, at_idx=at_idx)
            res.episodes.append(ep)
            await step("episode", id=ep.id, template=ep.template, answer=ep.answer, correct=ep.correct)

        for ep in res.episodes:
            if ep.correct:      # the answer already equals the operator's figure: nothing to notice
                continue
            notes: list[ObservationNote | None] = []
            if self.observe is not None:
                try:
                    notes = [n for n in await self.observe(ep) if n.cls is ObservationClass.REDUCIBLE]
                except Exception as e:  # noqa: BLE001 - the beat goes on with a mechanical noticing, recorded
                    await step("observer-fallback", episode=ep.id, error=type(e).__name__)
            notes = notes or [None]
            for k, note in enumerate(notes):
                obs = injection_observation(ep, note, k, round_, req.figure, req.phrasing)
                await self.observations.put(obs)
                res.observations.append(obs)
        await step("observations", ids=[o.id for o in res.observations])
        if not res.observations:
            res.stopped = "no observation: every answer matched the operator's figure"
            await step("done", **res.summary())
            return res

        shapes = coherence_guard(injection_shape(res.observations), res.observations)
        if not shapes:
            res.stopped = "the coherence guard split the observations into nothing"
            await step("done", **res.summary())
            return res
        res.shape = max(shapes, key=lambda x: len(x.observation_ids)).model_copy(update={"source": INJECTION_STREAM})
        members = [o for o in res.observations if o.id in set(res.shape.observation_ids)]
        res.bar_cleared = self.bar.clears(res.shape, members)
        await step("shape", id=res.shape.id, templates=sorted(res.shape.templates), terms=sorted(res.shape.terms),
                   observations=len(members), bar_cleared=res.bar_cleared, **DIRECTION_SKIPPED)
        if not res.bar_cleared:
            res.stopped = (f"held at the bar: {len(members)} observations over {len(res.shape.templates)} "
                           f"templates; the bar needs {self.bar.min_obs} over {self.bar.min_templates}")
            await step("done", **res.summary())
            return res

        nom = await self.nominator.nominate(req.run_id, req.arm, round_, res.shape, members)
        draft = mark_injection(nom.draft)
        await self.drafts.put(draft)
        await self.observations.dispose(res.shape.observation_ids, ObservationDisposition.SHAPED, by=draft.id)
        res.draft = draft
        await step("draft", id=draft.id, title=draft.title, kind=draft.kind.value, route=draft.route.value,
                   neighbours=[d.id for d, _ in nom.neighbours])

        ctx = CurationContext(run_id=req.run_id, arm=req.arm, at_idx=at_idx, sources=tuple(members),
                              neighbours=tuple(nom.neighbours))
        res.outcomes = list(await self.adjudicator.adjudicate(draft, ctx))
        await self.drafts.record(draft.id, SKIP_OUTCOME)   # the adjudicator rewrites `adjudication`
        await step("adjudicated", outcomes=[o.model_dump(mode="json") for o in res.outcomes])
        res.backtest = await self.backtests.get(backtest_id(draft.id))
        if res.backtest is None:
            last = res.outcomes[-1] if res.outcomes else None
            reached = any(o.role is LayerRole.DISPOSITIVE for o in res.outcomes)
            res.stopped = (None if reached else
                           f"stopped at {last.layer if last else 'L0'} ({last.verdict.value if last else 'none'}) "
                           f"before the backtest")
        await step("done", **res.summary())
        return res
