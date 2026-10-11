"""The S4 adversarial review's fixes: a backtest that cannot read holds (B1); only dispositive fires retire
(B2); the nominator's episodes stay out of the population (B3); fixes need the draft applied and a net gain
(M1); twin questions are excluded (M2); misses meeting the hook's terms come first (M3); the floor gate at L0
and the floor-view-only drop (M4); `admitted_at_idx` (M6); a second floor on one collection; admission errors
are recorded, not raised."""

from __future__ import annotations

import asyncio

from munchhausen.domain.backtest import BacktestVerdict
from munchhausen.domain.common import DecisionKind, FireRole, LifecycleStatus
from munchhausen.domain.draft import DraftStatus, Verdict
from munchhausen.domain.ids import decision_id
from munchhausen.domain.latches import FloorLatch
from munchhausen.learn.layers import L0Shape, L2Neighbours
from tests.test_adjudication import World, _admit_predecessor
from tests.test_adjudication_fakes import ARM, RUN, TERM, draft, episode, fire

RULE = "Active customers hold the RULE status set."
FLOOR = FloorLatch(collection="transactions", match={"rs": {"$ne": 3}})


def run(coro):  # noqa: ANN001, ANN201
    return asyncio.run(coro)


def test_b1_every_pair_raising_holds_and_never_refuses() -> None:
    w = World()

    async def boom(inp):  # noqa: ANN001, ANN202
        raise RuntimeError("model unavailable")

    w.models.propose = boom
    out = run(w.adjudicator().adjudicate(draft("d-gen", RULE, w.sources), w.ctx(at_idx=100)))
    assert out[-1].layer == "L4" and out[-1].verdict is Verdict.HOLD and out[-1].detail["reason"] == "insufficient"
    assert w.store.st.drafts["d-gen"].status is DraftStatus.HELD
    (bt,) = w.store.st.backtests.values()
    assert bt.verdict is BacktestVerdict.INSUFFICIENT and len(bt.errors) == 8 and bt.at_idx == 100
    # a later round reads afresh: the id is keyed by (draft, index)
    w.models.propose = type(w.models).propose.__get__(w.models)
    out = run(w.adjudicator().adjudicate(draft("d-gen", RULE, w.sources), w.ctx(at_idx=130)))
    assert out[-1].verdict is Verdict.ADMIT and len(w.store.st.backtests) == 2


def test_b1_thin_population_holds() -> None:
    w = World(n_per_template=1)        # 4 episodes, 2 of them sources: 2 scored pairs < BACKTEST_MIN_N
    out = run(w.adjudicator().adjudicate(draft("d-gen", RULE, w.sources), w.ctx()))
    assert out[-1].verdict is Verdict.HOLD and out[-1].detail["reason"] == "insufficient"


def test_b2_corroborating_fires_never_retire() -> None:
    w = World()
    pred = _admit_predecessor(w)
    for k in range(10):
        f = fire(pred, 20 + k, role=FireRole.CORROBORATING, k=k)
        w.store.st.fires[f.id] = f
    f = fire(pred, 40, k=99)
    w.store.st.fires[f.id] = f
    out = run(w.lifecycle().sweep(RUN, ARM, 50))
    assert out["retired"] == [] and out["contested"] == [pred]
    assert w.store.st.decisions[pred].is_admitted


def test_b3_nominator_seen_episodes_leave_the_population() -> None:
    w = World()
    seen = [e.id for e in w.store.st.episodes.values() if e.template == "t3"]
    d = draft("d-gen", RULE, w.sources).model_copy(update={"nominator_seen_episode_ids": tuple(seen)})
    bt = run(w.backtester().run(d, w.ctx())).backtest
    assert not {s.episode_id for s in bt.sampled} & set(seen)
    assert "t3" not in bt.source_templates, "seen neighbour episodes are excluded, not counted as sources"


def test_m1_a_flip_without_the_draft_applied_is_not_a_fix() -> None:
    w = World()
    real = w.models.propose

    async def unapplied(inp):  # noqa: ANN001, ANN202
        p = await real(inp)
        return p.model_copy(update={"consulted": ()})

    w.models.propose = unapplied
    bt = run(w.backtester().run(draft("d-gen", RULE, w.sources), w.ctx())).backtest
    assert bt.fixed == 0 and bt.verdict is BacktestVerdict.REFUSE
    assert all(s.applied is False and s.replay_answer is not None for s in bt.sampled)


def test_m2_twin_question_text_is_excluded() -> None:
    w = World()
    src = w.sources[0]
    twin = episode(77, "t3", correct=False, figure=5.0, question_id="other-id").model_copy(update={"text": src.text})
    w.add(twin)
    bt = run(w.backtester(n=40).run(draft("d-gen", RULE, w.sources), w.ctx())).backtest
    assert twin.id not in {s.episode_id for s in bt.sampled}


def test_m3_misses_meeting_the_hook_terms_come_first() -> None:
    w = World()
    for i in range(20):
        w.add(episode(200 + i, "t4", correct=False, figure=float(i), terms=()))
    bt = run(w.backtester().run(draft("d-gen", RULE, w.sources), w.ctx())).backtest
    misses = [w.store.st.episodes[s.episode_id] for s in bt.sampled if not s.original_correct]
    assert misses and all(TERM in e.terms for e in misses)


