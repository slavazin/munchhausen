"""In-memory fakes for the adjudication tests: a store that mirrors the Atlas repositories' semantics
(including the admission transaction of `store/decisions.py`), a scripted proposer and a scripted world.

The scripted proposer "applies" a consulted decision by a token in its payload: `RULE` answers each question's
right figure, `POISON` answers one fixed figure, anything else leaves the prior answer. That is the premise of
SPEC § 12 made mechanical, so the tests read the backtest's arithmetic, not a model."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

from munchhausen.domain.admission import Admission
from munchhausen.domain.backtest import Backtest
from munchhausen.domain.common import (
    DecisionKind,
    Disposer,
    Disposition,
    FireDisposition,
    FireRole,
    LifecycleStatus,
    Signature,
)
from munchhausen.domain.decision import Amendment, Decision, LifecycleError, Option, Warrant, evidence_state
from munchhausen.domain.draft import Draft, DraftStatus, LayerOutcome
from munchhausen.domain.episode import EVALUATION_ONLY_FIELDS, Consultation, Episode, Proposal
from munchhausen.domain.fire import Fire, FireCause
from munchhausen.domain.latches import FloorLatch, Guard, HookLatch, KeySet, RevisitLatch
from munchhausen.domain.observation import Observation, ObservationDisposition, Surfaces, Via
from munchhausen.domain.question import Question, QuestionKeys, SchemaSummary
from munchhausen.domain.registers import Term, ToolAccess
from munchhausen.ports.models import ProposerInput, SelfGrade

RUN, ARM = "wt-s4-test", "governed"
TERM = "active customers"
RIGHT_BASE, PRIOR_OFFSET, POISON_FIGURE = 1000.0, 37.0, 4242.0


def _matches_filter(doc: dict[str, Any], f: dict[str, Any]) -> bool:  # noqa: C901 - a tiny $match evaluator
    for k, cond in f.items():
        if k == "$or":
            if not any(_matches_filter(doc, c) for c in cond):
                return False
            continue
        if k == "$nor":
            if any(_matches_filter(doc, c) for c in cond):
                return False
            continue
        v = doc.get(k)
        if isinstance(cond, dict) and any(op.startswith("$") for op in cond):
            for op, arg in cond.items():
                vals = v if isinstance(v, (list, tuple)) else [v]
                if op == "$in" and not set(vals) & set(arg):
                    return False
                if op == "$nin" and set(vals) & set(arg):
                    return False
                if op == "$all" and not set(arg) <= set(vals):
                    return False
                if op == "$ne" and v == arg:
                    return False
                if op == "$gt" and not (v is not None and v > arg):
                    return False
                if op == "$gte" and not (v is not None and v >= arg):
                    return False
                if op == "$lte" and not (v is not None and v <= arg):
                    return False
        elif v != cond:
            return False
    return True


class State:
    def __init__(self) -> None:
        self.episodes: dict[str, Episode] = {}
        self.decisions: dict[str, Decision] = {}
        self.fires: dict[str, Fire] = {}
        self.drafts: dict[str, Draft] = {}
        self.backtests: dict[str, Backtest] = {}
        self.tool_access: list[ToolAccess] = []
        self.observations: dict[str, Observation] = {}
        self.views: dict[str, tuple[str, list[dict[str, Any]]]] = {}
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.terms = [Term(term=TERM, source="schema", admitted_at_idx=0)]


class FakeEpisodes:
    def __init__(self, st: State) -> None:
        self.st = st

    async def put(self, e: Episode) -> None:
        self.st.episodes[e.id] = e

    async def get(self, i: str) -> Episode | None:
        return self.st.episodes.get(i)

    async def for_learner(self, run_id: str, arm: str, *, with_authority: bool,
                          filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        out = []
        for e in self.st.episodes.values():
            doc = e.model_dump(by_alias=True)
            if e.run_id == run_id and e.arm == arm and _matches_filter(doc, filter or {}):
                out.append(doc if with_authority else {k: v for k, v in doc.items() if k not in EVALUATION_ONLY_FIELDS})
        return out

    async def backtest_sample(self, run_id: str, arm: str, match: dict[str, Any], *, n: int,
                              seed: int | None, prefer_terms: Sequence[str] = ()) -> list[Episode]:
        from munchhausen.store.repositories import balance

        rows = [e for e in self.st.episodes.values() if e.run_id == run_id and e.arm == arm
                and _matches_filter(e.model_dump(by_alias=True), match)]
        rows.sort(key=lambda e: hashlib.sha256(f"{seed}:{e.id}".encode()).hexdigest())
        misses = sorted((e for e in rows if not e.correct), key=lambda e: not set(e.terms) & set(prefer_terms))
        return balance([e for e in rows if e.correct], misses, n)

    async def consultations_of(self, run_id: str, arm: str, decision_id: str, last_n: int) -> list[Episode]:
        rows = sorted((e for e in self.st.episodes.values()
                       if any(c.decision_id == decision_id for c in e.consulted)), key=lambda e: -e.idx)
        return rows[:last_n]


class FakeDecisions:
    def __init__(self, st: State) -> None:
        self.st = st

    async def get(self, i: str) -> Decision | None:
        return self.st.decisions.get(i)

    async def admitted(self, run_id: str, arm: str) -> list[Decision]:
        return [d for d in self.st.decisions.values() if d.run_id == run_id and d.arm == arm and d.is_admitted]

    async def match_hooks(self, run_id: str, arm: str, keys: QuestionKeys) -> list[Decision]:
        return [d for d in await self.admitted(run_id, arm) if d.hook.matches(keys)]

    async def admit(self, plan: Admission) -> None:
        d = plan.decision
        if d.id in self.st.decisions:
            return
        for f in plan.flips:
            p = self.st.decisions.get(f.decision_id)
            if p is None or not p.is_admitted:
                raise LifecycleError(f"predecessor {f.decision_id} is not admitted")
        self.st.decisions[d.id] = d
        flipped = []
        for f in plan.flips:
            self.st.decisions[f.decision_id] = self.st.decisions[f.decision_id].model_copy(
                update={"lifecycle": f.lifecycle})
            flipped.append(f.decision_id)
        for fid, fire in list(self.st.fires.items()):
            if fire.decision_id in flipped and fire.disposition is FireDisposition.OPEN:
                self.st.fires[fid] = fire.model_copy(update={"disposition": FireDisposition.APPLIED,
                                                             "disposer": Disposer.LIFECYCLE})
        self.st.tool_access = [t for t in self.st.tool_access if t.decision_id not in plan.restore_views_of]
        if plan.rewire:
            r = plan.rewire
            self.st.tool_access = [t for t in self.st.tool_access
                                   if not (t.run_id == r.run_id and t.arm == r.arm and t.logical == r.logical)] + [r]
        if plan.draft_id in self.st.drafts:
            self.st.drafts[plan.draft_id] = self.st.drafts[plan.draft_id].model_copy(
                update={"status": DraftStatus.ADMITTED})

    async def supersede(self, plan: Admission) -> None:
        if not any(f.lifecycle.status is LifecycleStatus.SUPERSEDED for f in plan.flips):
            raise LifecycleError("a supersede plan must flip its predecessor to superseded")
        await self.admit(plan)

    async def converge(self, plan: Admission) -> None:
        if not any(f.lifecycle.status is LifecycleStatus.CONVERGED for f in plan.flips):
            raise LifecycleError("a converge plan must flip at least one decision to converged")
        await self.admit(plan)

    async def amend(self, decision_id: str, amendment: Amendment) -> None:
        d = self.st.decisions[decision_id]
        self.st.decisions[decision_id] = d.model_copy(update={"amendments": (*d.amendments, amendment)})

    async def moot(self, decision_id: str, at_idx: int, reason: str) -> None:
        await self._terminal(decision_id, lambda lc: lc.moot(at_idx, reason))

    async def retire(self, decision_id: str, at_idx: int, reason: str) -> None:
        await self._terminal(decision_id, lambda lc: lc.retire(at_idx, reason))

    async def _terminal(self, decision_id: str, t: Any) -> None:
        d = self.st.decisions[decision_id]
        self.st.decisions[decision_id] = d.model_copy(update={"lifecycle": t(d.lifecycle)})
        self.st.tool_access = [x for x in self.st.tool_access if x.decision_id != decision_id]

    async def refresh_evidence_state(self, decision_id: str) -> None:
        roles = [(f.role, f.disposition) for f in self.st.fires.values()
                 if f.decision_id == decision_id and f.disposition is FireDisposition.OPEN]
        d = self.st.decisions[decision_id]
        self.st.decisions[decision_id] = d.model_copy(update={"evidence_state": evidence_state(roles)})


class FakeFires:
    def __init__(self, st: State) -> None:
        self.st = st

    async def put(self, f: Fire) -> None:
        self.st.fires[f.id] = f

    async def get(self, i: str) -> Fire | None:
        return self.st.fires.get(i)

    async def open_for(self, decision_id: str) -> list[Fire]:
        return [f for f in self.st.fires.values()
                if f.decision_id == decision_id and f.disposition is FireDisposition.OPEN]

    async def for_decision(self, decision_id: str) -> list[Fire]:
        return sorted((f for f in self.st.fires.values() if f.decision_id == decision_id), key=lambda f: f.at_idx)

    async def dispose(self, ids: Sequence[str], disposition: FireDisposition, disposer: Disposer) -> None:
        for i in ids:
            self.st.fires[i] = self.st.fires[i].model_copy(update={"disposition": disposition, "disposer": disposer})


class FakeDrafts:
    def __init__(self, st: State) -> None:
        self.st = st

    async def put(self, d: Draft) -> None:
        self.st.drafts[d.id] = d

    async def get(self, i: str) -> Draft | None:
        return self.st.drafts.get(i)

    async def record(self, draft_id: str, outcome: LayerOutcome) -> None:
        d = self.st.drafts[draft_id]
        self.st.drafts[draft_id] = d.model_copy(update={"adjudication": {**d.adjudication, outcome.layer: outcome}})

    async def held(self, run_id: str, arm: str) -> list[Draft]:
        return [d for d in self.st.drafts.values() if d.status is DraftStatus.HELD]


class FakeBacktests:
    def __init__(self, st: State) -> None:
        self.st = st

    async def put(self, b: Backtest) -> None:
        self.st.backtests[b.id] = b

    async def get(self, i: str) -> Backtest | None:
        return self.st.backtests.get(i)

    async def for_arm(self, run_id: str, arm: str) -> list[Backtest]:
        return [b for b in self.st.backtests.values() if b.run_id == run_id and b.arm == arm]


class FakeToolAccess:
    def __init__(self, st: State) -> None:
        self.st = st

    async def view_map(self, run_id: str, arm: str) -> dict[str, str]:
        return {t.logical: t.view for t in self.st.tool_access if t.run_id == run_id and t.arm == arm}

    async def rewires(self, run_id: str, arm: str) -> list[ToolAccess]:
        return [t for t in self.st.tool_access if t.run_id == run_id and t.arm == arm]


class FakeObservations:
    def __init__(self, st: State) -> None:
        self.st = st

    async def put(self, o: Observation) -> None:
        self.st.observations[o.id] = o

    async def get(self, i: str) -> Observation | None:
        return self.st.observations.get(i)

    async def open_for_pass(self, run_id: str, arm: str, *, since_round: int) -> list[Observation]:
        return [o for o in self.st.observations.values() if o.disposition is ObservationDisposition.OPEN]

    async def dispose(self, ids: Sequence[str], disposition: ObservationDisposition, by: str) -> None:
        for i in ids:
            if i in self.st.observations:
                self.st.observations[i] = self.st.observations[i].model_copy(
                    update={"disposition": disposition, "disposed_by": by})


class FakeTerms:
    def __init__(self, st: State) -> None:
        self.st = st

    async def all(self) -> list[Term]:
        return list(self.st.terms)


class FakeWorld:
    """`world` as the replay sees it. A pipeline is `[{$project: {q, v}}]`; a floor (`$match` on
    `rs`, inline or through a view) returns the question's right figure."""

    def __init__(self, st: State, right: dict[str, float]) -> None:
        self.st, self.right = st, right

    async def aggregate(self, collection: str, pipeline: list[dict[str, Any]], *, max_time_ms: int) -> list[dict]:
        floored = collection in self.st.views or any("rs" in s.get("$match", {}) for s in pipeline)
        proj = next(s["$project"] for s in pipeline if "$project" in s)
        return [{"v": self.right[proj["q"]] if floored else proj["v"]}]

    async def find(self, *a: Any, **k: Any) -> list[dict]:
        return []

    async def collection_names(self) -> list[str]:
        return sorted(self.st.views)

    async def create_view(self, name: str, source: str, pipeline: list[dict[str, Any]]) -> None:
        self.st.views[name] = (source, pipeline)
        self.st.events.append(("create_view", {"name": name}))

    async def drop_view(self, name: str) -> None:
        self.st.views.pop(name, None)
        self.st.events.append(("drop_view", {"name": name}))

    async def replace_collection(self, collection: str, docs: Sequence[dict]) -> int:
        return 0


