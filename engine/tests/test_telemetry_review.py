"""S5 review fixes: proxy verdicts, F4 resolution rules, paired-pair hygiene, rolling paired curve, premise join,
injection separation, guard refusals from episodes, resume diff, planted-map fallback, call-path details."""

from __future__ import annotations

import asyncio
import contextvars
import copy
import json
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from munchhausen import evidence
from munchhausen.config import Settings
from munchhausen.domain.registers import PlantedMapping, RunRecord
from munchhausen.impl import models_anthropic as M
from munchhausen.metrics import readings as R
from munchhausen.metrics import synthetic
from munchhausen.metrics.planted_map import planted_map
from munchhausen.store.repositories import round_pipeline


@pytest.fixture
def s(settings_offline: Settings) -> Settings:
    return settings_offline


@pytest.fixture
def run(s: Settings) -> tuple[dict[str, list[dict[str, Any]]], R.Context]:
    arms = s.arms()
    return synthetic.rows(arms), synthetic.context(arms, s.forecasts())


# --- B2 proxy -------------------------------------------------------------------------------------------


def test_proxy_readings_never_get_agreement_verdicts(run: Any) -> None:
    rows, ctx = run
    no_map = {**rows, "planted_map": []}
    f1 = R.read_forecast("F1", ctx.forecasts["F1"], no_map, ctx)
    assert f1["verdict"] and all(v == "unread (proxy)" for v in f1["verdict"].values())
    f4 = R.read_forecast("F4", ctx.forecasts["F4"], no_map, ctx)
    assert f4["verdict"]["F4.ungated-governed"] == "unread (proxy)"


# --- M1 + S4 addendum: resolution is supersession only ----------------------------------------------------


def test_converge_and_retire_do_not_resolve_a_drift(run: Any) -> None:
    rows, ctx = run
    rows = copy.deepcopy(rows)
    for d in rows["decisions"]:
        if d["_id"] == "D-ungated-q1":
            d["lifecycle"] = {"status": "converged", "at_idx": 450, "converged_into": "D-ungated-q1b"}
    i, how, held = R.resolution_idx(rows, ctx, "ungated", drift="D1", prefix="Q1")
    assert i is None and held and "held but unresolved" in how
    f4 = R.read_forecast("F4", ctx.forecasts["F4"], rows, ctx)
    assert f4["verdict"]["F4.ungated-governed"] == "unread"
    # never held is reported apart from held-but-unresolved
    _, how_f, held_f = R.resolution_idx(rows, ctx, "frozen", drift="D1", prefix="Q1")
    assert not held_f and how_f.startswith("never held")


def test_f1_window_does_not_end_at_a_converge(run: Any) -> None:
    rows, ctx = run
    rows = copy.deepcopy(rows)
    for d in rows["decisions"]:
        if d["_id"] == "D-governed-q1":
            d["lifecycle"] = {"status": "converged", "at_idx": 360}
    gov = next(r for r, _ in R.drift_calibration(rows, ctx, drift="D1", prefix="Q1", reference="frozen", margin=0.05)
               if r.name == "F1.governed")
    assert "300…449" in gov.population


# --- M2 pairs ---------------------------------------------------------------------------------------------


def test_pairs_drop_errors_and_question_mismatches(run: Any) -> None:
    rows, ctx = run
    rows = copy.deepcopy(rows)
    eps = [e for e in rows["episodes"] if e["arm"] == "governed" and e["stream"] == "stream"]
    eps[400]["error"] = "episode_failed: ProposalError"
    eps[401]["question_id"] = "other"
    xa, _, idx, drop = R._pairs(rows, "governed", "naive", lambda e: True)
    assert drop == {"error.governed": 1, "error.naive": 0, "question_mismatch": 1}
    assert 400 not in idx and 401 not in idx and len(xa) == len(idx)
    r, _ = R.paired_accuracy(rows, ctx, "governed", "naive", population="all", after_round=10, margin=0.05)
    assert "error.governed 1" in r.note and "question_mismatch 1" in r.note
    summ = {x.name: x for x in R.arm_summary(rows, ctx, "governed")}
    assert summ["governed.errored_episodes"].value == 1


# --- M8 rolling paired, floor, injection, guard refusals ---------------------------------------------------


