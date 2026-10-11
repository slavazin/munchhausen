"""Write-only outward ports: MemorySink and Trace (SPEC § 21, § 25.1).

Nothing on the learning path reads either. Trace invariance: a run under any Trace writes
byte-identical `decisions` to the same run under `null`.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from munchhausen.domain.decision import Decision


@runtime_checkable
class MemorySink(Protocol):
    """Downstream memory product (e.g. Atlas Agent Engine). Called from lifecycle functions only."""

    async def publish(self, decision: Decision) -> None: ...

    async def withdraw(self, decision_id: str, reason: str) -> None: ...


@runtime_checkable
class Trace(Protocol):
    def begin(self, episode: dict[str, Any]) -> None: ...

    def signal(self, name: str, value: Any, comment: str | None = None) -> None: ...

    def event(self, name: str, payload: dict[str, Any]) -> None: ...

    def finish(self, output: Any) -> None: ...