class FakeModels:
    """The scripted proposer: applies a consulted decision by the token in its payload."""

    def __init__(self, right: dict[str, float], prior: dict[str, float]) -> None:
        self.right, self.prior, self.calls = right, prior, []

    async def propose(self, inp: ProposerInput) -> Proposal:
        q = inp.question.id
        answer, consulted = self.prior[q], []
        for d in inp.consulted:
            applied = "RULE" in d.payload or "POISON" in d.payload or d.floor is not None
            if "RULE" in d.payload:
                answer = self.right[q]
            elif "POISON" in d.payload:
                answer = POISON_FIGURE
            consulted.append(Consultation(decision_id=d.id, disposition=Disposition.APPLIED if applied
                                          else Disposition.CONSIDERED_NOT_APPLICABLE))
        self.calls.append((inp.stage, q, tuple(d.id for d in inp.consulted)))
        return Proposal(collection="transactions", pipeline=[{"$project": {"q": q, "v": answer}}], answer_path="0.v",
                        consulted=tuple(consulted), confidence=0.5, rationale="r")

    async def self_grade(self, episode: Episode) -> SelfGrade:
        from munchhausen.domain.lesson import Lesson

        return SelfGrade(correct=False, lesson=Lesson(title="Active customers hold a status",
                                                      kind=DecisionKind.TAXONOMIC, payload="Count by RULE status."))

    async def lesson(self, episode: Episode, observation: Observation) -> Any:
        from munchhausen.domain.lesson import Lesson

        return Lesson(title="Active customers hold a status", kind=DecisionKind.TAXONOMIC,
                      payload="Count customers by RULE status field.")


