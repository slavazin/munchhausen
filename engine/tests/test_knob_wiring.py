"""Every backward collaborator `bootstrap_learn` builds carries its knobs.

Each relevant knob is set to a sentinel that differs from its default; every arm's collaborators are built
through `bootstrap_learn`; each object must carry the sentinel. Two reads: an explicit table (field → knob,
including renamed fields such as `Backtester.n ← BACKTEST_N`), and a sweep that fails on any dataclass field
whose name is a knob but whose value is not that knob's (smoke-2: `EpisodicPass.direction_window` stayed at
its default and the direction read silently ran cumulative)."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from munchhausen import bootstrap_learn
from munchhausen.config import Settings
from munchhausen.domain.arm import WritePath
from munchhausen.ports import registry
from tests.test_adjudication_bootstrap import Harness as _BaseHarness
from tests.test_adjudication_bootstrap import _Rep, _Stub

SENTINELS: dict[str, Any] = {
    "round_size": 31, "carry_rounds": 7, "direction_window": 41, "holdout_templates": 2,
    "bar_min_templates_floor": 5, "stream_seed": 12, "neighbour_k": 6, "nominator_residual_window": 5,
    "embed_mask": "surfaces", "leak_min_abs": 11.5, "bar_min_obs": 3, "bar_min_templates": 3, "bar_min_gap": 0.11,
    "bar_min_matched": 11, "neighbour_rerank": 0.86, "l2_route_contested": True, "lens_mode": "gate",
    "lens_threshold": 0.51, "lens_explore_eps": 0.12, "world_seed": 8, "backtest_n": 9, "score_rel_tol": 2e-4,
    "execute_max_time_ms": 3001, "backtest_seed": 18, "backtest_concurrency": 5, "backtest_recent": 301,
    "backtest_holdout_share": 0.3, "backtest_min_fixed": 3, "backtest_min_fixed_heldout": 2,
    "backtest_max_broken": 2, "backtest_min_n": 5, "retire_idle": 299, "retire_fires": 7, "direct_merge": False,
    "naive_merge_cosine": 0.93, "workers_per_arm": 7, "lens_call_mode": "joint", "lens_phrasings": 2,
    "lens_max_concurrency": 6, "lens_model": "jev-x", "lens_timeout_s": 21.0,
}

# (collaborator key, attribute path) → knob, for fields whose name differs from the knob's
TABLE: dict[tuple[str, str], str] = {
    ("backtester", "n"): "backtest_n", ("backtester", "rel_tol"): "score_rel_tol",
    ("backtester", "max_time_ms"): "execute_max_time_ms", ("backtester", "seed"): "backtest_seed",
    ("backtester", "concurrency"): "backtest_concurrency", ("backtester", "recent"): "backtest_recent",
    ("backtester", "holdout_share"): "backtest_holdout_share",
    ("backtester", "thresholds.min_fixed"): "backtest_min_fixed",
    ("backtester", "thresholds.min_fixed_heldout"): "backtest_min_fixed_heldout",
    ("backtester", "thresholds.max_broken"): "backtest_max_broken",
    ("backtester", "thresholds.min_n"): "backtest_min_n",
    ("L0", "leak_min_abs"): "leak_min_abs",
    ("L1", "min_templates"): "bar_min_templates", ("L1", "min_templates_floor"): "bar_min_templates_floor",
    ("L2", "threshold"): "neighbour_rerank", ("L2", "route_contested"): "l2_route_contested",
    ("L3", "mode"): "lens_mode", ("L3", "threshold"): "lens_threshold", ("L3", "explore_eps"): "lens_explore_eps",
    ("L3", "seed"): "world_seed",
    ("lens_panel", "_mode"): "lens_call_mode", ("lens_panel", "_k"): "lens_phrasings",
    ("lens_panel", "_concurrency"): "lens_max_concurrency", ("lens_panel", "_model"): "lens_model",
    ("lens_panel", "_timeout"): "lens_timeout_s",
    ("lifecycle", "retire_idle"): "retire_idle", ("lifecycle", "retire_fires"): "retire_fires",
    ("direct_writer", "merge"): "direct_merge", ("direct_writer", "merge_cosine"): "naive_merge_cosine",
    ("direct_writer", "concurrency"): "workers_per_arm",
    ("observer", "embed_mask"): "embed_mask",
    ("nominator", "neighbour_k"): "neighbour_k", ("nominator", "residual_window"): "nominator_residual_window",
    ("episodic", "round_size"): "round_size", ("episodic", "carry_rounds"): "carry_rounds",
    ("episodic", "direction_window"): "direction_window", ("episodic", "holdout_templates"): "holdout_templates",
    ("episodic", "min_templates_floor"): "bar_min_templates_floor", ("episodic", "holdout_seed"): "stream_seed",
    ("episodic", "bar.min_obs"): "bar_min_obs", ("episodic", "bar.min_templates"): "bar_min_templates",
    ("episodic", "bar.min_gap"): "bar_min_gap", ("episodic", "bar.min_matched"): "bar_min_matched",
}


class Harness(_BaseHarness):
    def port(self, arm: str, port: str) -> Any:
        if port == "lens_panel":
            cache = self.ports.setdefault(arm, {})
            if "lens_panel" not in cache:
                cache["lens_panel"] = registry.resolve(port, self.arms[arm].ports[port]).create(
                    self.arms[arm].ports[port], self.settings, None)
            return cache["lens_panel"]
        return {"representation": _Rep(), "memory_sink": self.sink}.get(port, _Stub())


@pytest.fixture
def sentinel_settings(settings_offline: Settings) -> Settings:
    for k, v in SENTINELS.items():
        assert getattr(settings_offline, k) != v, f"sentinel for {k} equals its default"
    return settings_offline.model_copy(update=SENTINELS)


def _built(h: Harness, arm: str) -> dict[str, Any]:
    spec = h.arms[arm]
    out: dict[str, Any] = {}
    if spec.write_path is WritePath.NONE:
        return out
    curator = bootstrap_learn.curator_for(h, arm)
    out |= {layer.name if layer.name != "admit" else "admit": layer for layer in curator.layers}
    out["adjudicator"] = bootstrap_learn.adjudicator_for(h, arm)
    out["lifecycle"] = bootstrap_learn.lifecycle_for(h, arm)
    if "L4" in out:
        out["backtester"] = out["L4"].backtester
    if "L3" in out:
        out["lens_panel"] = out["L3"].panel
    if spec.write_path in bootstrap_learn.LESSON_PATHS:
        out["direct_writer"] = bootstrap_learn.direct_writer_for(h, arm)
    if spec.authority and spec.write_path is not WritePath.SELF_GRADE:
        deps = bootstrap_learn._deps(h, arm)
        out["observer"] = bootstrap_learn._collaborator(h, arm, "observer", "munchhausen.learn.observe",
                                                        "Observer", deps)
        if spec.write_path is WritePath.EPISODIC:
            deps["nominator"] = out["nominator"] = bootstrap_learn._collaborator(
                h, arm, "nominator", "munchhausen.learn.nominate", "Nominator", deps)
            from munchhausen.learn.episodic import EpisodicPass

            # built without `settings`: EpisodicPass's own fallback must not mask a knob the deps fail to carry
            out["episodic"] = bootstrap_learn._build(EpisodicPass, {k: v for k, v in deps.items() if k != "settings"})
    return out


def _get(obj: Any, path: str) -> Any:
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def test_every_backward_collaborator_carries_its_knobs(sentinel_settings: Settings) -> None:
    h = Harness(sentinel_settings)
    s = h.settings
    knobs = set(Settings.model_fields)
    misses: list[str] = []
    seen_keys: set[str] = set()
    checked: set[tuple[str, str]] = set()
    for arm in h.arms:
        built = _built(h, arm)
        seen_keys |= set(built)
        for (key, path), knob in TABLE.items():
            if key not in built or not hasattr(built[key], path.split(".")[0]):
                continue                   # e.g. L0 is `LessonShape` on the lesson write paths
            checked.add((key, path))
            if _get(built[key], path) != getattr(s, knob):
                misses.append(f"{arm}.{key}.{path} = {_get(built[key], path)!r}, want {knob}={getattr(s, knob)!r}")
        for key, obj in built.items():
            if not dataclasses.is_dataclass(obj):
                continue
            for f in dataclasses.fields(obj):
                if f.name in knobs and f.name not in ("trace", "world") and getattr(obj, f.name) != getattr(s, f.name):
                    misses.append(f"{arm}.{key}.{f.name} = {getattr(obj, f.name)!r}, knob {getattr(s, f.name)!r}")
    assert not misses, "knobs not wired:\n" + "\n".join(misses)
    expected = {"L0", "L1", "L2", "L3", "L4", "backtester", "lens_panel", "lifecycle", "adjudicator",
                "direct_writer", "observer", "nominator", "episodic"}
    assert expected <= seen_keys, f"not built: {expected - seen_keys}"
    assert checked == set(TABLE), f"table rows never read (a renamed field?): {set(TABLE) - checked}"