def test_m4_l0_refuses_a_floor_off_world_or_outside_the_sandbox() -> None:
    w = World()
    l0 = L0Shape(w.store.terms, world=w.world)
    w.store.st.views["transactions"] = ("transactions", [])     # the fake lists views as its collections
    ok = draft("d-f", "Transactions exclude batches whose rs field is 3.", w.sources, kind=DecisionKind.FLOOR,
               floor=FLOOR)
    assert run(l0.check(ok, w.ctx())).verdict is Verdict.PASS
    missing = draft("d-f2", "Ledger rows exclude batches whose rs field is 3.", w.sources, kind=DecisionKind.FLOOR,
                    floor=FloorLatch(collection="ledger", match={"rs": {"$ne": 3}}))
    assert run(l0.check(missing, w.ctx())).verdict is Verdict.REFUSE
    js = draft("d-f3", "Transactions exclude batches whose rs field is 3.", w.sources, kind=DecisionKind.FLOOR,
               floor=FloorLatch(collection="transactions", match={"$where": "true"}))
    out = run(l0.check(js, w.ctx()))
    assert out.verdict is Verdict.REFUSE and any("sandbox" in p for p in out.detail["problems"])


def test_m4_lifecycle_drops_only_floor_view_names() -> None:
    w = World()
    run(w.lifecycle()._drop(["transactions", "transactions__D-abc123"], by="D-x"))
    names = [(n, p.get("view")) for n, p in w.store.st.events if n.startswith("view.")]
    assert ("view.drop_refused", "transactions") in names and ("view.drop", "transactions__D-abc123") in names


def test_m6_admission_index_is_recorded_and_survives_a_flip() -> None:
    w = World(n_per_template=8)
    pred = _admit_predecessor(w)
    assert w.store.st.decisions[pred].admitted_at_idx == 20
    f = fire(pred, 12)
    w.store.st.fires[f.id] = f
    run(w.adjudicator().adjudicate(draft("d-succ", RULE, w.sources, supersedes=pred), w.ctx(at_idx=40)))
    p = w.store.st.decisions[pred]
    assert p.lifecycle.status is LifecycleStatus.SUPERSEDED and p.lifecycle.at_idx == 40 and p.admitted_at_idx == 20


def test_a_second_floor_on_one_collection_is_refused_at_l2() -> None:
    w = World()
    d1 = draft("d-floor", "Transactions exclude batches whose rs field is 3.", w.sources, kind=DecisionKind.FLOOR,
               floor=FLOOR)
    assert run(w.adjudicator().adjudicate(d1, w.ctx()))[-1].verdict is Verdict.ADMIT
    d2 = draft("d-floor2", "Transactions exclude batches whose rs field is 3.", w.sources, kind=DecisionKind.FLOOR,
               floor=FloorLatch(collection="transactions", match={"rs": {"$lt": 3}}))
    out = run(L2Neighbours(threshold=0.85, decisions=w.store.decisions, fires=w.store.fires).check(d2, w.ctx()))
    assert out.verdict is Verdict.REFUSE and out.neighbour_id == decision_id("d-floor")


def test_an_admission_error_is_recorded_on_the_draft_not_raised() -> None:
    w = World()

    async def ddl_fails(name, source, pipeline):  # noqa: ANN001, ANN202
        raise RuntimeError("createView failed")

    w.world.create_view = ddl_fails
    d1 = draft("d-floor", "Transactions exclude batches whose rs field is 3.", w.sources, kind=DecisionKind.FLOOR,
               floor=FLOOR)
    out = run(w.adjudicator().adjudicate(d1, w.ctx()))
    assert out[-1].layer == "admission" and out[-1].verdict is Verdict.HOLD
    assert w.store.st.drafts["d-floor"].status is DraftStatus.HELD and not w.store.st.decisions


def test_holdout_templates_get_reserved_sample_slots_hits_and_misses() -> None:
    w = World(n_per_template=8)
    for i in range(40):                       # crowd the population so the held-out template would be rare
        w.add(episode(300 + i, "t1", correct=i % 2 == 0, figure=float(i)))
    d = draft("d-gen", RULE, w.sources).model_copy(update={"holdout_templates": ("t4",)})
    b = w.backtester()
    b.holdout_share = 0.25
    bt = run(b.run(d, w.ctx())).backtest
    held = [s for s in bt.sampled if s.template == "t4"]
    assert bt.holdout_reserved == 2 and bt.holdout_available == 2 and len(bt.sampled) == 8
    assert len(held) >= 2 and {s.original_correct for s in held} == {True, False}
    assert bt.fixed_heldout >= 1


def test_holdout_short_population_records_what_it_had() -> None:
    w = World()
    d = draft("d-gen", RULE, w.sources).model_copy(update={"holdout_templates": ("t9",)})
    bt = run(w.backtester().run(d, w.ctx())).backtest
    assert bt.holdout_reserved == 2 and bt.holdout_available == 0 and len(bt.sampled) == 8
    no_fold = run(w.backtester().run(draft("d-plain", RULE, w.sources), w.ctx())).backtest
    assert no_fold.holdout_reserved == 0 and no_fold.holdout_available is None