class HookConsulter:
    """The arm's consultation: hook match over admitted decisions (no rerank, no budget)."""

    def __init__(self, decisions: FakeDecisions) -> None:
        self.decisions = decisions

    async def consult(self, run_id: str, arm: str, question: Question) -> tuple[QuestionKeys, list[Decision]]:
        keys = QuestionKeys(terms=frozenset({TERM} if TERM in question.text else set()),
                            collections=frozenset(question.collections), persona=question.persona)
        return keys, await self.decisions.match_hooks(run_id, arm, keys)


class Store:
    def __init__(self) -> None:
        self.st = State()
        self.episodes = FakeEpisodes(self.st)
        self.decisions = FakeDecisions(self.st)
        self.fires = FakeFires(self.st)
        self.drafts = FakeDrafts(self.st)
        self.backtests = FakeBacktests(self.st)
        self.tool_access = FakeToolAccess(self.st)
        self.observations = FakeObservations(self.st)
        self.terms = FakeTerms(self.st)


class Trace:
    def __init__(self, st: State) -> None:
        self.st = st

    def begin(self, episode: dict[str, Any]) -> None: ...

    def signal(self, name: str, value: Any, comment: str | None = None) -> None: ...

    def event(self, name: str, payload: dict[str, Any]) -> None:
        self.st.events.append((name, payload))

    def finish(self, output: Any) -> None: ...


