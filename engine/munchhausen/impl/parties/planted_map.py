"""Planted-truth judge party (SPEC § 11), evaluation only. Owner: telemetry/metrics surface (M4)."""

from __future__ import annotations

from munchhausen.config import Settings
from munchhausen.domain.decision import Decision
from munchhausen.impl.parties import LLM


async def run(llm: LLM, settings: Settings, decision: Decision, pack_definitions: str) -> str | None:
    raise NotImplementedError("M4: evaluation-only planted-truth judge")
