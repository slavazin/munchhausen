"""A synthetic run (rows shaped like `EvidenceRepository.snapshot`) for tests and the `report-demo` command.

Not evidence of anything: it exists so the report is demonstrable and testable before a real run. Every
report rendered from it is labelled SYNTHETIC. The story it plants mirrors SPEC § 13: each learning arm admits
a Q1 decision before D1; at D1 the Q1 definition moves; the governed-shape arm fires and supersedes at
`resolve_at`, the ungated-shape arm later, the naive-shape arm never; confidence stays flat throughout.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from munchhausen.domain.arm import ArmSpec
from munchhausen.metrics.readings import Context

TEMPLATES = {"t_q1_a": "Q1_active_customer", "t_q1_b": "Q1_active_customer", "t_q3": "Q3_soft_delete"}
CONTROLS = ("t_ctrl_a", "t_ctrl_b")


def context(arms: Mapping[str, ArmSpec], forecasts: Mapping[str, Mapping[str, Any]], *, run_id: str = "synthetic",
            run_length: int = 600, d1_at: int = 300, round_size: int = 30) -> Context:
    return Context(run_id=run_id, arms=dict(arms), round_size=round_size, run_length=run_length,
                   drift_at={"D1": d1_at}, drift_quirk={"D1": "Q1_active_customer"}, template_quirk=dict(TEMPLATES),
                   label_horizon=150, drift_window=150, bootstrap_n=500, ci_level=0.90, seed=17,
                   premise_first=10, premise_share=0.5, forecasts=dict(forecasts))


def _plan(spec: ArmSpec, last_episodic: bool) -> dict[str, Any]:
    """Per arm, from its spec (never its name): Q1 decision admitted at, resolved (superseded) at, and the
    accuracy gain on other quirks. Direct writers never resolve; episodic writers do, the last one listed
    first (in conf/arms.yaml that is the governed arm)."""
    wp = spec.write_path.value
    if wp == "direct":
        return {"q1_at": 60, "resolve_at": None, "learn": 0.55, "direct": True}
    if wp == "episodic":
        return {"q1_at": 90, "resolve_at": 360 if last_episodic else 450, "learn": 0.75 if last_episodic else 0.6,
                "direct": False}
    if wp == "self_grade":
        return {"q1_at": None, "resolve_at": None, "learn": 0.1, "direct": False}
    return {"q1_at": None, "resolve_at": None, "learn": 0.0, "direct": False}


def rows(arms: Mapping[str, ArmSpec], *, run_id: str = "synthetic", run_length: int = 600, d1_at: int = 300,
         round_size: int = 30, seed: int = 3, flat_after_drift: bool = False) -> dict[str, list[dict[str, Any]]]:
    rng = np.random.default_rng(seed)
    templates = [*TEMPLATES, *CONTROLS]
    weights = np.array([0.25, 0.2, 0.2, 0.2, 0.15])
    draws = rng.choice(len(templates), size=run_length, p=weights / weights.sum())
    u = rng.random((len(arms), run_length))
    out: dict[str, list[dict[str, Any]]] = {k: [] for k in ("episodes", "decisions", "fires", "backtests", "drafts",
                                                            "rounds", "planted_map")}
    episodic = [a for a, s in arms.items() if s.write_path.value == "episodic"]
    for k, arm in enumerate(arms):
        p = _plan(arms[arm], bool(episodic) and arm == episodic[-1])
        q1_at, resolve_at = p["q1_at"], p["resolve_at"]
        d_old, d_new, d_q3 = f"D-{arm}-q1", f"D-{arm}-q1b", f"D-{arm}-q3"
        for i in range(run_length):
            t = templates[draws[i]]
            quirk = TEMPLATES.get(t)
            consulted: list[dict[str, str]] = []
            if quirk is None:
                pc = 0.85
            elif quirk.startswith("Q1"):
                holds_old = q1_at is not None and i >= q1_at and (resolve_at is None or i < resolve_at)
                holds_new = resolve_at is not None and i >= resolve_at
                if holds_old:
                    consulted = [{"decision_id": d_old, "disposition": "applied"}]
                    pc = 0.9 if (i < d1_at or flat_after_drift) else 0.1
                elif holds_new:
                    consulted = [{"decision_id": d_new, "disposition": "applied"}]
                    pc = 0.9
                else:
                    pc = 0.2 if (i < d1_at or flat_after_drift) else 0.15
            else:
                pc = 0.25 + (p["learn"] if i >= 150 else 0.0)
                if p["learn"] and i >= 150:
                    consulted = [{"decision_id": d_q3, "disposition": "applied"}]
            out["episodes"].append({
                "_id": f"{run_id}:{arm}:e{i}", "run_id": run_id, "arm": arm, "idx": i, "stream": "stream",
                "question_id": f"q{i}", "template": t, "persona": "analyst", "consulted": consulted,
                "view_map": {}, "confidence": 0.8, "correct": bool(u[k, i] < pc), "tokens": {"in": 900, "out": 120}})
        for at in range(75, run_length, 150):
            for j in range(20):
                out["episodes"].append({"_id": f"{run_id}:{arm}:v:{j}:{at}", "run_id": run_id, "arm": arm, "idx": at,
                                        "v_at": at, "stream": "v", "template": templates[j % 5], "confidence": 0.8,
                                        "correct": bool(rng.random() < 0.5 + 0.3 * p["learn"] * (at > 150)),
                                        "consulted": []})
        if q1_at is not None:
            out["decisions"].append(_decision(run_id, arm, d_old, q1_at, "superseded" if resolve_at else "admitted",
                                              resolve_at or q1_at, d_new if resolve_at else None))
            out["planted_map"].append(_map(run_id, arm, d_old, "Q1_active_customer"))
            if resolve_at is not None:
                out["decisions"].append(_decision(run_id, arm, d_new, resolve_at, "admitted", resolve_at, None))
                out["planted_map"].append(_map(run_id, arm, d_new, "Q1_active_customer"))
                fire_at = resolve_at - 30
                out["fires"].append({"_id": f"F-{arm}-1", "run_id": run_id, "arm": arm, "decision_id": d_old,
                                     "latch": f"T-{d_old}-1", "role": "dispositive", "cause": "residuals",
                                     "episode_ids": [], "disposition": "applied", "at_idx": fire_at})
        if p["learn"]:
            out["decisions"].append(_decision(run_id, arm, d_q3, 149, "admitted", 149, None))
            out["planted_map"].append(_map(run_id, arm, d_q3, "Q3_soft_delete"))
        if p["direct"]:   # the direct writer admits a poisoned figure and a one-person preference org-wide
            out["decisions"].append(_decision(run_id, arm, "D-naive-n1", 200, "admitted", 200, None))
            out["planted_map"].append(_map(run_id, arm, "D-naive-n1", "N1_poison"))
            out["decisions"].append(_decision(run_id, arm, "D-naive-p1", 230, "admitted", 230, None))
            out["planted_map"].append(_map(run_id, arm, "D-naive-p1", "P1_claire_rounding"))
        if arms[arm].write_path.value == "episodic":
            for b in range(12):
                sampled = [{"episode_id": f"{run_id}:{arm}:e{b * 30 + s}", "template": templates[s % 5],
                            "original_correct": s % 2 == 0, "baseline_correct": s % 3 == 0,
                            "replay_correct": (s % 3 == 0 and s != 6) or (s % 3 != 0 and (b + s) % 2 == 0),
                            "context": []} for s in range(8)]
                fixed = sum(1 for s in sampled if s["replay_correct"] and not s["baseline_correct"])
                broken = sum(1 for s in sampled if s["baseline_correct"] and not s["replay_correct"])
                out["drafts"].append({"_id": f"{run_id}:{arm}:r{b}:x", "run_id": run_id, "arm": arm, "round": b,
                                      "status": "admitted" if fixed >= 2 and broken <= 1 else "refused"})
                out["backtests"].append({"_id": f"BT-{arm}-{b}", "run_id": run_id, "arm": arm,
                                         "draft_id": f"{run_id}:{arm}:r{b}:x", "sampled": sampled, "fixed": fixed,
                                         "fixed_heldout": max(0, fixed - 1), "broken": broken,
                                         "verdict": "admit" if fixed >= 2 and broken <= 1 else "refuse"})
    return out


def _decision(run_id: str, arm: str, did: str, admitted: int, status: str, at_idx: int,
              by: str | None) -> dict[str, Any]:
    persona = None
    return {"_id": did, "run_id": run_id, "arm": arm, "title": f"synthetic {did}", "kind": "taxonomic",
            "admitted_at_idx": admitted,
            "latches": [{"type": "hook", "fires_when": {"terms": ["active customers"], "collections": [],
                                                        "persona": persona}, "not_this": []}],
            "lifecycle": {"status": status, "at_idx": at_idx, "superseded_by": by}}


def _map(run_id: str, arm: str, did: str, quirk: str | None) -> dict[str, Any]:
    return {"_id": f"PM-{did}", "run_id": run_id, "arm": arm, "decision_id": did, "quirk": quirk,
            "scope": "org", "model": "synthetic", "at": "1970-01-01T00:00:00Z"}


def observations(arms: Mapping[str, ArmSpec], *, run_length: int = 600, d1_at: int = 300, round_size: int = 30,
                 dim: int = 16, seed: int = 5) -> dict[str, list[dict[str, Any]]]:
    """E8 input rows `{round, idx, vector}`: before D1 observations stay near a few fixed directions; after D1
    a new direction appears (the drifting quirk's misses read differently)."""
    rng = np.random.default_rng(seed)
    base = rng.normal(size=(3, dim))
    new = rng.normal(size=dim)
    out: dict[str, list[dict[str, Any]]] = {}
    for arm, spec in arms.items():
        if spec.write_path.value != "episodic":
            continue
        rows = []
        for r in range(run_length // round_size):
            for j in range(4):
                centre = new if (r * round_size >= d1_at and j < 2) else base[j % 3]
                rows.append({"round": r, "idx": r * round_size + j,
                             "vector": (centre + 0.05 * rng.normal(size=dim)).tolist()})
        out[arm] = rows
    return out


def spend(arms: Mapping[str, ArmSpec], n: int = 600) -> list[dict[str, Any]]:
    out = []
    for arm in arms:
        out.append({"arm": arm, "stage": "propose", "model": "claude-haiku-4-5", "calls": n, "errors": 2,
                    "tokens_in": 900 * n, "tokens_out": 120 * n, "cache_read": 0, "cache_write": 0,
                    "usd": (900 * n * 1.0 + 120 * n * 5.0) / 1e6, "latency_ms_mean": 1400.0,
                    "served": ["claude-haiku-4-5"], "error_kinds": ["RateLimitError(429)"] * 2})
        if arms[arm].write_path.value == "episodic":   # an unavailable nominator model shows as evidence
            out.append({"arm": arm, "stage": "nominate", "model": "claude-sonnet-5-5", "calls": 5, "errors": 5,
                        "tokens_in": 0, "tokens_out": 0, "cache_read": 0, "cache_write": 0, "usd": 0.0,
                        "latency_ms_mean": 300.0, "served": [], "error_kinds": ["RateLimitError(429)"] * 5})
    return out