class Sink:
    def __init__(self) -> None:
        self.published: list[str] = []
        self.withdrawn: list[tuple[str, str]] = []

    async def publish(self, decision: Decision) -> None:
        self.published.append(decision.id)

    async def withdraw(self, decision_id: str, reason: str) -> None:
        self.withdrawn.append((decision_id, reason))


SCHEMA = SchemaSummary(collections={"customers": {"st": "int"}})


# --- record builders ---------------------------------------------------------------------------------


def episode(idx: int, template: str, *, correct: bool, figure: float, persona: str = "omar",
            question_id: str | None = None, terms: tuple[str, ...] = (TERM,), arm: str = ARM) -> Episode:
    return Episode(_id=f"{RUN}:{arm}:e{idx}", run_id=RUN, arm=arm, idx=idx, question_id=question_id or f"q{idx}",
                   text=f"How many {TERM} in {template} for period {idx}?", template=template, persona=persona,
                   terms=terms,
                   world_version="v0", consulted=(), collection="customers", pipeline=[], answer_path="0.v",
                   view_map={}, answer=figure if correct else figure + PRIOR_OFFSET, confidence=0.5, correct=correct,
                   figure=None if correct else figure, phrasing=None, confirmed_figure=figure,
                   collections=("customers",))


def observation(e: Episode, k: int = 0) -> Observation:
    return Observation(_id=f"{e.id}:o{k}", run_id=e.run_id, arm=e.arm, episode_id=e.id, via=Via.OBSERVER,
                       cls="reducible", noticed="The count exceeds the figure.", surfaces=Surfaces(terms=(TERM,)),
                       template=e.template, persona=e.persona, answer=e.answer, figure=e.figure, round=0)


