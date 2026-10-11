"""Write-only sinks and the null signal source."""

from __future__ import annotations

import atexit
import json
import logging
import re
import sys
import threading
from collections import Counter
from collections.abc import Sequence
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Self

from munchhausen.config import Settings
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Shape
from munchhausen.domain.registers import EPISODE_OUTPUT, SIGNAL_AUTHORITY_CORRECTION, SIGNAL_CORRECT, catalogued
from munchhausen.impl._base import NoDeps

log = logging.getLogger(__name__)


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
        if not catalogued(name):
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


class TeeTrace:
    """Fan-out (`registry.FAN_OUT["trace"]`): forwards every call to each trace in selection order, e.g.
    `TRACE_IMPL=jsonl,raindrop`. Each trace keeps its own never-raise contract."""

    def __init__(self, traces: Sequence[Any]) -> None:
        self.traces = tuple(traces)

    def begin(self, episode: dict[str, Any]) -> None:
        for t in self.traces:
            t.begin(episode)

    def signal(self, name: str, value: Any, comment: str | None = None) -> None:
        for t in self.traces:
            t.signal(name, value, comment)

    def event(self, name: str, payload: dict[str, Any]) -> None:
        for t in self.traces:
            t.event(name, payload)

    def finish(self, output: Any) -> None:
        for t in self.traces:
            t.finish(output)


@dataclass
class _OpenEpisode:
    """The Raindrop interaction of the episode running in this context, and its proposer output so far."""

    interaction: Any
    event_id: str
    pipeline: Any = None
    confidence: Any = None


