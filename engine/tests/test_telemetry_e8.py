"""E8 observation novelty (exploratory reading): the curve on synthetic vectors, the lead, the manifest entry."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from munchhausen.config import Settings
from munchhausen.metrics import readings as R
from munchhausen.metrics import report as rep
from munchhausen.metrics import synthetic


def test_novelty_curve_on_synthetic_vectors() -> None:
    obs = [{"round": 0, "idx": 0, "vector": [1.0, 0.0]},
           {"round": 1, "idx": 30, "vector": [1.0, 0.0]},          # identical to round 0: distance 0
           {"round": 1, "idx": 31, "vector": [0.0, 2.0]},          # orthogonal: distance 1
           {"round": 2, "idx": 60, "vector": [0.0, 1.0]}]          # matches round 1's second: distance 0
    c = R.novelty_curve(obs)
    assert [p["round"] for p in c] == [1, 2]                       # round 0 undefined
    assert c[0]["novelty"] == pytest.approx(0.5) and c[0]["n"] == 2 and c[0]["n_prior"] == 1
    assert c[1]["novelty"] == pytest.approx(0.0) and c[1]["n_prior"] == 3


@pytest.fixture
def setup(settings_offline: Settings) -> tuple[Any, Any, Any]:
    arms = settings_offline.arms()
    rows = synthetic.rows(arms)
    ctx = synthetic.context(arms, settings_offline.forecasts())
    return rows, ctx, synthetic.observations(arms)


def test_novelty_lead_reads_when_both_sides_exist(setup: Any) -> None:
    rows, ctx, obs = setup
    curve = R.novelty_curve(obs["governed"])
    r = R.novelty_lead(curve, rows, ctx, "governed", drift="D1", prefix="Q1")
    assert r.value is not None and "exploratory" in r.note        # alarm at round 10 (idx 329); fire at 330
    assert r.value == pytest.approx(330 - 329)


def test_novelty_lead_unread_without_a_fire_or_a_map(setup: Any) -> None:
    rows, ctx, obs = setup
    curve = R.novelty_curve(obs["governed"])
    no_fire = {**copy.deepcopy(rows), "fires": []}
    r = R.novelty_lead(curve, no_fire, ctx, "governed", drift="D1", prefix="Q1")
    assert r.value is None and "no dispositive fire" in r.note
    r = R.novelty_lead(curve, {**rows, "planted_map": []}, ctx, "governed", drift="D1", prefix="Q1")
    assert r.value is None and "no planted map" in r.note


def test_novelty_in_report_and_manifest(setup: Any) -> None:
    rows, ctx, obs = setup
    out = R.all_readings(rows, ctx, observations=obs)
    m = rep.manifest(out, ctx.run_id)["figures"]
    assert "curve.novelty.governed" in m and m["curve.novelty.governed"]["n"] > 0
    assert "E8.lead.governed" in m
    md = rep.markdown(out, {})
    assert "exploratory, not pre-registered" in md and "minimum cosine distance" in md
