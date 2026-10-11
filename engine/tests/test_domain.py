"""Domain invariants: hooks, lifecycle, admission plans, backtest read, L0, evidence state."""

from __future__ import annotations

import pytest

from munchhausen.domain.admission import plan_admission
from munchhausen.domain.backtest import Backtest, BacktestSample, BacktestThresholds, BacktestVerdict
from munchhausen.domain.common import (
    DecisionKind,
    EvidenceState,
    FireDisposition,
    FireRole,
    LifecycleStatus,
    Signature,
)
from munchhausen.domain.decision import Decision, Lifecycle, LifecycleError, Option, Warrant, evidence_state
from munchhausen.domain.draft import Draft, Route
from munchhausen.domain.latches import FloorLatch, Guard, HookLatch, KeySet, NotThisRow, RevisitLatch
from munchhausen.domain.question import QuestionKeys
from munchhausen.domain.scoring import matches


def keys(terms=(), colls=(), persona=None) -> QuestionKeys:  # noqa: ANN001
    return QuestionKeys(terms=frozenset(terms), collections=frozenset(colls), persona=persona)


def entry_fields(**over):  # noqa: ANN003, ANN201
    base = dict(
        title="Active customers carry status codes two or seven",
        kind=DecisionKind.TAXONOMIC,
        payload="A customer is active when field st holds one of the codes in the active set.",
        options=(Option(definition="not closed", verdict="rejected", prior=True),
                 Option(definition="st in active set", verdict="chosen")),
        forecloses="counting every non-closed customer",
        latches=(HookLatch(fires_when=KeySet(terms=("active customers",), collections=("customers",)),
                           not_this=(NotThisRow(terms=("active accounts",), contrast="a count of accounts"),)),
                 RevisitLatch(id="T-x-1", signature=Signature.SET_MEMBER, guard=Guard(min_residuals=2, window=30))),
        residue="does not check joins from accounts",
        warrant=Warrant(source_observation_ids=("o1",), source_episode_ids=("e1",), templates=2,
                        falsifier="two attributable residuals within 30 consultations"),
    )
    base.update(over)
    return base


def make_draft(**over) -> Draft:  # noqa: ANN003
    return Draft(_id="r:a:r1:x", run_id="r", arm="governed", shape_id="S-1",
                 source_observation_ids=("o1",), round=1, **entry_fields(**over))


def test_hook_matches_on_terms_or_collections_and_respects_not_this() -> None:
    hook = make_draft().hook
    assert hook.matches(keys(terms=["active customers"]))
    assert hook.matches(keys(colls=["customers"]))
    assert not hook.matches(keys(colls=["customers"], terms=["active accounts"]))
    assert not hook.matches(keys(colls=["transactions"]))


def test_persona_scope_is_required() -> None:
    hook = HookLatch(fires_when=KeySet(terms=("revenue",), persona="dana"))
    assert hook.matches(keys(terms=["revenue"], persona="dana"))
    assert not hook.matches(keys(terms=["revenue"], persona="omar"))


def test_lifecycle_transitions_only_from_admitted() -> None:
    lc = Lifecycle(status=LifecycleStatus.ADMITTED, at_idx=10)
    sup = lc.supersede("D-2", 40)
    assert sup.status is LifecycleStatus.SUPERSEDED and sup.superseded_by == "D-2"
    with pytest.raises(LifecycleError):
        sup.retire(50, "late")


def test_l0_refuses_structural_gaps_and_leaked_figures() -> None:
    assert make_draft().l0_violations([1204.0]) == []
    leaky = make_draft(payload="Active customers number 1,204 in total.")
    assert any("source figure" in p for p in leaky.l0_violations([1204.0]))
    no_reject = make_draft(options=(Option(definition="x", verdict="chosen"),))
    assert any("rejected" in p for p in no_reject.l0_violations([]))
    bad_floor = make_draft(kind=DecisionKind.FLOOR)
    assert any("floor latch" in p for p in bad_floor.l0_violations([]))


def _sample(t: str, o: bool, with_: bool, without: bool) -> BacktestSample:
    return BacktestSample(episode_id=f"e{t}{o}{with_}{without}", template=t, original_correct=o,
                          replay_correct=with_, baseline_correct=without)


