"""Write-only sinks and the null signal source."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

from munchhausen.config import Settings
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Shape
from munchhausen.domain.registers import TRACE_EVENTS
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
    """Append-only local trace: `var/runs/<run_id>/events.jsonl`, one line per event
    `{at, run_id, name, arm?, idx?, <ids>…}` (corpus/EVIDENCE.md § 3). Write-only: nothing on the learning path
    reads it (SPEC § 21 trace invariance), and a write failure never raises into the caller."""

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(events_path(settings.var_dir, settings.run_id), settings.run_id)

    def __init__(self, path: Path, run_id: str = "") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path, self._run_id = path, run_id

    def _write(self, name: str, fields: dict[str, Any]) -> None:
        row = {"at": datetime.now(UTC).isoformat(), "run_id": self._run_id, "name": name, **fields}
        if name not in TRACE_EVENTS:
            row["uncatalogued"] = True
        try:
            with self._path.open("a") as f:
                f.write(json.dumps(row, default=str) + "\n")
        except OSError as e:
            print(f"[trace] event not written ({type(e).__name__}): {name}", file=sys.stderr)

    def begin(self, episode: dict[str, Any]) -> None:
        self._write("episode", {"phase": "begin", **episode})

    def signal(self, name: str, value: Any, comment: str | None = None) -> None:
        self._write("signal", {"signal": name, "value": value, "comment": comment})

    def event(self, name: str, payload: dict[str, Any]) -> None:
        self._write(name, dict(payload))

    def finish(self, output: Any) -> None:
        self._write("episode", {"phase": "finish", "output": output})


def events_path(var_dir: Path, run_id: str) -> Path:
    return var_dir / "runs" / run_id / "events.jsonl"


def read_events(var_dir: Path, run_id: str) -> list[dict[str, Any]]:
    """For the report and the viewer only (evaluation side). Never called on the learning path."""
    p = events_path(var_dir, run_id)
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


class NoSignalSource(NoDeps):
    async def shapes(self, run_id: str, arm: str, since_idx: int) -> list[Shape]:
        return []
