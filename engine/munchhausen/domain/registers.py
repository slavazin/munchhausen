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