def test_rolling_paired_difference_vs_reference(run: Any) -> None:
    rows, ctx = run
    curves = R.rolling_paired(rows, ctx, "frozen")
    assert "frozen" not in curves and curves["governed"]
    p = curves["governed"][-1]
    assert p["lo"] <= p["diff"] <= p["hi"] and p["n"] > 0
    out = R.all_readings(rows, ctx)
    assert out["reference"] == "frozen" and out["paired_curves"]["governed"]


def test_injection_is_counted_apart_from_organic(run: Any) -> None:
    rows, ctx = run
    rows = copy.deepcopy(rows)
    gov_bt = [b for b in rows["backtests"] if b["arm"] == "governed"]
    before = {r.name: r for r in R.backtest_summary(rows, ctx)}["backtest.admit_rate.governed"].n
    inj = gov_bt[0]["draft_id"]
    for d in rows["drafts"]:
        if d["_id"] == inj:
            d["source"] = "injection"
    after = {r.name: r for r in R.backtest_summary(rows, ctx)}["backtest.admit_rate.governed"].n
    assert after == before - 1
    inj_r = {r.name: r for r in R.injection_readings(rows, ctx, [{"name": "injection.figure"}])}
    assert inj_r["injection.drafts"].value == 1 and inj_r["injection.events"].value == {"injection.figure": 1}


def test_guard_refusals_read_from_episodes_with_party_from_trace(run: Any) -> None:
    rows, ctx = run
    rows = copy.deepcopy(rows)
    ep = next(e for e in rows["episodes"] if e["arm"] == "governed")
    ep["error"] = "PipelineRefused: $out"
    out = {r.name: r for r in R.sandbox_readings(rows, [], ctx)}
    g = out["sandbox.guard_refusals.governed"]
    assert g.value == 1 and "unknown 1" in g.note
    ev = [{"name": "guard_refusal", "episode_id": ep["_id"], "party": "proposer"}]
    out = {r.name: r for r in R.sandbox_readings(rows, ev, ctx)}
    assert "proposer 1" in out["sandbox.guard_refusals.governed"].note


def test_floor_readings_from_tool_access_and_view_map(run: Any) -> None:
    rows, ctx = run
    rows = copy.deepcopy(rows)
    rows["tool_access"] = [{"run_id": "synthetic", "arm": "governed", "logical": "customers",
                            "view": "customers__D-x", "decision_id": "D-x"}]
    for e in rows["episodes"]:
        if e["arm"] == "governed" and e.get("idx", 0) >= 500 and e["stream"] == "stream":
            e["view_map"] = {"customers": "customers__D-x"}
    out = {r.name: r for r in R.floor_readings(rows, ctx)}
    assert out["floor.rewires.governed"].n == 1 and out["floor.view_filtered.governed"].value == 100


# --- S4 addendum: premise joined to the planted map --------------------------------------------------------


def test_premise_joins_the_planted_map(run: Any) -> None:
    rows, ctx = run
    out = {r.name: r for r in R.backtest_summary(rows, ctx)}
    assert "PROXY" in out["backtest.premise.governed"].note             # drafts not mapped in the fixture
    rows = copy.deepcopy(rows)
    for b in rows["backtests"]:
        if b["arm"] == "governed":
            rows["planted_map"].append({"_id": f"PM-{b['draft_id']}", "run_id": "synthetic", "arm": "governed",
                                        "decision_id": b["draft_id"], "quirk": "Q1_active_customer",
                                        "scope": "org", "model": "x", "subject": "draft"})
    joined = {r.name: r for r in R.backtest_summary(rows, ctx)}["backtest.premise.governed"]
    assert "PROXY" not in joined.note and joined.n < out["backtest.premise.governed"].n
    # draft-subject rows never count as decisions in F2
    assert R.read_forecast("F2", ctx.forecasts["F2"], rows, ctx)["verdict"] == "agrees"


def test_f2_with_an_absent_arm_is_unread(run: Any) -> None:
    rows, ctx = run
    ctx = replace(ctx, arms={a: s for a, s in ctx.arms.items() if a != "naive"})
    assert R.read_forecast("F2", ctx.forecasts["F2"], rows, ctx)["verdict"] == "unread"


# --- B2 planted map: per-subject failure, fallback, persisted as read ----------------------------------------


