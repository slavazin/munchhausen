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
    # which Anthropic credential the client used (never a value): api_key_workspace | oauth_fallback | oauth |
    # api_key | none (config.Settings.anthropic_auth_mode)
    auth_mode: str = "none"
    # stage → {requested, served, ok, failed{error: n}}, stamped by `finish_run` from `spend` (with ended_at)
    models_served: dict[str, dict[str, Any]] = Field(default_factory=dict)
    length: int | None = None                 # `run --length` at start (None: RUN_LENGTH)
    # one entry per resume that found something moved: {at, length, moved{field: {registered, current}}}
    resumes: list[dict[str, Any]] = Field(default_factory=list)
    lost_spend_writes: int = 0                # spend rows the call path could not write (stamped at finish)
    arm_specs: dict[str, dict[str, Any]] = Field(default_factory=dict)   # arm → ArmSpec as registered
    pack_file_hash: str | None = None         # sha256 of the pack file (`pack_hash` may be the World's own hash)


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
    tokens_in: int | None = None              # from `spend` rows attributed to the round's episodes; None: none
    tokens_out: int | None = None
    n_error: int = 0                          # stream episodes with `error`: excluded from accuracy and gap
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
    run_id: str | None = None                 # S2: the run this row is written for (seeding is per run)
    runs: dict[str, int] = Field(default_factory=dict)   # run key → admitted_at_idx in that run (`term_run_key`)


def term_run_key(run_id: str) -> str:
    """A run id as a field-safe key of `Term.runs` (Atlas paths treat '.' as nesting and '$' as an operator)."""
    return run_id.replace(".", "_").replace("$", "_")


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


class EmbeddingCacheRow(Value):
    """One cached embedding (`embedding_cache`). Run-independent: the key names the embedder, dimension and
    input type, so a changed embedder never reads another's vectors (SPEC § 24.1 E10). One-way door: `_id` =
    sha256 of the compact JSON array `[embedder_id, dim, input_type, text]` (`impl/voyage.embed_cache_key`)."""

    id: str = Field(alias="_id")
    embedder_id: str
    dim: int
    input_type: str
    text_hash: str                            # sha256 of the text
    vector: tuple[float, ...]
    at: datetime


class RerankCacheRow(Value):
    """One cached rerank (`rerank_cache`). `_id` = sha256 of the compact JSON array
    `[model, query, [sha256(doc)…], top_k]` (`impl/voyage.rerank_cache_key`). `indices`/`scores` are the
    result pairs in the order the reranker returned them (most relevant first)."""

    id: str = Field(alias="_id")
    model: str
    query_hash: str
    doc_hashes: tuple[str, ...]
    top_k: int | None
    indices: tuple[int, ...]
    scores: tuple[float, ...]
    at: datetime


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
    subject: Literal["decision", "draft"] = "decision"   # `decision_id` holds a draft id when subject is draft


# Trace event catalog (corpus/EVIDENCE.md § 3): the names the surfaces emit are canonical. `Trace.event(name,
# payload)` with `payload` = {arm, idx?, <ids>…}. An unknown name is still written, flagged `uncatalogued: true`.
# A name ending in `.failed` (`<stage>.failed`) and `lifecycle.<status>` are catalogued by prefix/suffix.
TRACE_EVENTS: frozenset[str] = frozenset({
    # forward pass and runner (S2)
    "episode", "consultation_set", "view_resolved", "guard_refusal", "proposal_failed", "episode_written",
    "episode_failed", "fire_raised", "round_closed",
    # shaping (S3)
    "observation.none", "observation.refused", "observation.written", "shape.formed", "shape.split",
    "shape.failed", "shape.windowed", "shape.refused", "bar.verdict", "bar.direction_read", "nominator.run",
    "nomination.failed", "draft.written", "draft.renominated", "draft.resumed", "draft.adjudicated",
    "draft.supersede_stripped",
    # adjudication and lifecycle (S4)
    "backward.round", "backward.unavailable", "adjudication", "adjudication.layer", "adjudication.failed",
    "backtest", "admission", "admission.failed", "lifecycle.superseded", "lifecycle.converged", "lifecycle.moot",
    "lifecycle.retired", "lifecycle.sweep", "lifecycle.status", "view.create", "view.drop", "tool_access.rewire",
    "fire.dispose", "owner.dispose", "direct.merge", "self_grade", "lensfit.label",
    # evidence (S5)
    "run_start", "run_finish",
})


def catalogued(name: str) -> bool:
    return (name in TRACE_EVENTS or name.endswith(".failed") or name.startswith(("lifecycle.", "injection."))
            or name == "signal")
