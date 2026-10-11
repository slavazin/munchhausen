"""Hold to accrue (approved 2026-10-11, "A + floor bar 2"): a draft with no held-out fold whose backtest
clears everything but the held-out fix is HELD (`awaiting_heldout_template`), not refused; its evidence goes
back `open` and a later 3-template shape re-nominates it with a fold, where the full held-out rule applies.
A wrong draft is still refused. The floor bar is 2, so a 3-template floor folds to 2 + 1 and is not undone."""

from __future__ import annotations

import asyncio
from typing import Any

from munchhausen.config import Settings
from munchhausen.domain.backtest import Backtest, BacktestSample, BacktestThresholds, BacktestVerdict
from munchhausen.domain.common import DecisionKind
from munchhausen.domain.draft import DraftStatus, Verdict
from munchhausen.domain.ids import decision_id
from munchhausen.domain.observation import ObservationDisposition
from munchhausen.learn.adjudicate import Adjudicator
from munchhausen.learn.backtest import BacktestRun
from munchhausen.learn.curators import LayeredCurator
from munchhausen.learn.episodic import shape_of
from munchhausen.learn.layers import L4Backtest
from tests import test_shaping as S3
from tests.test_adjudication import World
from tests.test_adjudication_fakes import draft

RULE = "Active customers hold the RULE status set."


def run(coro):  # noqa: ANN001, ANN201
    return asyncio.run(coro)


def _no_heldout_fix(w: World) -> None:
    """Held-out templates (t3, t4) answer something the draft does not reproduce: fixes land on t1/t2 only."""
    for e in list(w.store.st.episodes.values()):
        if e.template in ("t3", "t4") and not e.correct:
            w.prior[e.question_id] = w.right[e.question_id] = e.confirmed_figure + 1.0


def test_two_template_draft_that_clears_but_the_heldout_fix_is_held() -> None:
    w = World(n_per_template=8)
    _no_heldout_fix(w)
    out = run(w.adjudicator().adjudicate(draft("d-2t", RULE, w.sources), w.ctx()))
    l4 = out[-1]
    assert (l4.layer, l4.verdict, l4.detail["reason"]) == ("L4", Verdict.HOLD, "awaiting_heldout_template")
    assert l4.detail["fixed"] >= 2 and l4.detail["broken"] == 0 and l4.detail["fixed_heldout"] == 0
    assert w.store.st.drafts["d-2t"].status is DraftStatus.HELD and not w.store.st.decisions
    (bt,) = w.store.st.backtests.values()
    assert bt.verdict is BacktestVerdict.AWAITING_HELDOUT
    assert any(n == "backtest" and p["verdict"] == "awaiting_heldout" for n, p in w.store.st.events)


def test_the_same_draft_breaking_hits_is_refused_not_held() -> None:
    w = World(n_per_template=8)
    _no_heldout_fix(w)
    for e in w.store.st.episodes.values():
        if e.correct:
            w.right[e.question_id] = e.confirmed_figure + 5.0      # applying the draft breaks every hit
    out = run(w.adjudicator().adjudicate(draft("d-2t", RULE, w.sources), w.ctx()))
    assert out[-1].layer == "L4" and out[-1].verdict is Verdict.REFUSE and out[-1].detail["broken"] >= 3
    assert w.store.st.drafts["d-2t"].status is DraftStatus.REFUSED


def test_poisoned_two_template_draft_is_refused_not_held() -> None:
    w = World(n_per_template=8)
    out = run(w.adjudicator().adjudicate(draft("d-p", "Active customers follow the POISON count.", w.sources),
                                         w.ctx()))
    assert out[-1].verdict is Verdict.REFUSE and out[-1].detail["fixed"] == 0


def test_renominated_with_a_fold_is_admitted_on_a_heldout_fix() -> None:
    w = World(n_per_template=8)
    d = draft("d-3t", RULE, w.sources).model_copy(update={"holdout_templates": ("t3",)})
    out = run(w.adjudicator().adjudicate(d, w.ctx()))
    assert out[-1].verdict is Verdict.ADMIT and out[-1].detail["fixed_heldout"] >= 1
    assert out[-1].detail["holdout_available"] >= 1 and decision_id("d-3t") in w.store.st.decisions