def draft(did: str, payload: str, sources: Sequence[Episode], *, kind: DecisionKind = DecisionKind.TAXONOMIC,
          supersedes: str | None = None, floor: FloorLatch | None = None, arm: str = ARM,
          new_terms: tuple[str, ...] = ()) -> Draft:
    from munchhausen.domain.draft import Route

    latches: list[Any] = [HookLatch(fires_when=KeySet(terms=(TERM,))),
                          RevisitLatch(id=f"T-{did}-1", signature=Signature.EXCLUSION,
                                       guard=Guard(min_residuals=2, window=30))]
    if floor is not None:
        latches.append(floor)
    return Draft(
        _id=did, run_id=RUN, arm=arm, title="Active customers hold one status set", kind=kind, payload=payload,
        options=(Option(definition="all rows", verdict="rejected", prior=True),
                 Option(definition=payload, verdict="chosen")),
        forecloses="counts over every status", latches=tuple(latches), residue="lookups bypass the view",
        warrant=Warrant(source_observation_ids=tuple(f"{e.id}:o0" for e in sources),
                        source_episode_ids=tuple(e.id for e in sources),
                        templates=len({e.template for e in sources}), falsifier="residuals agree in direction"),
        shape_id="S-1", source_observation_ids=tuple(f"{e.id}:o0" for e in sources), round=1,
        route=Route.SUPERSEDE if supersedes else Route.NEW, supersedes=supersedes, new_terms=new_terms)


def fire(decision_id: str, at_idx: int, *, role: FireRole = FireRole.DISPOSITIVE, k: int = 0) -> Fire:
    return Fire(_id=f"F-{decision_id}-{at_idx}-{k}", run_id=RUN, arm=ARM, decision_id=decision_id,
                latch=f"T-{decision_id}-1", role=role, cause=FireCause.RESIDUALS, episode_ids=(), at_idx=at_idx)
