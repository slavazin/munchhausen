"""One module per LLM party (SPEC § 21 `Models`): prompt, wire schema and domain mapping live together.

Each module exposes one `async def run(llm: LLM, settings: Settings, ...)`. `AnthropicModels` owns only the
shared call path (`LLM.parse`, `LLM.client`, spend/telemetry) and delegates every port method here, so
each party can change without touching the others.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

W = TypeVar("W", bound=BaseModel)


class LLM(Protocol):
    """The shared call path a party may use. `parse` records spend for every call."""

    client: Any   # anthropic.AsyncAnthropic, for parties that run a tool loop (the nominator's world tool)

    async def parse(self, *, stage: str, arm: str, model: str, system: str, user: str, wire: type[W],
                    effort: str | None = None, max_tokens: int = 16000, temperature: float | None = None) -> W: ...

    async def record_call(self, *, stage: str, arm: str, model: str, usage: Any, latency_ms: int,
                          system: str = "", request_id: str | None = None, served_model: str | None = None) -> None:
        """For parties that call `client` directly (tool loops): record the call like `parse` does."""
        ...

    async def record_error(self, *, stage: str, arm: str, model: str, error: BaseException, latency_ms: int,
                           system: str = "") -> None:
        """For parties that call `client` directly: record a failed call (failed calls are evidence)."""
        ...