def test_planted_map_falls_back_and_persists_each_row() -> None:
    subj = [("decision", SimpleNamespace(id=f"D-{i}", run_id="r", arm="governed",
                                         hook=SimpleNamespace(fires_when=SimpleNamespace(persona=None))))
            for i in range(3)]
    written: list[PlantedMapping] = []

    async def judge(d: Any, model: str) -> str | None:
        if d.id == "D-0" and model == "opus":
            raise RuntimeError("429")
        if d.id == "D-2":
            raise RuntimeError("down")
        return "Q1_x"

    async def sink(row: PlantedMapping) -> None:
        written.append(row)

    res = asyncio.run(planted_map(subj, judge, ["Q1_x"], models=["opus", "sonnet"], concurrency=2, sink=sink))
    assert {r.decision_id: r.model for r in written} == {"D-0": "sonnet", "D-1": "opus"}
    assert res.failed == {"D-2": "RuntimeError"} and res.by_model == {"sonnet": 1, "opus": 1}


# --- M3 resume ------------------------------------------------------------------------------------------


def _rec(s: Settings, **kw: Any) -> RunRecord:
    r = evidence.build_run_record(s, selection={"governed": {"x": "a"}}, capabilities={}, git=("sha1", False),
                                  prompts={"proposer": "h1"}, pack_hash="p1", world_counts={}, now=datetime.now(UTC),
                                  length=60)
    return r.model_copy(update=kw)


def test_resume_diff_names_what_moved(s: Settings) -> None:
    a = _rec(s)
    b = _rec(s, git_sha="sha2", prompt_hashes={"proposer": "h2"}, knobs={**a.knobs, "backtest_n": 99})
    moved = evidence.resume_diff(a, b)
    assert set(moved) == {"git_sha", "prompt_hashes", "knobs.backtest_n"}
    assert moved["knobs.backtest_n"] == {"registered": a.knobs["backtest_n"], "current": 99}


def test_start_run_appends_a_resume_entry(s: Settings) -> None:
    calls: list[Any] = []

    class Runs:
        rec: RunRecord | None = None

        async def get(self, rid: str) -> RunRecord | None:
            return self.rec

        async def start(self, r: RunRecord) -> RunRecord:
            self.rec = r
            return r

        async def append_resume(self, rid: str, entry: dict[str, Any]) -> None:
            calls.append(entry)

    async def zero(rid: str) -> int:
        return 0

    async def caps() -> dict[str, Any]:
        return {}

    def world() -> Any:
        raise RuntimeError

    store = SimpleNamespace(runs=Runs(), capabilities=caps, evidence=SimpleNamespace(episode_count=zero))
    h = SimpleNamespace(settings=s, selection=lambda: {}, world=world, shared=lambda *a: SimpleNamespace(event=print),
                        store=store)
    asyncio.run(evidence.start_run(h, length=60))
    asyncio.run(evidence.start_run(h, length=60))
    assert calls == []                                         # nothing moved: no entry
    asyncio.run(evidence.start_run(h, length=120))
    assert calls and calls[0]["moved"]["length"] == {"registered": 60, "current": 120}


# --- call path: temperature, cache key, contextvar episode id, rounds tokens -------------------------------


def test_cache_key_covers_arm_effort_tokens_temperature(s: Settings) -> None:
    m = M.AnthropicModels.__new__(M.AnthropicModels)
    m._s = s
    k = dict(arm="a", effort=None, max_tokens=10, temperature=None)
    base = m._cache_path("mod", "sys", "u", RunRecord, **k)
    for change in ({"arm": "b"}, {"effort": "low"}, {"max_tokens": 11}, {"temperature": 0.0}):
        assert m._cache_path("mod", "sys", "u", RunRecord, **{**k, **change}) != base


def test_parse_sends_temperature_as_extra_body(s: Settings) -> None:
    seen: dict[str, Any] = {}

    class Msgs:
        async def parse(self, **kw: Any) -> Any:
            seen.update(kw)
            return SimpleNamespace(stop_reason="end_turn", parsed_output=SimpleNamespace(), usage=None,
                                   model="claude-haiku-4-5")

    m = M.AnthropicModels.__new__(M.AnthropicModels)
    m._s, m._spend, m.lost_spend_writes = s, None, 0
    m.client = SimpleNamespace(messages=Msgs())
    asyncio.run(m.parse(stage="propose", arm="a", model="x", system="s", user="u", wire=RunRecord, temperature=0.0))
    assert seen["extra_body"] == {"temperature": 0.0}
    seen.clear()
    asyncio.run(m.parse(stage="propose", arm="a", model="x", system="s", user="u", wire=RunRecord))
    assert "extra_body" not in seen


