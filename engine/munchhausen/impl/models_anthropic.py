"""Models port over the Anthropic SDK (SPEC § 3, § 21).

Wire schemas (what the model is asked to emit) are defined here and mapped to domain objects, so a
provider's structured-output constraints never shape the domain. Structured output uses
`client.messages.parse(output_format=...)`; no forced `tool_choice` (rejected on 5.5 models).
Effort is sent only where configured — Haiku 4.5 rejects `effort`.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
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

        self.client = AsyncAnthropic(**client_kwargs(settings))
        self._s = settings
        self._spend = spend
        self.lost_spend_writes = 0          # stamped in `runs` by `evidence.finish_run`

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
                     effort: str | None = None, max_tokens: int = 16000, temperature: float | None = None) -> W:
        """One structured call. Every call writes a `spend` row — a failed call too (`ok=False`, the
        exception class), so failures are evidence. With `RESPONSE_CACHE`, a hit returns the stored parsed
        output and writes a zero-token row with `request_id="cache"` (trace-invariance replay, SPEC § 21).
        `temperature` is sent as `extra_body` only when set (some models reject it)."""
        cache = (self._cache_path(model, system, user, wire, arm=arm, effort=effort, max_tokens=max_tokens,
                                  temperature=temperature) if self._s.response_cache else None)
        if cache is not None and cache.exists():
            out = wire.model_validate_json(cache.read_text())
            await self._record(stage=stage, arm=arm, model=model, usage=None, latency_ms=0, system=system,
                               request_id="cache")
            return out
        kwargs: dict[str, Any] = {}
        if effort:
            kwargs["output_config"] = {"effort": effort}
        if temperature is not None:
            kwargs["extra_body"] = {"temperature": temperature}
        t0 = time.monotonic()
        try:
            msg = await self.client.messages.parse(
                model=model, max_tokens=max_tokens, system=system,
                messages=[{"role": "user", "content": user}], output_format=wire, **kwargs)
        except Exception as e:
            await self._record(stage=stage, arm=arm, model=model, usage=None,
                               latency_ms=int((time.monotonic() - t0) * 1000), system=system, error=e)
            raise
        latency = int((time.monotonic() - t0) * 1000)
        request_id = getattr(msg, "_request_id", None)
        if msg.stop_reason == "refusal" or msg.parsed_output is None:
            err = RuntimeError(f"{stage}: no parsed output (stop_reason={msg.stop_reason})")
            await self._record(stage=stage, arm=arm, model=model, usage=msg.usage, latency_ms=latency,
                               system=system, request_id=request_id, error=err)
            raise err
        await self._record(stage=stage, arm=arm, model=model, usage=msg.usage, latency_ms=latency, system=system,
                           request_id=request_id, served_model=getattr(msg, "model", None))
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            tmp = cache.with_suffix(f".{os.getpid()}.tmp")
            tmp.write_text(msg.parsed_output.model_dump_json())
            os.replace(tmp, cache)                          # atomic: a reader never sees a partial file
        return msg.parsed_output

    async def record_call(self, *, stage: str, arm: str, model: str, usage: Any, latency_ms: int,
                          system: str = "", request_id: str | None = None, served_model: str | None = None) -> None:
        await self._record(stage=stage, arm=arm, model=model, usage=usage, latency_ms=latency_ms, system=system,
                           request_id=request_id, served_model=served_model)

    async def record_error(self, *, stage: str, arm: str, model: str, error: BaseException, latency_ms: int,
                           system: str = "") -> None:
        """For parties that call `client` directly: record a failed call like `parse` does."""
        await self._record(stage=stage, arm=arm, model=model, usage=None, latency_ms=latency_ms, system=system,
                           error=error)

    async def _record(self, *, stage: str, arm: str, model: str, usage: Any, latency_ms: int, system: str,
                      request_id: str | None = None, error: BaseException | None = None,
                      served_model: str | None = None) -> None:
        if self._spend is None:
            return
        row = spend_row(self._s, stage=stage, arm=arm, model=model, usage=usage, latency_ms=latency_ms,
                        system=system, request_id=request_id, error=error, served_model=served_model,
                        episode_id=current_episode_id())
        try:
            await self._spend.record(row)
        except Exception as e:   # a lost spend row must not fail the episode; it is counted and stamped in `runs`
            self.lost_spend_writes += 1
            print(f"[spend] row not written ({type(e).__name__}): {stage} {arm} {model}", file=sys.stderr)

    def _cache_path(self, model: str, system: str, user: str, wire: type[BaseModel], *, arm: str,
                    effort: str | None, max_tokens: int, temperature: float | None) -> Path:
        parts = (model, wire.__name__, arm, str(effort), str(max_tokens), str(temperature), system, user)
        h = hashlib.sha256("\x1f".join(parts).encode()).hexdigest()
        return self._s.var_dir / "cache" / f"{h}.json"


def current_episode_id() -> str | None:
    """The episode a call belongs to, from the `ContextVar` named `current_episode_id` that the forward pass
    sets (S2). Found by name so this module depends on no loop module; None outside an episode."""
    for var, value in contextvars.copy_context().items():
        if var.name == "current_episode_id":
            return str(value) if value is not None else None
    return None


def client_kwargs(settings: Settings) -> dict[str, Any]:
    """Per `Settings.anthropic_auth_mode()`: an API key with its workspace header; else the OAuth token with its
    beta header (`ANTHROPIC_OAUTH_BETA`), also when a key is present without a workspace id (recorded as
    `oauth_fallback` in `runs`); else the bare key."""
    mode = settings.anthropic_auth_mode()
    if mode == "api_key_workspace":
        return {"api_key": key(settings, "anthropic_api_key"),
                "default_headers": {"anthropic-workspace-id": settings.anthropic_workspace_id},
                "max_retries": settings.model_max_retries}
    if mode in ("oauth", "oauth_fallback"):
        return {"api_key": None, "auth_token": key(settings, "anthropic_auth_token"),
                "default_headers": {"anthropic-beta": settings.anthropic_oauth_beta},
                "max_retries": settings.model_max_retries}
    return {"api_key": key(settings, "anthropic_api_key"), "max_retries": settings.model_max_retries}


def error_label(error: BaseException) -> str:
    """Exception class, plus the HTTP status when the SDK carries one (e.g. `RateLimitError(429)`)."""
    status = getattr(error, "status_code", None)
    return f"{type(error).__name__}({status})" if status is not None else type(error).__name__


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def spend_row(settings: Settings, *, stage: str, arm: str, model: str, usage: Any, latency_ms: int, system: str,
              request_id: str | None = None, error: BaseException | None = None,
              served_model: str | None = None, episode_id: str | None = None) -> SpendRow:
    """The `spend` row of one call (pure): tokens incl. cache, list-price USD, prompt hash, request id.
    `meta.episode_id` is set when the call ran inside an episode (rounds attribute tokens through it)."""
    t_in = int(getattr(usage, "input_tokens", 0) or 0)
    t_out = int(getattr(usage, "output_tokens", 0) or 0)
    c_read = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
    c_write = int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
    return SpendRow(
        at=datetime.now(UTC),
        meta={"run_id": settings.run_id, "arm": arm, "stage": stage, "model": model,
              **({"episode_id": episode_id} if episode_id else {})},
        tokens_in=t_in, tokens_out=t_out, latency_ms=latency_ms,
        usd=settings.usd(model, t_in, t_out, c_read, c_write),
        tokens_cache_read=c_read, tokens_cache_write=c_write,
        prompt_hash=sha256(system) if system else None, request_id=request_id,
        ok=error is None, error=error_label(error) if error is not None else None,
        served_model=served_model if error is None else None)