class RaindropTrace:
    """Trace → Raindrop (SPEC § 25.1), SDK `raindrop-ai` (`raindrop.analytics`). Write-only: nothing on the
    learning path reads it, and an SDK failure is logged and counted, never raised into the caller.

    - `begin` opens one interaction per episode (`user_id` = persona, `event_id` = episode id,
      `convo_id` = `<run_id>:<arm>`), held in a ContextVar so concurrent workers never cross.
      A payload without a persona is skipped (counted): there is no placeholder user.
    - `event(EPISODE_OUTPUT)` keeps the pipeline and confidence for `finish`; `finish` closes the interaction
      with the answer, the pipeline as a code attachment and the confidence as a property.
    - `signal` attaches `correct` (default, POSITIVE/NEGATIVE) and `authority_correction` (feedback, the
      authority's phrasing as comment) to the open episode.
    - `event` sends names matching RAINDROP_EVENTS as `track_ai` under the adjudicator user; scalars become
      properties, ids the input, the verdict/status the output, nested fields code attachments.
    Keys matching RAINDROP_REDACT_KEYS are dropped and secret-like strings replaced before anything is sent.
    """

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        key = settings.raindrop_write_key
        if key is None or not key.get_secret_value().strip():
            raise ValueError(f"trace {name!r} needs RAINDROP_WRITE_KEY, which is not set (the composition root "
                             "falls back to the null trace; construct it only with a key)")
        import raindrop.analytics as raindrop  # vendor SDK: optional extra `trace`

        return cls(raindrop, settings)

    def __init__(self, sdk: Any, settings: Settings) -> None:
        self._rd, self._s = sdk, settings
        self._secret = settings.raindrop_write_key.get_secret_value() if settings.raindrop_write_key else ""
        self._value_res = [re.compile(p) for p in settings.raindrop_redact_values]
        self._open: ContextVar[_OpenEpisode | None] = ContextVar(f"raindrop_episode_{id(self)}", default=None)
        self.counts: Counter[str] = Counter()
        self._lock = threading.Lock()
        self._enabled = False
        try:
            sdk.set_debug_logs(settings.raindrop_debug)
            sdk.init(self._secret, tracing_enabled=settings.raindrop_tracing)
            self._enabled = True
        except Exception as e:  # noqa: BLE001 - observability never takes the run down
            self._fail("init", e)
        atexit.register(self.shutdown)

    # --- the port -----------------------------------------------------------------------------------

    def begin(self, episode: dict[str, Any]) -> None:
        self._open.set(None)
        if not self._enabled:
            return
        persona = episode.get("persona")
        if not isinstance(persona, str) or not persona.strip():
            self._count("skipped_no_persona")
            return
        try:
            run_id = str(episode.get("run_id") or self._s.run_id)
            props = self._clean({k: episode[k] for k in self._s.raindrop_episode_properties if k in episode})
            interaction = self._rd.begin(
                user_id=persona, event=self._s.raindrop_episode_event, event_id=str(episode["episode_id"]),
                convo_id=f"{run_id}:{episode.get('arm', '')}", input=self._scrub(str(episode.get("text") or "")),
                properties=_scalars(props))
            self._open.set(_OpenEpisode(interaction=interaction, event_id=str(episode["episode_id"])))
            self._count("begun")
        except Exception as e:  # noqa: BLE001
            self._fail("begin", e)

    def finish(self, output: Any) -> None:
        cur = self._open.get()
        self._open.set(None)
        if cur is None:
            return
        try:
            attachments = []
            if cur.pipeline:
                attachments.append({"type": "code", "name": "pipeline", "role": "output", "language": "json",
                                    "value": self._scrub(_compact(self._clean_value(cur.pipeline)))})
            props = _scalars({"confidence": cur.confidence})
            kw: dict[str, Any] = {"output": self._scrub(output if isinstance(output, str) else _compact(output))}
            if props:
                kw["properties"] = props
            if attachments:
                kw["attachments"] = attachments
            cur.interaction.finish(**kw)
            self._count("finished")
        except Exception as e:  # noqa: BLE001
            self._fail("finish", e)

    def signal(self, name: str, value: Any, comment: str | None = None) -> None:
        cur = self._open.get()
        if cur is None:
            self._count("signal_without_episode")
            return
        try:
            if name == SIGNAL_CORRECT:
                self._rd.track_signal(event_id=cur.event_id, name=name, signal_type="default",
                                      sentiment="POSITIVE" if value else "NEGATIVE")
            elif name == SIGNAL_AUTHORITY_CORRECTION:
                if not comment or not comment.strip():
                    self._count("skipped_no_comment")   # a feedback signal needs the phrasing
                    return
                self._rd.track_signal(event_id=cur.event_id, name=name, signal_type="feedback",
                                      comment=self._scrub(comment), sentiment="NEGATIVE")
            else:
                self._rd.track_signal(event_id=cur.event_id, name=name, signal_type="default",
                                      properties=_scalars(self._clean({"value": value})))
            self._count(f"signal.{name}")
        except Exception as e:  # noqa: BLE001
            self._fail("signal", e)

    def event(self, name: str, payload: dict[str, Any]) -> None:
        if name == EPISODE_OUTPUT:
            cur = self._open.get()
            if cur is not None:
                cur.pipeline, cur.confidence = payload.get("pipeline"), payload.get("confidence")
            return
        if not self._enabled or not any(fnmatchcase(name, p) for p in self._s.raindrop_events):
            return
        try:
            clean = self._clean(dict(payload))
            run_id = str(clean.get("run_id") or self._s.run_id)
            arm = clean.get("arm")
            ids = {k: v for k, v in clean.items() if _is_id(k)}
            output = next((str(clean[f]) for f in self._s.raindrop_output_fields if clean.get(f) is not None), name)
            props = _scalars({**{k: v for k, v in clean.items() if not isinstance(v, list | dict)},
                              **{f"n_{k}": len(v) for k, v in clean.items() if isinstance(v, list)}})
            attachments = [{"type": "code", "name": k, "role": "context", "language": "json",
                            "value": self._scrub(_compact(v))}
                           for k, v in clean.items() if isinstance(v, list | dict) and v and not _is_id(k)]
            self._rd.track_ai(user_id=self._s.raindrop_adjudicator_user, event=name,
                              convo_id=f"{run_id}:{arm}" if arm else run_id, input=self._scrub(_compact(ids)),
                              output=self._scrub(output), properties=props, attachments=attachments or None)
            self._count(f"event.{name}")
        except Exception as e:  # noqa: BLE001
            self._fail("event", e)

    def shutdown(self) -> None:
        """Flush (registered with `atexit`); prints the counts so a run shows what reached Raindrop."""
        if not self._enabled:
            return
        self._enabled = False
        try:
            self._rd.shutdown()
        except Exception as e:  # noqa: BLE001
            self._fail("shutdown", e)
        print(f"[trace] raindrop: {dict(sorted(self.counts.items()))}", file=sys.stderr)

    # --- internals ----------------------------------------------------------------------------------

    def _count(self, what: str) -> None:
        with self._lock:
            self.counts[what] += 1

    def _fail(self, where: str, e: BaseException) -> None:
        self._count("errors")
        self._count(f"errors.{where}")
        log.warning("[trace] raindrop %s failed (%s): %s", where, type(e).__name__, self._scrub(str(e)))

    def _redacted_key(self, key: str) -> bool:
        k = key.lower()
        return any(fnmatchcase(k, p) for p in self._s.raindrop_redact_keys)

    def _clean(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {k: self._clean_value(v) for k, v in payload.items() if not self._redacted_key(str(k))}

    def _clean_value(self, v: Any) -> Any:
        if isinstance(v, dict):
            return self._clean(v)
        if isinstance(v, list | tuple | set | frozenset):
            return [self._clean_value(x) for x in v]
        if isinstance(v, str):
            return self._scrub(v)
        return v

    def _scrub(self, text: str) -> str:
        if self._secret and self._secret in text:
            text = text.replace(self._secret, self._s.raindrop_redacted)
        for rx in self._value_res:
            text = rx.sub(self._s.raindrop_redacted, text)
        return text


def _compact(v: Any) -> str:
    return json.dumps(v, default=str, separators=(",", ":"), sort_keys=True)


def _is_id(key: str) -> bool:
    return key == "id" or key.endswith(("_id", "_ids"))


def _scalars(d: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Raindrop properties take scalars only: None dropped, anything else as compact JSON."""
    out: dict[str, str | int | float | bool] = {}
    for k, v in d.items():
        if v is None:
            continue
        out[k] = v if isinstance(v, str | int | float | bool) else _compact(v)
    return out


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
