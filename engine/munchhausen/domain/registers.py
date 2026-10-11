"""Registers and supporting ledgers (SPEC § 10.1): runs, rounds, cursors, leases, tool access, terms, spend."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from munchhausen.domain.common import Value


class RunRecord(Value):
    id: str = Field(alias="_id")
    world: str
    pack: str
    seeds: dict[str, int]
    knobs: dict[str, Any]
    ports: dict[str, dict[str, str]]          # arm → port → implementation
    forecasts: dict[str, str]                 # pre-registered; never edited (§ 11)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    # --- M4 evidence (additive; corpus/EVIDENCE.md § 1). One-way doors: readers depend on these names.
    git_sha: str | None = None
    git_dirty: bool | None = None
    isolation: Literal["roles", "convention"] = "convention"   # roles iff every per-role URI is set
    models: dict[str, str] = Field(default_factory=dict)          # model knob → model id
    prompt_hashes: dict[str, str] = Field(default_factory=dict)   # party → sha256 of its prompt source
    pack_hash: str | None = None
    world_counts: dict[str, int] = Field(default_factory=dict)
    forecast_register: dict[str, dict[str, Any]] = Field(default_factory=dict)   # id → full forecast entry
    keys_present: dict[str, bool] = Field(default_factory=dict)  # presence only, never a value
    ended_at: datetime | None = None
    auth_mode: Literal["api_key", "oauth", "none"] = "none"      # which Anthropic credential (never its value)
    # stage → {requested, served, ok, failed{error: n}}, stamped by `finish_run` from `spend` (with ended_at)
    models_served: dict[str, dict[str, Any]] = Field(default_factory=dict)


class RoundRecord(Value):
    run_id: str
    arm: str
    round: int
    idx_range: tuple[int, int]
    acc_stream: float | None = None
    acc_self_assessed: float | None = None
    acc_v: float | None = None
    store_sizes: dict[str, int] = Field(default_factory=dict)
    admitted: int = 0
    refused: int = 0
    superseded: int = 0
    retired: int = 0
    fires: dict[str, int] = Field(default_factory=dict)
    tokens_per_episode: float | None = None
    # --- M4 evidence (additive), written by the `$merge` at round close
    n_stream: int = 0
    calibration_gap: float | None = None      # acc_self_assessed − acc_stream (mean confidence − accuracy)
    moot: int = 0
    converged: int = 0
    view_filtered: int = 0                    # stream episodes whose view_map rewired a collection
    tokens_in: int = 0
    tokens_out: int = 0
    usd: float = 0.0
    usd_per_episode: float | None = None
    usd_cum: float = 0.0                      # the arm's spend at round close (usd = usd_cum − previous usd_cum)
    closed_at: datetime | None = None


class Cursor(Value):
    run_id: str
    arm: str
    next_idx: int = 0
    round: int = 0
    resume_tokens: dict[str, Any] = Field(default_factory=dict)   # change-stream consumer → token


class Lease(Value):
    run_id: str
    arm: str
    idx: int
    worker: str
    expires_at: datetime


class ToolAccess(Value):
    """One rewired mapping: logical collection → view, owned by a floor decision (SPEC § 8)."""

    run_id: str
    arm: str
    logical: str
    view: str
    decision_id: str


class Term(Value):
    term: str
    aliases: tuple[str, ...] = ()
    source: Literal["schema", "question", "authority", "nominator"]
    admitted_at_idx: int
    decision_id: str | None = None


class SpendRow(Value):
    at: datetime
    meta: dict[str, str]          # {arm, stage, model}
    tokens_in: int
    tokens_out: int
    latency_ms: int
    usd: float
    # --- M4 evidence (additive). meta = {run_id, arm, stage, model}. A failed call is a row too.
    tokens_cache_read: int = 0
    tokens_cache_write: int = 0
    prompt_hash: str | None = None             # sha256 of the system prompt
    request_id: str | None = None
    ok: bool = True
    error: str | None = None                   # exception class (+ HTTP status) when ok is False
    served_model: str | None = None            # the model id the API reports it served (`message.model`)


class PlantedMapping(Value):
    """Evaluation-only planted-truth map (SPEC § 11): one admitted decision → a quirk id or none."""

    id: str = Field(alias="_id")              # PM-<decision_id>
    run_id: str
    arm: str
    decision_id: str
    quirk: str | None
    scope: Literal["org", "persona"]          # persona iff the hook carries a persona scope
    model: str
    at: datetime


# Trace event catalog (corpus/EVIDENCE.md § 3). `Trace.event(name, payload)`: `name` from this set,
# `payload` = {arm, idx?, <ids>…}. An unknown name is still written, flagged `uncatalogued: true`.
TRACE_EVENTS: frozenset[str] = frozenset({
    "episode", "consultation", "guard_refusal", "observation", "shape", "bar", "draft", "layer", "backtest",
    "admission", "supersession", "moot", "retire", "view_rewire", "fire", "fire_disposed", "owner_override",
    "round_close", "run_start", "run_finish",
})
