"""S5 telemetry and evidence: verdicts, readings on synthetic runs, manifest completeness, the run record's
secret hygiene, the shared call path's spend rows, the trace file, and the run-start seam. Offline."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from munchhausen import evidence
from munchhausen.config import Settings
from munchhausen.domain.registers import TRACE_EVENTS, RunRecord
from munchhausen.impl.models_anthropic import spend_row
from munchhausen.impl.sinks import JsonlTrace, events_path, read_events
from munchhausen.metrics import readings as R
from munchhausen.metrics import report as rep
from munchhausen.metrics import synthetic
from munchhausen.metrics.paired import difference_of_means, paired_difference
from munchhausen.store.repositories import round_pipeline


@pytest.fixture
def s(settings_offline: Settings) -> Settings:
    return settings_offline


@pytest.fixture
def run(s: Settings) -> tuple[dict[str, list[dict[str, Any]]], R.Context]:
    arms = s.arms()
    return synthetic.rows(arms), synthetic.context(arms, s.forecasts())


# --- verdicts ---------------------------------------------------------------------------------------------


def test_three_way_verdict_and_unread() -> None:
    hi = [1.0] * 40 + [0.0] * 10
    lo = [0.0] * 40 + [1.0] * 10
    assert R.verdict3(paired_difference(hi, lo, n_boot=300, level=0.9, seed=1), 0.05) == "above"
    assert R.verdict3(paired_difference(lo, hi, n_boot=300, level=0.9, seed=1), 0.05) == "below"
    assert R.verdict3(paired_difference(hi, hi, n_boot=300, level=0.9, seed=1), 0.05) == "within"
    assert R.verdict3(paired_difference([], [], n_boot=300, level=0.9, seed=1), 0.05) == "unread"


def test_difference_of_means_reads_two_windows() -> None:
    r = difference_of_means([0.5] * 30, [0.0] * 60, n_boot=300, level=0.9, seed=1)
    assert r.diff == pytest.approx(0.5) and r.n == 30 and r.lo == pytest.approx(0.5)


def test_forecast_naming_an_absent_arm_is_unread(run: Any) -> None:
    rows, ctx = run
    ctx = replace(ctx, arms={a: s for a, s in ctx.arms.items() if a != "ungated"})
    f = R.read_forecast("F6", ctx.forecasts["F6"], rows, ctx)
    assert f["verdict"] == "unread" and "ungated" in f["note"]


def test_paired_accuracy_reads_the_planted_gap(run: Any) -> None:
    rows, ctx = run
    f = R.read_forecast("F5", ctx.forecasts["F5"], rows, ctx)
    assert f["verdict"] == "above"
    (r,) = f["readings"]
    assert r["n"] > 100 and r["interval"][0] > 0.05 and "quirk-bearing" in r["population"]


def test_quirk_bearing_population_unread_without_pack(run: Any) -> None:
    rows, ctx = run
    f = R.read_forecast("F5", ctx.forecasts["F5"], rows, replace(ctx, template_quirk={}))
    assert f["verdict"] == "unread"


# --- F1 calibration gap ------------------------------------------------------------------------------------


def test_f1_reads_a_synthetic_calibration_gap(run: Any) -> None:
    rows, ctx = run
    f = R.read_forecast("F1", ctx.forecasts["F1"], rows, ctx)
    v = f["verdict"]
    assert set(v) == {"F1.naive", "F1.ungated", "F1.governed"}      # frozen holds nothing: not read
    assert all(x == "above" for x in v.values())
    gov = next(r for r in f["readings"] if r["name"] == "F1.governed")
    assert "300…359" in gov["population"]                            # window stops at the supersession (idx 360)
    assert "frozen-referenced" in gov["note"]


def test_f1_within_when_the_drift_moves_nothing(s: Settings) -> None:
    arms = s.arms()
    rows = synthetic.rows(arms, flat_after_drift=True)
    ctx = synthetic.context(arms, s.forecasts())
    f = R.read_forecast("F1", ctx.forecasts["F1"], rows, ctx)
    assert all(x == "within" for x in f["verdict"].values())


# --- F4 latency, stale-applied (L11) ---------------------------------------------------------------------


def test_drift_latency_unresolved_is_unread(run: Any) -> None:
    rows, ctx = run
    f = R.read_forecast("F4", ctx.forecasts["F4"], rows, ctx)
    by = {r["name"]: r for r in f["readings"]}
    assert by["F4.ungated-governed"]["value"] == pytest.approx(90.0)   # 450 − 360
    assert f["verdict"]["F4.ungated-governed"] == "above"
    assert "held but unresolved" in by["F4.naive-governed"]["note"]    # naive never supersedes
    assert f["verdict"]["F4.naive-governed"] == "unread"                 # an unresolved arm is not a reading


def test_stale_applied_waits_label_horizon(run: Any) -> None:
    rows, ctx = run
    out = {r.name: r for r in R.stale_applied(rows, ctx, drift="D1", prefix="Q1")}
    naive = out["stale_applied.naive"]
    assert "idx ≥ 300" in naive.population and naive.value is not None and naive.value > 0.9
    late = R.stale_applied(rows, replace(ctx, label_horizon=400), drift="D1", prefix="Q1")
    pop = {r.name: r for r in late}["stale_applied.naive"].population
    assert pop.startswith("stream episodes of arm naive with idx ≥ 460")


def test_planted_readings_and_supersession_audit(run: Any) -> None:
    rows, ctx = run
    assert R.read_forecast("F2", ctx.forecasts["F2"], rows, ctx)["verdict"] == "agrees"
    assert R.read_forecast("F3", ctx.forecasts["F3"], rows, ctx)["verdict"] == "agrees"
    no_map = {**rows, "planted_map": []}
    assert R.read_forecast("F2", ctx.forecasts["F2"], no_map, ctx)["verdict"] == "unread"
    audit = {r.name: r for r in R.supersession_audit(rows, ctx)}
    assert audit["supersession_audit.governed"].value == 1 and audit["supersession_audit.governed"].note is None


def test_backtest_premise_reading(run: Any) -> None:
    rows, ctx = run
    out = {r.name: r for r in R.backtest_summary(rows, ctx)}
    p = out["backtest.premise.governed"]
    assert p.n > 0 and 0.0 <= p.value <= 1.0 and "§ 12 premise" in p.note


# --- manifest and report -------------------------------------------------------------------------------


def test_every_figure_has_a_query_and_n(run: Any, s: Settings) -> None:
    rows, ctx = run
    arms = s.arms()
    readings = R.all_readings(rows, ctx, spend=synthetic.spend(arms), priced=s.model_prices_usd_per_mtok)
    m = rep.manifest(readings, ctx.run_id)["figures"]
    names = {r["name"] for r in readings["readings"]} | {
        f"forecast.{f['id']}.{r['name']}" for f in readings["forecasts"] for r in f["readings"]}
    names |= {f"curve.accuracy.{a}" for a in readings["curves"]}
    assert names <= set(m)
    for fig, entry in m.items():
        assert entry["query"], fig
        assert isinstance(entry["n"], int), fig
    for r in readings["readings"]:
        assert {"value", "unit", "population", "n", "query"} <= set(r), r["name"]


def test_report_prints_each_forecast_beside_its_reading(run: Any, s: Settings) -> None:
    rows, ctx = run
    readings = R.all_readings(rows, ctx)
    md = rep.markdown(readings, {"started_at": "t", "knobs": {"a": 1}}, against={"_id": "other", "knobs": {"a": 2}})
    for fid in ctx.forecasts:
        assert f"### {fid}" in md
    assert "**Verdict**" in md and "| a | 1 | 2 |" in md
    page = rep.html_report(readings, {}, chartjs_url=s.chartjs_url)
    assert s.chartjs_url in page and '"curves"' in page and "<script src" in page


def test_knob_diff_lists_only_moved_knobs() -> None:
    assert rep.knob_diff({"a": 1, "b": 2}, {"a": 1, "b": 3, "c": 0}) == [
        {"knob": "b", "this": 2, "other": 3}, {"knob": "c", "this": None, "other": 0}]


# --- run record --------------------------------------------------------------------------------------


def test_run_record_never_holds_a_secret(tmp_path: Any) -> None:
    s = Settings(_env_file=None, var_dir=tmp_path, mongodb_uri="mongodb+srv://u:PW-SECRET-1@x.example/",
                 anthropic_api_key="sk-ant-SECRET-2", voyage_api_key="pa-SECRET-3")
    rec = evidence.build_run_record(s, selection={"governed": {"store": "atlas"}}, capabilities={"x": 1},
                                    git=("abc", False), prompts=evidence.prompt_hashes(), pack_hash="h",
                                    world_counts={}, now=datetime.now(UTC))
    blob = json.dumps(rec.model_dump(mode="json", by_alias=True))
    assert "SECRET" not in blob and "PW-" not in blob
    assert rec.keys_present["anthropic_api_key"] and not rec.keys_present["typesafe_api_key"]
    assert rec.isolation == "convention"
    assert set(rec.forecast_register) == set(s.forecasts()) and rec.forecasts["F5"].startswith("on quirk")
    assert "planted_map" in rec.prompt_hashes and rec.models["proposer_model"] == s.proposer_model
    assert rec.auth_mode == "api_key"


def test_oauth_client_and_auth_mode_presence_only(tmp_path: Any) -> None:
    from munchhausen.impl.models_anthropic import client_kwargs

    ws = Settings(_env_file=None, var_dir=tmp_path, anthropic_api_key="sk-SECRET-5", anthropic_workspace_id="wrk-ID-6",
                  anthropic_auth_token="tok-SECRET-4")
    assert ws.anthropic_auth_mode() == "api_key_workspace"
    assert client_kwargs(ws)["default_headers"] == {"anthropic-workspace-id": "wrk-ID-6"}
    rec_ws = evidence.build_run_record(ws, selection={}, capabilities={}, git=(None, None), prompts={},
                                       pack_hash=None, world_counts={}, now=datetime.now(UTC))
    blob_ws = json.dumps(rec_ws.model_dump(mode="json", by_alias=True))
    assert "wrk-ID-6" not in blob_ws and "SECRET" not in blob_ws and rec_ws.keys_present["anthropic_workspace_id"]
    fb = Settings(_env_file=None, var_dir=tmp_path, anthropic_api_key="sk-SECRET-5", anthropic_auth_token="t")
    assert fb.anthropic_auth_mode() == "oauth_fallback" and client_kwargs(fb)["api_key"] is None
    s = Settings(_env_file=None, var_dir=tmp_path, anthropic_auth_token="tok-SECRET-4")
    kw = client_kwargs(s)
    assert kw["api_key"] is None and kw["default_headers"] == {"anthropic-beta": s.anthropic_oauth_beta}
    assert s.anthropic_auth_mode() == "oauth"
    rec = evidence.build_run_record(s, selection={}, capabilities={}, git=(None, None), prompts={}, pack_hash=None,
                                    world_counts={}, now=datetime.now(UTC))
    blob = json.dumps(rec.model_dump(mode="json", by_alias=True))
    assert rec.auth_mode == "oauth" and "SECRET" not in blob and rec.keys_present["anthropic_auth_token"]


def test_unavailable_model_is_visible_as_evidence(s: Settings) -> None:
    served = R.models_served(synthetic.spend(s.arms()))
    assert served["nominate"]["served"] == [] and served["nominate"]["failed"] == {"RateLimitError(429)": 10}
    rs = {r.name: r for r in R.models_served_readings(synthetic.spend(s.arms()))}
    assert "NO call answered" in rs["models.served.nominate"].note
    assert rs["models.served.propose"].value == ["claude-haiku-4-5"]


class _Runs:
    def __init__(self) -> None:
        self.rec: RunRecord | None = None
        self.merged: list[tuple[Any, ...]] = []

    async def get(self, run_id: str) -> RunRecord | None:
        return self.rec

    async def start(self, run: RunRecord) -> RunRecord:
        self.rec = self.rec or run
        return self.rec

    async def merge_round(self, *a: Any) -> None:
        self.merged.append(a)


def _harness(s: Settings, episodes: int = 0) -> Any:
    async def caps() -> dict[str, Any]:
        return {"server_version": "8.0"}

    async def count(run_id: str) -> int:
        return episodes

    store = SimpleNamespace(runs=_Runs(), capabilities=caps, evidence=SimpleNamespace(episode_count=count))

    def world() -> Any:
        raise RuntimeError("world not built")

    return SimpleNamespace(settings=s, store=store, selection=lambda: {"frozen": {}}, world=world,
                           shared=lambda port, name: JsonlTrace.create(name, s))


def test_start_run_is_idempotent_and_refuses_late_registration(s: Settings) -> None:
    h = _harness(s)
    first = asyncio.run(evidence.start_run(h))
    again = asyncio.run(evidence.start_run(h))
    assert first is again and first.pack_hash                  # pack file hash when the world is not built
    assert any(e["name"] == "run_start" for e in read_events(s.var_dir, s.run_id))
    with pytest.raises(evidence.PreRegistrationError):
        asyncio.run(evidence.start_run(_harness(s, episodes=3)))
    asyncio.run(evidence.close_round(h, "governed", 2, (60, 89)))
    assert h.store.runs.merged == [(s.run_id, "governed", 2, (60, 89))]


def test_round_pipeline_merges_into_rounds_on_its_unique_key() -> None:
    p = round_pipeline("r", "governed", 3, (90, 119))
    assert p[0] == {"$match": {"run_id": "r", "arm": "governed"}}
    assert p[-1]["$merge"]["into"] == "rounds" and p[-1]["$merge"]["on"] == ["run_id", "arm", "round"]


# --- shared call path and trace ------------------------------------------------------------------------


def test_spend_row_prices_tokens_and_records_failures(s: Settings) -> None:
    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=100_000, cache_read_input_tokens=0,
                            cache_creation_input_tokens=0)
    row = spend_row(s, stage="propose", arm="governed", model="claude-haiku-4-5", usage=usage, latency_ms=5,
                    system="sys", request_id="req_1")
    assert row.usd == pytest.approx(1.0 + 0.5) and row.ok and row.request_id == "req_1"
    assert row.meta == {"run_id": s.run_id, "arm": "governed", "stage": "propose", "model": "claude-haiku-4-5"}
    assert row.prompt_hash and len(row.prompt_hash) == 64
    bad = spend_row(s, stage="propose", arm="governed", model="unpriced-x", usage=None, latency_ms=5, system="",
                    error=TimeoutError())
    assert not bad.ok and bad.error == "TimeoutError" and bad.usd == 0.0 and bad.tokens_in == 0
    e429 = TimeoutError()
    e429.status_code = 429  # type: ignore[attr-defined]
    rl = spend_row(s, stage="nominate", arm="governed", model="claude-sonnet-5-5", usage=None, latency_ms=1,
                   system="", error=e429, served_model=None)
    assert rl.error == "TimeoutError(429)" and rl.meta["model"] == "claude-sonnet-5-5" and rl.served_model is None


def test_jsonl_trace_writes_one_line_per_event(s: Settings) -> None:
    t = JsonlTrace.create("jsonl", s)
    t.event("admission", {"arm": "governed", "idx": 90, "decision_id": "D-1"})
    t.event("not_in_catalog", {"arm": "governed"})
    rows = [json.loads(x) for x in events_path(s.var_dir, s.run_id).read_text().splitlines()]
    assert rows[0]["name"] == "admission" and rows[0]["run_id"] == s.run_id and rows[0]["decision_id"] == "D-1"
    assert "uncatalogued" not in rows[0] and rows[1]["uncatalogued"] is True
    assert "admission" in TRACE_EVENTS


def test_metrics_never_name_an_arm() -> None:
    """Readings iterate ArmSpecs; arm names live in conf/forecasts.yaml (the synthetic fixture's docstring
    and the forecasts aside)."""
    from pathlib import Path

    src = (Path(R.__file__)).read_text()
    for arm in ("governed", "naive", "ungated", "frozen", "self_ref"):
        assert f'"{arm}"' not in src and f"'{arm}'" not in src.replace("arm: '", "")
