"""The stand-in adjudicator (M3b): the paired backtest refuses a poisoned or case-leaking draft and admits a
generalizing one; supersede reads only the shifted world; floors become views; decisions stay frozen at
admission; `ungated` admits at L0 what `governed` refuses at L4; the owner port; the direct write paths."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from munchhausen.agent.proposer import Proposer
from munchhausen.domain.backtest import BacktestThresholds
from munchhausen.domain.common import DecisionKind, FireDisposition, FireRole, LifecycleStatus
from munchhausen.domain.draft import DraftStatus, Route, Verdict
from munchhausen.domain.ids import decision_id
from munchhausen.domain.latches import FloorLatch
from munchhausen.learn.adjudicate import Adjudicator
from munchhausen.learn.backtest import Backtester, applied_premise, population_filter
from munchhausen.learn.curators import governed, hitl, ungated
from munchhausen.learn.direct import DirectWriter, blind
from munchhausen.learn.layers import L0Shape, L1Bar, L2Neighbours, L3Lenses, L4Backtest
from munchhausen.learn.lifecycle import LifecycleService
from munchhausen.ports.curation import CurationContext
from munchhausen.store.repositories import balance
from tests.test_adjudication_fakes import (
    ARM,
    POISON_FIGURE,
    RUN,
    SCHEMA,
    TERM,
    FakeModels,
    FakeWorld,
    HookConsulter,
    Sink,
    Store,
    Trace,
    draft,
    episode,
    fire,
    observation,
)


def run(coro):  # noqa: ANN001, ANN201
    return asyncio.run(coro)


class _NoPanel:
    id = "none"

    async def score(self, draft, sources, neighbours):  # noqa: ANN001, ANN201
        return {}


class _Weights:
    async def current_weights(self):  # noqa: ANN201
        from munchhausen.domain.lens import LensWeights

        return LensWeights(version=0, weights={})


class World:
    """A store of episodes over four templates: sources on t1/t2, held out t3/t4. Misses are quirk-bearing
    (the prior answer is off), hits are not (prior = right)."""

    def __init__(self, *, n_per_template: int = 4) -> None:
        self.store = Store()
        self.right: dict[str, float] = {}
        self.prior: dict[str, float] = {}
        idx = 0
        for t in ("t1", "t2", "t3", "t4"):
            for k in range(n_per_template):
                correct = k % 2 == 1
                e = episode(idx, t, correct=correct, figure=1000.0 + idx)
                self.add(e)
                idx += 1
        self.sources = [self.store.st.episodes[f"{RUN}:{ARM}:e{i}"] for i in (0, n_per_template)]   # misses on t1, t2
        for e in self.sources:
            self.store.st.observations[f"{e.id}:o0"] = observation(e)
        self.models = FakeModels(self.right, self.prior)
        self.world = FakeWorld(self.store.st, self.right)
        self.trace = Trace(self.store.st)
        self.sink = Sink()

    def add(self, e: Any) -> None:
        self.store.st.episodes[e.id] = e
        self.right[e.question_id] = e.confirmed_figure
        self.prior[e.question_id] = e.answer

    def backtester(self, n: int = 8) -> Backtester:
        s = self.store
        return Backtester(episodes=s.episodes, fires=s.fires, consulter=HookConsulter(s.decisions),
                          proposer=Proposer(self.models), world=self.world,
                          thresholds=BacktestThresholds(min_fixed=2, min_fixed_heldout=1, max_broken=1), n=n,
                          rel_tol=1e-4, max_time_ms=1000, backtests=s.backtests, tool_access=s.tool_access,
                          schema=lambda: SCHEMA, seed=17, concurrency=4, trace=self.trace)

    def lifecycle(self) -> LifecycleService:
        s = self.store
        return LifecycleService(decisions=s.decisions, world=self.world, sink=self.sink, tool_access=s.tool_access,
                                fires=s.fires, episodes=s.episodes, trace=self.trace, retire_idle=300, retire_fires=6)

    def curator(self, name: str = "governed") -> Any:
        s = self.store
        l0 = L0Shape(s.terms)
        if name == "ungated":
            return ungated(l0)
        layers = (l0, L1Bar(min_templates=2, min_templates_floor=2),
                  L2Neighbours(threshold=0.85, decisions=s.decisions, fires=s.fires),
                  L3Lenses(panel=_NoPanel(), weights=_Weights(), mode="record", threshold=0.5, explore_eps=0.0,
                           seed=7),
                  L4Backtest(self.backtester()))
        return hitl(*layers) if name == "hitl" else governed(*layers)

    def adjudicator(self, name: str = "governed") -> Adjudicator:
        s = self.store
        return Adjudicator(curator=self.curator(name), drafts=s.drafts, decisions=s.decisions, fires=s.fires,
                           lifecycle=self.lifecycle(), view_name=lambda c, d: f"{c}__{d}", trace=self.trace)

    def ctx(self, at_idx: int = 100) -> CurationContext:
        return CurationContext(run_id=RUN, arm=ARM, at_idx=at_idx,
                               sources=tuple(self.store.st.observations[f"{e.id}:o0"] for e in self.sources))


# --- the dispositive check -----------------------------------------------------------------------------


def test_generalizing_draft_is_admitted_with_a_heldout_fix() -> None:
    w = World()
    d = draft("d-gen", "Active customers hold the RULE status set.", w.sources)
    out = run(w.backtester().run(d, w.ctx()))
    bt = out.backtest
    assert bt.verdict.value == "admit" and bt.fixed >= 2 and bt.fixed_heldout >= 1 and bt.broken == 0
    sampled = {s.episode_id for s in bt.sampled}
    assert not sampled & {e.id for e in w.sources}, "sources never enter the population"
    assert len(bt.sampled) == 8 and sum(not s.original_correct for s in bt.sampled) == 4, "balanced"
    assert w.store.st.backtests[bt.id] == bt
    assert out.calls == 16 and out.applied == 8
    replays = [st for st, *_ in w.models.calls if st == "replay"]
    assert len(replays) == 16
    ev = [p for n, p in w.store.st.events if n == "backtest"]
    assert ev and ev[0]["fixed"] == bt.fixed and len(ev[0]["replays"]) == 8


def test_poisoned_draft_is_refused_zero_fixed_two_broken() -> None:
    """A draft encoding one episode's figure: it reproduces only that episode (a source, excluded, and its
    repeat, excluded by question) and breaks every hit it touches."""
    w = World()
    src = w.sources[0]
    repeat = episode(99, "t3", correct=False, figure=POISON_FIGURE, question_id=src.question_id)
    w.add(repeat)
    w.right[src.question_id] = POISON_FIGURE
    d = draft("d-poison", "Active customers follow the POISON count.", w.sources)
    bt = run(w.backtester().run(d, w.ctx())).backtest
    assert bt.verdict.value == "refuse"
    assert bt.fixed == 0 and bt.broken >= 2
    assert repeat.id not in {s.episode_id for s in bt.sampled}, "a source's repeated question is excluded"


def test_case_leak_without_heldout_fix_is_refused() -> None:
    """Fixes only on the source templates: fixed ≥ 2 but fixed_heldout = 0."""
    w = World()
    for e in list(w.store.st.episodes.values()):
        if e.template in ("t3", "t4") and not e.correct:
            w.prior[e.question_id] = e.confirmed_figure + 1.0
            w.right[e.question_id] = e.confirmed_figure + 1.0   # the draft's "right" misses the held-out figure
    d = draft("d-leak", "Active customers hold the RULE status set.", w.sources)
    bt = run(w.backtester().run(d, w.ctx())).backtest
    assert bt.fixed >= 2 and bt.fixed_heldout == 0 and bt.verdict.value == "refuse"


def test_population_filter_is_the_hook_definition() -> None:
    from munchhausen.domain.latches import HookLatch, KeySet, NotThisRow

    hook = HookLatch(fires_when=KeySet(terms=(TERM,), persona="dana"),
                     not_this=(NotThisRow(terms=("churn",), contrast="active customers by churn month"),))
    f = population_filter(hook, exclude_ids=["e1"], exclude_questions=["q1"], after_idx=10)
    assert f["persona"] == "dana" and f["$nor"] == [{"terms": {"$all": ["churn"]}}] and f["idx"] == {"$gt": 10}
    assert f["confirmed_figure"] == {"$ne": None} and f["stream"] == "stream"
    assert population_filter(HookLatch(fires_when=KeySet()), exclude_ids=[], exclude_questions=[],
                             after_idx=None) == {"_id": {"$in": []}}


def test_balanced_sample_tops_up_a_short_stratum() -> None:
    assert balance([1, 2, 3, 4, 5], [9], 4) == [1, 2, 3, 9]
    assert balance([1], [7, 8, 9, 10], 4) == [1, 7, 8, 9]
    assert balance([1, 2], [7, 8], 8) == [1, 2, 7, 8]


def test_applied_premise_reads_misses_fixed() -> None:
    w = World()
    run(w.backtester().run(draft("d-gen", "Active customers hold the RULE status set.", w.sources), w.ctx()))
    p = applied_premise(run(w.store.backtests.for_arm(RUN, ARM)))
    assert p["misses_sampled"] == 4 and p["misses_fixed"] == 4 and p["rate"] == 1.0


# --- supersession -----------------------------------------------------------------------------------------


def _admit_predecessor(w: World, payload: str = "Active customers hold the PRIOR status set.") -> str:
    adj = w.adjudicator("ungated")
    d = draft("d-pred", payload, w.sources)
    w.store.st.drafts[d.id] = d
    out = run(adj.adjudicate(d, w.ctx(at_idx=20)))
    assert out[-1].verdict is Verdict.ADMIT
    return decision_id("d-pred")


def test_supersede_population_starts_at_the_fire_and_drops_the_predecessor() -> None:
    w = World(n_per_template=8)
    pred = _admit_predecessor(w)
    f = fire(pred, 12)
    w.store.st.fires[f.id] = f
    run(w.store.decisions.refresh_evidence_state(pred))
    d = draft("d-succ", "Active customers hold the RULE status set.", w.sources, supersedes=pred)
    out = run(w.adjudicator().adjudicate(d, w.ctx(at_idx=40)))
    assert out[-1].verdict is Verdict.ADMIT, [o.detail for o in out]
    bt = next(iter(w.store.st.backtests.values()))
    assert all(int(s.episode_id.rsplit("e", 1)[1]) >= 12 for s in bt.sampled)
    assert all(pred not in s.context for s in bt.sampled)
    assert all(pred not in ids for st, _, ids in w.models.calls if st == "replay")
    succ = decision_id("d-succ")
    p = w.store.st.decisions[pred]
    assert p.lifecycle.status is LifecycleStatus.SUPERSEDED and p.lifecycle.superseded_by == succ
    assert w.store.st.fires[f.id].disposition is FireDisposition.APPLIED
    assert p.evidence_state.value == "clear"
    assert w.store.st.decisions[succ].wiring.supersedes == pred
    assert (pred, "superseded") in w.sink.withdrawn


def test_l2_refuses_a_supersede_against_a_clear_neighbour() -> None:
    w = World()
    pred = _admit_predecessor(w)
    d = draft("d-succ", "Active customers hold the RULE status set.", w.sources, supersedes=pred)
    out = run(w.adjudicator().adjudicate(d, w.ctx()))
    assert out[-1].layer == "L2" and out[-1].verdict is Verdict.REFUSE
    assert w.store.st.drafts["d-succ"].status is DraftStatus.REFUSED
    assert not w.store.st.backtests, "no replay is spent on a refused route"


def test_l2_route_contested_knob_routes_a_new_draft_as_supersede() -> None:
    w = World()
    pred = _admit_predecessor(w)
    f = fire(pred, 5)
    w.store.st.fires[f.id] = f
    layer = L2Neighbours(threshold=0.85, decisions=w.store.decisions, fires=w.store.fires, route_contested=True)
    d = draft("d-new", "Active customers hold the RULE status set.", w.sources)
    ctx = CurationContext(RUN, ARM, 40, (), neighbours=((w.store.st.decisions[pred], 0.9),))
    out = run(layer.check(d, ctx))
    assert (out.verdict, out.route, out.neighbour_id) == (Verdict.PASS, Route.SUPERSEDE, pred)
    off = L2Neighbours(threshold=0.85, decisions=w.store.decisions, fires=w.store.fires)
    assert run(off.check(d, ctx)).route is Route.NEW


# --- floors -------------------------------------------------------------------------------------------------


def test_floor_admission_creates_view_and_rewires_then_supersede_drops_and_restores() -> None:
    w = World()
    floor = FloorLatch(collection="customers", match={"deleted_at": None})
    d1 = draft("d-floor", "Customers exclude rows with deleted_at set.", w.sources, kind=DecisionKind.FLOOR,
               floor=floor)
    assert run(w.adjudicator().adjudicate(d1, w.ctx()))[-1].verdict is Verdict.ADMIT
    f1 = decision_id("d-floor")
    view = f"customers__{f1}"
    assert view in w.store.st.views and w.store.st.views[view][1] == [{"$match": {"deleted_at": None}}]
    assert run(w.store.tool_access.view_map(RUN, ARM)) == {"customers": view}
    # the predecessor is contested; a non-floor successor supersedes it: the view drops, the mapping restores
    f = fire(f1, 1)
    w.store.st.fires[f.id] = f
    d2 = draft("d-succ", "Active customers hold the RULE status set.", w.sources, supersedes=f1)
    assert run(w.adjudicator().adjudicate(d2, w.ctx(at_idx=120)))[-1].verdict is Verdict.ADMIT
    assert view not in w.store.st.views
    assert run(w.store.tool_access.view_map(RUN, ARM)) == {}
    names = [n for n, _ in w.store.st.events]
    assert names.index("view.create") < names.index("admission") and "view.drop" in names


def test_retire_drops_a_floor_view_and_sweep_moots_idle_decisions() -> None:
    w = World()
    floor = FloorLatch(collection="customers", match={"deleted_at": None})
    d1 = draft("d-floor", "Customers exclude rows with deleted_at set.", w.sources, kind=DecisionKind.FLOOR,
               floor=floor)
    run(w.adjudicator().adjudicate(d1, w.ctx(at_idx=10)))
    f1 = decision_id("d-floor")
    for k in range(6):
        f = fire(f1, 20 + k, role=FireRole.DISPOSITIVE if k == 0 else FireRole.CORROBORATING, k=k)
        w.store.st.fires[f.id] = f
    out = run(w.lifecycle().sweep(RUN, ARM, 50))
    assert out["retired"] == [f1]
    assert w.store.st.decisions[f1].lifecycle.status is LifecycleStatus.RETIRED
    assert not w.store.st.views and run(w.store.tool_access.view_map(RUN, ARM)) == {}
    assert all(f.disposition is not FireDisposition.OPEN for f in w.store.st.fires.values())
    pred = _admit_predecessor(w)
    out = run(w.lifecycle().sweep(RUN, ARM, 20 + 300))
    assert out["moot"] == [pred] and w.store.st.decisions[pred].lifecycle.status is LifecycleStatus.MOOT


# --- frozen at admission ------------------------------------------------------------------------------------


def test_frozen_at_admission_only_lifecycle_evidence_and_amendments_change() -> None:
    w = World(n_per_template=8)
    pred = _admit_predecessor(w)
    before = w.store.st.decisions[pred].model_dump()
    f = fire(pred, 12)
    w.store.st.fires[f.id] = f
    run(w.store.decisions.refresh_evidence_state(pred))
    d = draft("d-succ", "Active customers hold the RULE status set.", w.sources, supersedes=pred)
    run(w.adjudicator().adjudicate(d, w.ctx(at_idx=40)))
    after = w.store.st.decisions[pred].model_dump()
    changed = {k for k in before if before[k] != after[k]}
    assert changed <= {"lifecycle", "evidence_state", "amendments"} and "lifecycle" in changed


# --- the gate's ablation, hitl and the owner -----------------------------------------------------------------


def test_ungated_admits_at_l0_what_governed_refuses_at_l4() -> None:
    poison = "Active customers follow the POISON count."
    g, u = World(), World()
    out_g = run(g.adjudicator("governed").adjudicate(draft("d-p", poison, g.sources), g.ctx()))
    out_u = run(u.adjudicator("ungated").adjudicate(draft("d-p", poison, u.sources), u.ctx()))
    assert [o.layer for o in out_g] == ["L0", "L1", "L2", "L3", "L4"] and out_g[-1].verdict is Verdict.REFUSE
    assert out_g[-1].detail["fixed"] == 0 and out_g[-1].detail["broken"] >= 2 and out_g[-1].detail["label"] == 0
    assert [o.layer for o in out_u] == ["L0", "admit"] and out_u[-1].verdict is Verdict.ADMIT
    assert decision_id("d-p") in u.store.st.decisions and decision_id("d-p") not in g.store.st.decisions
    assert g.store.st.drafts["d-p"].status is DraftStatus.REFUSED
    assert set(g.store.st.drafts["d-p"].adjudication) == {"L0", "L1", "L2", "L3", "L4"}


def test_hitl_holds_an_l4_admit_for_the_owner_who_admits_it() -> None:
    w = World()
    adj = w.adjudicator("hitl")
    d = draft("d-gen", "Active customers hold the RULE status set.", w.sources)
    out = run(adj.adjudicate(d, w.ctx()))
    assert out[-1].verdict is Verdict.HOLD and out[-1].detail["awaiting"] == "owner"
    assert out[-1].detail["backtest_id"]
    assert w.store.st.drafts["d-gen"].status is DraftStatus.HELD
    rec = run(adj.owner_dispose_draft("d-gen", Verdict.ADMIT, 130, note="demo"))
    assert rec.adjudication["L5"].detail["disposer"] == "owner"
    dec = w.store.st.decisions[decision_id("d-gen")]
    assert dec.is_admitted and dec.warrant.backtest_id == out[-1].detail["backtest_id"]
    assert w.store.st.drafts["d-gen"].status is DraftStatus.ADMITTED


def test_owner_disposes_a_fire() -> None:
    w = World()
    pred = _admit_predecessor(w)
    f = fire(pred, 12)
    w.store.st.fires[f.id] = f
    run(w.store.decisions.refresh_evidence_state(pred))
    run(w.adjudicator().owner_dispose_fire(f.id, FireDisposition.REJECTED, "false alarm"))
    assert w.store.st.fires[f.id].disposer.value == "owner"
    assert w.store.st.decisions[pred].evidence_state.value == "clear"


def test_l0_accepts_hook_terms_through_the_escape() -> None:
    w = World()
    w.store.st.terms = []
    d = draft("d-esc", "Active customers hold the RULE status set.", w.sources,
              new_terms=(f"other({TERM}): how a question names customers in use",))
    assert run(L0Shape(w.store.terms).check(d, w.ctx())).verdict is Verdict.PASS
    bare = draft("d-bare", "Active customers hold the RULE status set.", w.sources)
    assert run(L0Shape(w.store.terms).check(bare, w.ctx())).verdict is Verdict.REFUSE


def test_adjudicator_never_disposes_observations() -> None:
    w = World()
    run(w.adjudicator().adjudicate(draft("d-gen", "Active customers hold the RULE status set.", w.sources),
                                   w.ctx()))
    assert all(o.disposition.value == "open" for o in w.store.st.observations.values())


# --- the direct write paths ----------------------------------------------------------------------------------


class _Rep:
    id, dim = "fake-emb", 2

    async def embed(self, texts, role):  # noqa: ANN001, ANN201
        import numpy as np

        return np.asarray([[1.0, 0.0] for _ in texts])


def _naive(w: World) -> DirectWriter:
    from munchhausen.learn.curators import naive
    from munchhausen.learn.layers import LessonShape

    s = w.store
    adj = Adjudicator(curator=naive(LessonShape()), drafts=s.drafts, decisions=s.decisions, fires=s.fires,
                      lifecycle=w.lifecycle(), view_name=lambda c, d: f"{c}__{d}", representation=_Rep(),
                      trace=w.trace)
    return DirectWriter(models=w.models, adjudicator=adj, decisions=s.decisions, observations=s.observations,
                        representation=_Rep(), merge=True, merge_cosine=0.92, trace=w.trace)


def test_naive_admits_a_lesson_then_merges_the_next_as_a_converged_successor() -> None:
    w = World()
    writer = _naive(w)
    e0, e1 = w.sources
    o0, o1 = w.store.st.observations[f"{e0.id}:o0"], w.store.st.observations[f"{e1.id}:o0"]
    run(writer.write(e0, [o0], round_=1, at_idx=30))
    first = [d for d in w.store.st.decisions.values() if d.is_admitted]
    assert len(first) == 1 and first[0].warrant.backtest_id is None
    run(writer.write(e1, [o1], round_=1, at_idx=30))
    admitted = [d for d in w.store.st.decisions.values() if d.is_admitted]
    assert len(admitted) == 1 and admitted[0].id != first[0].id
    old = w.store.st.decisions[first[0].id]
    assert old.lifecycle.status is LifecycleStatus.CONVERGED and old.lifecycle.converged_into == admitted[0].id
    assert set(admitted[0].warrant.source_episode_ids) == {e0.id, e1.id}
    assert all(o.disposition.value == "spent" for o in w.store.st.observations.values())


def test_self_grade_reads_blind() -> None:
    w = World()
    docs = run(w.store.episodes.for_learner(RUN, ARM, with_authority=False))
    blinded = [blind(d) for d in docs]
    assert all(e.figure is None and e.confirmed_figure is None for e in blinded)
    with pytest.raises(ValueError, match="evaluation-only"):
        blind(run(w.store.episodes.for_learner(RUN, ARM, with_authority=True))[0])
    from munchhausen.impl.parties.self_grade import render

    text = render(blinded[0])
    assert "confirmed" not in text and "correct" not in text and "figure" not in text


def test_self_ref_writes_lessons_from_self_judged_misses() -> None:
    w = World()
    writer = _naive(w)
    docs = run(w.store.episodes.for_learner(RUN, ARM, with_authority=False, filter={"idx": {"$lte": 1}}))
    out = run(writer.grade([blind(d) for d in docs], round_=0, at_idx=1))
    assert len(out) == 2 and len([d for d in w.store.st.decisions.values() if d.is_admitted]) == 1


def test_a_failed_lesson_call_is_loud_recorded_and_leaves_the_observation_open() -> None:
    w = World()
    writer = _naive(w)

    async def boom(episode, observation):  # noqa: ANN001, ANN202
        raise RuntimeError("429 rate limited")

    w.models.lesson = boom
    e0 = w.sources[0]
    run(writer.write(e0, [w.store.st.observations[f"{e0.id}:o0"]], round_=1, at_idx=30))
    assert writer.failures and writer.failures[0][0] == "lesson"
    assert any(n == "lesson.failed" for n, _ in w.store.st.events)
    assert w.store.st.observations[f"{e0.id}:o0"].disposition.value == "open" and not w.store.st.decisions


def test_jev_panel_asks_each_lens_in_isolation_reads_only_its_pointer_and_logs_hedging(settings_offline) -> None:  # noqa: ANN001
    from types import SimpleNamespace

    from munchhausen.impl.lens_panel import JevLensPanel

    calls: list[tuple[dict, dict]] = []

    class Client:
        async def system_one(self, state, questions):  # noqa: ANN001, ANN202
            calls.append((state, questions))
            ((name, q),) = questions.items()
            if q["type"] == "choice":
                return SimpleNamespace(answers={name: SimpleNamespace(probabilities={"floor": 0.2})})
            p = 0.9 if "beyond" in str(q["instructions"]).lower() else 0.3
            return SimpleNamespace(answers={name: SimpleNamespace(noul=p)})

    w = World()
    panel = JevLensPanel(settings_offline.lenses(), "k", phrasings=3, client=Client())
    d = draft("d-gen", "Active customers hold the RULE status set.", w.sources)
    out = run(panel.score(d, [w.store.st.observations[f"{e.id}:o0"] for e in w.sources], []))
    assert len(calls) == 5 * 3 and all(len(q) == 1 for _, q in calls)
    leak_states = [s for s, q in calls if "case_leak" in q]
    assert all(set(s) == {"draft", "sources"} and set(s["draft"]) == {"payload"} for s in leak_states)
    assert {"generalizes", "case_leak", "mechanizable", "hedge:generalizes"} <= set(out)
    assert 0.0 <= out["hedge:case_leak"] <= 1.0
    assert run(JevLensPanel(settings_offline.lenses(), None).score(d, [], [])) == {}
