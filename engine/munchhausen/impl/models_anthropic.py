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
from munchhausen.impl import parties
from munchhausen.impl._base import key
from munchhausen.impl.parties import lesson, nominator, observer, planted_map, proposer, self_grade  # noqa: F401
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

        self.client = AsyncAnthropic(api_key=key(settings, "anthropic_api_key"),
                                      max_retries=settings.model_max_retries)
        self._s = settings
        self._spend = spend

    # --- port methods: each delegates to its party module (impl/parties/) ---------------------------

    async def propose(self, inp: ProposerInput) -> Proposal:
        return await parties.proposer.run(self, self._s, inp)

    async def observe(self, episode: Episode) -> list[ObservationNote]:
        return await parties.observer.run(self, self._s, episode)

    async def nominate(self, inp: NominatorInput) -> tuple[EntryContract, tuple[str, ...]]:
        return await parties.nominator.run(self, self._s, inp)

    async def lesson(self, episode: Episode, observation: Observation) -> Lesson:
        return await parties.lesson.run(self, self._s, episode, observation)

    async def self_grade(self, episode: Episode) -> SelfGrade:
        return await parties.self_grade.run(self, self._s, episode)

    async def planted_map(self, decision: Decision, pack_definitions: str) -> str | None:
        return await parties.planted_map.run(self, self._s, decision, pack_definitions)

    # --- shared call path --------------------------------------------------------------------------

    async def parse(self, *, stage: str, arm: str, model: str, system: str, user: str, wire: type[W],
                     effort: str | None = None, max_tokens: int = 16000) -> W:
        kwargs: dict[str, Any] = {}
        if effort:
            kwargs["output_config"] = {"effort": effort}
        t0 = time.monotonic()
        msg = await self.client.messages.parse(
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

    async def record_call(self, *, stage: str, arm: str, model: str, usage: Any, latency_ms: int,
                          system: str = "", request_id: str | None = None) -> None:
        if self._spend is not None:
            await self._spend.record(SpendRow(
                at=datetime.now(UTC), meta={"arm": arm, "stage": stage, "model": model},
                tokens_in=usage.input_tokens, tokens_out=usage.output_tokens, latency_ms=latency_ms, usd=0.0))
