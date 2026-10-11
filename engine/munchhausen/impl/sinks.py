"""Write-only sinks and the null signal source."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

from munchhausen.config import Settings
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Shape
from munchhausen.impl._base import NoDeps


class NullMemorySink(NoDeps):
    async def publish(self, decision: Decision) -> None:
        return None

    async def withdraw(self, decision_id: str, reason: str) -> None:
        return None


class NullTrace(NoDeps):
    def begin(self, episode: dict[str, Any]) -> None: ...

    def signal(self, name: str, value: Any, comment: str | None = None) -> None: ...

    def event(self, name: str, payload: dict[str, Any]) -> None: ...

    def finish(self, output: Any) -> None: ...


class JsonlTrace:
    """Append-only local trace under var/ — useful offline and as the Raindrop stand-in."""

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(settings.var_dir / f"trace-{settings.run_id}.jsonl")

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path

    def _write(self, kind: str, **fields: Any) -> None:
        row = {"at": datetime.now(UTC).isoformat(), "kind": kind, **fields}
        with self._path.open("a") as f:
            f.write(json.dumps(row, default=str) + "\n")

    def begin(self, episode: dict[str, Any]) -> None:
        self._write("begin", episode=episode)

    def signal(self, name: str, value: Any, comment: str | None = None) -> None:
        self._write("signal", name=name, value=value, comment=comment)

    def event(self, name: str, payload: dict[str, Any]) -> None:
        self._write("event", name=name, payload=payload)

    def finish(self, output: Any) -> None:
        self._write("finish", output=output)


class NoSignalSource(NoDeps):
    async def shapes(self, run_id: str, arm: str, since_idx: int) -> list[Shape]:
        return []
