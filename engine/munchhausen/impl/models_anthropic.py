"""Models port over the Anthropic SDK (SPEC § 3, § 21).

Wire schemas (what the model is asked to emit) are defined here and mapped to domain objects, so a
provider's structured-output constraints never shape the domain. Structured output uses
`client.messages.parse(output_format=...)`; no forced `tool_choice` (rejected on 5.5 models).
Effort is sent only where configured — Haiku 4.5 rejects `effort`.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Any, Self, TypeVar

from pydantic import BaseModel, Field

from munchhausen.config import Settings
from munchhausen.domain.decision import Decision, EntryContract
from munchhausen.domain.episode import Consultation, Episode, Proposal
from munchhausen.domain.lesson import Lesson
from munchhausen.domain.observation import Observation, ObservationNote
from munchhausen.domain.registers import SpendRow
from munchhausen.impl._base import key
from munchhausen.ports.models import NominatorInput, ProposerInput, SelfGrade
from munchhausen.ports.store import SpendRepository

W = TypeVar("W", bound=BaseModel)


class ProposalWire(BaseModel):
    """Pipeline travels as a JSON string: arbitrary-key objects don't fit strict structured output."""

    collection: str
    pipeline_json: str = Field(description="The aggregation pipeline as a JSON array of stages")
    answer_path: str
    terms_used: list[str]
    consulted: list[Consultation]
    anomalies: list[str]
    confidence: float
    rationale: str

    def to_domain(self) -> Proposal:
        return Proposal(collection=self.collection, pipeline=json.loads(self.pipeline_json),
                        answer_path=self.answer_path, terms_used=tuple(self.terms_used),
                        consulted=tuple(self.consulted), anomalies=tuple(self.anomalies),
                        confidence=min(max(self.confidence, 0.0), 1.0), rationale=self.rationale)


class AnthropicModels:
    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(settings, store.spend if store is not None else None)

    def __init__(self, settings: Settings, spend: SpendRepository | None = None) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=key(settings, "anthropic_api_key"),
                                      max_retries=settings.model_max_retries)
        self._s = settings
        self._spend = spend

    async def propose(self, inp: ProposerInput) -> Proposal:
        raise NotImplementedError("M2: proposer prompt (consultation language, § 22.6) → ProposalWire")

    async def observe(self, episode: Episode) -> list[ObservationNote]:
        raise NotImplementedError("M3: observer prompt compiled from § 23.1")

    async def nominate(self, inp: NominatorInput) -> tuple[EntryContract, tuple[str, ...]]:
        raise NotImplementedError("M3: nominator with the read-only world tool; runs the prior option first")

    async def lesson(self, episode: Episode, observation: Observation) -> Lesson:
        raise NotImplementedError("M3: naive lesson writer (NAIVE_LESSON_MODEL) → Lesson")

    async def self_grade(self, episode: Episode) -> SelfGrade:
        raise NotImplementedError("M3: self_ref self-grade as 'the subject-matter expert'")

    async def planted_map(self, decision: Decision, pack_definitions: str) -> str | None:
        raise NotImplementedError("M4: evaluation-only planted-truth judge")

    # --- shared call path --------------------------------------------------------------------------

    async def _parse(self, *, stage: str, arm: str, model: str, system: str, user: str, wire: type[W],
                     effort: str | None = None, max_tokens: int = 16000) -> W:
        kwargs: dict[str, Any] = {}
        if effort:
            kwargs["output_config"] = {"effort": effort}
        t0 = time.monotonic()
        msg = await self._client.messages.parse(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}], output_format=wire, **kwargs)
        if msg.stop_reason == "refusal" or msg.parsed_output is None:
            raise RuntimeError(f"{stage}: no parsed output (stop_reason={msg.stop_reason})")
        if self._spend is not None:
            await self._spend.record(SpendRow(
                at=datetime.now(UTC), meta={"arm": arm, "stage": stage, "model": model},
                tokens_in=msg.usage.input_tokens, tokens_out=msg.usage.output_tokens,
                latency_ms=int((time.monotonic() - t0) * 1000), usd=0.0))
        return msg.parsed_output