def test_spend_meta_carries_the_current_episode_id(s: Settings) -> None:
    var: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_episode_id", default=None)
    assert M.current_episode_id() is None
    tok = var.set("r:governed:e7")
    try:
        assert M.current_episode_id() == "r:governed:e7"
    finally:
        var.reset(tok)

    rows: list[Any] = []

    class Spend:
        async def record(self, row: Any) -> None:
            rows.append(row)

    class Broken:
        async def record(self, row: Any) -> None:
            raise OSError

    m = M.AnthropicModels.__new__(M.AnthropicModels)
    m._s, m._spend, m.lost_spend_writes = s, Spend(), 0

    async def go() -> None:
        var.set("r:governed:e8")
        await m.record_call(stage="propose", arm="governed", model="claude-haiku-4-5", usage=None, latency_ms=1)

    asyncio.run(go())
    assert rows[0].meta["episode_id"] == "r:governed:e8"
    m._spend = Broken()
    asyncio.run(m.record_call(stage="propose", arm="governed", model="x", usage=None, latency_ms=1))
    assert m.lost_spend_writes == 1


def test_round_tokens_come_from_spend_or_null() -> None:
    p = json.dumps(round_pipeline("r", "governed", 3, (90, 120)))
    assert '"meta.episode_id"' in p and '"$tokens.in"' not in p
    assert '"tokens_in": {"$ifNull": ["$_tin", null]}' in p


# --- readiness review: proposer errors are misses; E9 proxy; window labels ---------------------------------


def test_proposer_execution_error_counts_as_a_miss(run: Any) -> None:
    rows, ctx = run
    rows = copy.deepcopy(rows)
    eps = [e for e in rows["episodes"] if e["arm"] == "governed" and e["stream"] == "stream"]
    hit = next(e for e in eps if e["correct"] and e["idx"] >= 300)
    base_acc = {r.name: r for r in R.arm_summary(rows, ctx, "governed")}["governed.stream_accuracy"]
    hit["error"], hit["correct"] = "empty result", False
    after = {r.name: r for r in R.arm_summary(rows, ctx, "governed")}
    assert after["governed.stream_accuracy"].n == base_acc.n                     # still scored
    assert after["governed.stream_accuracy"].value < base_acc.value              # as a miss
    assert after["governed.errored_episodes"].value == 0                         # not a harness failure
    xa, _, idx, drop = R._pairs(rows, "governed", "naive", lambda e: True)
    assert hit["idx"] in idx and xa[idx.index(hit["idx"])] == 0.0 and drop["error.governed"] == 0
    hit["error"] = "episode_failed: TimeoutError"                                # a harness failure: excluded
    _, _, idx, drop = R._pairs(rows, "governed", "naive", lambda e: True)
    assert hit["idx"] not in idx and drop["error.governed"] == 1


def test_round_pipeline_excludes_only_harness_failures() -> None:
    p = json.dumps(round_pipeline("r", "governed", 3, (90, 120)))
    assert '"$indexOfCP"' in p and '"episode_failed"' in p


def test_e9_without_a_planted_map_is_unread_proxy(run: Any) -> None:
    rows, ctx = run
    out = {r.name: r for r in R.retrieval_lead({**rows, "planted_map": []}, ctx)}
    e9 = out["E9.naive-over-governed"]
    assert e9.status == "unread (proxy)" and e9.value is None
    assert {r.name: r for r in R.retrieval_lead(rows, ctx)}["E9.naive-over-governed"].status is None


def test_windows_never_labelled_past_the_last_index(s: Settings) -> None:
    arms = s.arms()
    rows = synthetic.rows(arms, run_length=240)
    ctx = synthetic.context(arms, s.forecasts(), run_length=600)       # registered length longer than the run
    curves = R.rolling_paired(rows, ctx, "frozen")
    assert max(p["idx_hi"] for p in curves["governed"]) == 239
    assert max(p["idx_hi"] for p in R.stream_curve(rows, ctx, "governed")) == 239


def test_paired_accuracy_controls_population_and_unknown_population_refused(run) -> None:  # noqa: ANN001
    import pytest

    rows, ctx = run
    r, _ = R.paired_accuracy(rows, ctx, "governed", "ungated", population="controls", after_round=10, margin=0.05)
    assert r.population.startswith("control stream questions")
    with pytest.raises(ValueError):
        R.paired_accuracy(rows, ctx, "governed", "ungated", population="contrls", after_round=10, margin=0.05)