# --- end to end with the episodic pass (S3) ------------------------------------------------------------


class _Backtester:
    """Fixes on the draft's own templates; a fix on each held-out template when it has a fold."""

    async def run(self, d: Any, ctx: Any) -> BacktestRun:
        own = sorted({o.template for o in ctx.sources})
        samples = [BacktestSample(episode_id=f"x{i}", template=own[i % len(own)], original_correct=False,
                                  replay_correct=True, baseline_correct=False, applied=True) for i in range(3)]
        samples += [BacktestSample(episode_id=f"h-{t}", template=t, original_correct=False, replay_correct=True,
                                   baseline_correct=False, applied=True) for t in d.holdout_templates]
        bt = Backtest.read(id=f"B-{d.id}", run_id=d.run_id, arm=d.arm, draft_id=d.id, sampled=tuple(samples),
                           source_templates=frozenset(own), holdout_fold=bool(d.holdout_templates),
                           thresholds=BacktestThresholds(min_fixed=2, min_fixed_heldout=1, max_broken=1, min_n=2))
        return BacktestRun(backtest=bt)


class _Lifecycle:
    def __init__(self) -> None:
        self.plans: list[Any] = []

    async def admit(self, plan: Any) -> None:
        self.plans.append(plan)


def test_end_to_end_hold_reopens_then_a_third_template_renominates_with_a_fold_and_admits() -> None:
    life = _Lifecycle()
    rows = [S3.obs("o1", "r:a:e1", template="t1"), S3.obs("o2", "r:a:e2", template="t1"),
            S3.obs("o3", "r:a:e3", template="t2"), S3.obs("o4", "r:a:e4", template="t2")]
    p, store, drafts, _, _ = S3.build(S3.GAP, Verdict.HOLD, rows, models=S3.Warranting(), holdout=1)
    p.adjudicator = Adjudicator(curator=LayeredCurator("governed", [L4Backtest(_Backtester())]), drafts=drafts,
                                decisions=None, fires=None, lifecycle=life, view_name=lambda c, d: f"{c}__{d}")
    (held_id,) = run(p.run("r", "a", 0)).drafts
    assert drafts.rows[held_id].status is DraftStatus.HELD
    assert drafts.rows[held_id].adjudication["L4"].detail["reason"] == "awaiting_heldout_template"
    assert all(r.disposition is ObservationDisposition.OPEN for r in store.rows.values())
    store.rows["o5"] = S3.obs("o5", "r:a:e5", template="t3")      # a third template arrives
    (succ_id,) = run(p.run("r", "a", 1)).drafts
    succ = drafts.rows[succ_id]
    assert succ.holdout_templates and drafts.rows[held_id].status is DraftStatus.REFUSED
    assert succ.adjudication["L4"].verdict is Verdict.ADMIT and len(life.plans) == 1
    assert all(r.disposition is ObservationDisposition.SPENT for r in store.rows.values())


def test_a_three_template_floor_folds_to_two_plus_one_and_is_not_undone(settings_offline: Settings) -> None:
    assert settings_offline.bar_min_templates_floor == 2
    rows = [S3.obs("o1", "r:a:e1", template="t1"), S3.obs("o2", "r:a:e2", template="t1"),
            S3.obs("o3", "r:a:e3", template="t2"), S3.obs("o4", "r:a:e4", template="t2"),
            S3.obs("o5", "r:a:e5", template="t4")]
    p, _, drafts, trace, _ = S3.build(S3.GAP, Verdict.ADMIT, rows, holdout=1,
                                      models=S3.Warranting(DecisionKind.FLOOR))
    assert p.min_templates_floor == 2
    fold = p.fold(shape_of(rows), rows)
    assert len(fold.templates) == 1 and len(fold.shape.templates) == 2
    (did,) = run(p.run("r", "a", 0)).drafts
    d = drafts.rows[did]
    assert len(d.holdout_templates) == 1 and "holdout.undone" not in trace.names()