TH = BacktestThresholds(min_fixed=2, min_fixed_heldout=1, max_broken=1)


def _read(sampled: tuple[BacktestSample, ...]) -> Backtest:
    return Backtest.read(id="B", run_id="r", arm="g", draft_id="d", sampled=sampled,
                         source_templates=frozenset({"a"}), thresholds=TH)


def test_backtest_read_requires_heldout_fix() -> None:
    only_source = (_sample("a", False, True, False), _sample("a", False, True, False), _sample("b", True, True, True))
    bt = _read(only_source)
    assert (bt.fixed, bt.fixed_heldout, bt.verdict) == (2, 0, BacktestVerdict.REFUSE)
    with_heldout = (*only_source[:1], _sample("c", False, True, False), _sample("b", True, False, True))
    bt = _read(with_heldout)
    # review M1: admission also needs fixed − broken ≥ min_fixed, so one break against two fixes refuses
    assert (bt.fixed, bt.fixed_heldout, bt.broken, bt.verdict) == (2, 1, 1, BacktestVerdict.REFUSE)
    bt = _read((*with_heldout[:2], _sample("b", True, True, True)))
    assert (bt.fixed, bt.fixed_heldout, bt.broken, bt.verdict) == (2, 1, 0, BacktestVerdict.ADMIT)


def test_backtest_read_is_paired() -> None:
    """A miss re-solved by chance in both replays fixes nothing; a hit lost in both breaks nothing."""
    chance = (_sample("b", False, True, True), _sample("c", False, True, True), _sample("c", True, False, False))
    bt = _read(chance)
    assert (bt.fixed, bt.broken, bt.verdict) == (0, 0, BacktestVerdict.REFUSE)
    # the counterfactual, not the recorded outcome, decides: a recorded hit the draft rescues counts as fixed
    rescued = (_sample("b", True, True, False), _sample("c", True, True, False))
    assert _read(rescued).fixed == 2


def test_supersede_plan_flips_predecessor_and_wires_lineage() -> None:
    pred = Decision(_id="D-old", run_id="r", arm="governed",
                    lifecycle=Lifecycle(status=LifecycleStatus.ADMITTED, at_idx=5), **entry_fields())
    draft = make_draft().model_copy(update={"route": Route.SUPERSEDE, "supersedes": "D-old"})
    plan = plan_admission(draft, at_idx=320, backtest_id="B-1", lens_score=0.7, predecessors=(pred,))
    assert plan.decision.wiring.supersedes == "D-old" and plan.decision.wiring.edges == ("D-old",)
    assert plan.flips[0].lifecycle.superseded_by == plan.decision.id
    assert plan.decision.warrant.backtest_id == "B-1"


def test_floor_admission_rewires_tool_access() -> None:
    floor = make_draft(kind=DecisionKind.FLOOR,
                       latches=(*make_draft().latches, FloorLatch(collection="transactions", match={"rs": {"$ne": 3}})))
    plan = plan_admission(floor, at_idx=100, backtest_id="B", lens_score=None, view_name="transactions__D-x")
    assert plan.rewire is not None and plan.rewire.logical == "transactions"


def test_evidence_state_is_computed_from_open_dispositive_fires() -> None:
    assert evidence_state([(FireRole.CORROBORATING, FireDisposition.OPEN)]) is EvidenceState.CLEAR
    assert evidence_state([(FireRole.DISPOSITIVE, FireDisposition.OPEN)]) is EvidenceState.CONTESTED


def test_scoring() -> None:
    assert matches(1204.0, 1204.05, rel_tol=1e-4)
    assert not matches(1204.0, 1300.0, rel_tol=1e-4)
    assert matches(["AAPL", "msft"], ["msft", "aapl"], rel_tol=0)
    assert not matches(None, 1.0, rel_tol=1e-4)


def test_leaked_figures_ignores_dates_and_small_figures() -> None:
    from munchhausen.domain.decision import leaked_figures

    assert leaked_figures("born on or after 1970-01-01T00:00:00Z", [1.0]) == []
    assert leaked_figures("codes 2 and 7 count", [2.0], min_abs=10.0) == []
    assert leaked_figures("the total is 1,204", [1204.0], min_abs=10.0) == ["1204"]
