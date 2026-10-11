"""A pipeline written as text by a model → stages the driver can run (pure; SPEC § 6.1).

- **Extended JSON dates** are the documented literal for a date (`{"$date": "2012-01-01T00:00:00Z"}`); plain
  `json.loads` leaves them as a one-key object, which never equals or orders against a stored date, so every
  date filter silently matched nothing. They decode to timezone-aware `datetime`s here. `$date` is never an
  aggregation operator, so the decode cannot change the meaning of a valid stage.
- **Lenient repair** runs only when the strict parse fails: shell-style constructors (`new Date("…")`,
  `ISODate("…")`, `NumberInt(…)`, `NumberLong(…)`) and trailing commas. Each rewrite applied is returned by
  name, so the episode records that its pipeline was repaired rather than written as valid JSON.

Residue: repair rewrites syntax, never semantics; a pipeline that still does not parse stays unparsed.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from munchhausen.domain.common import Pipeline

# name → (pattern, replacement). Order matters: constructors before trailing commas.
REPAIRS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("js_date", re.compile(r"""\b(?:new\s+)?(?:ISODate|Date)\(\s*(["'])([^"']*)\1\s*\)"""), r'{"$date": "\2"}'),
    ("js_number", re.compile(r"""\b(?:NumberInt|NumberLong)\(\s*(["']?)(-?\d+)\1\s*\)"""), r"\2"),
    ("trailing_comma", re.compile(r",\s*([\]}])"), r"\1"),
)


def parse_pipeline(raw: str) -> tuple[Pipeline | None, tuple[str, ...]]:
    """(stages, repairs applied). Stages are None when the text is not a pipeline even after repair."""
    repairs: list[str] = []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        text = raw
        for name, pattern, replacement in REPAIRS:
            text, n = pattern.subn(replacement, text)
            if n:
                repairs.append(name)
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return None, tuple(repairs)
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(s, dict) for s in value):
        return None, tuple(repairs)
    return decode_dates(value), tuple(repairs)


def decode_dates(node: Any) -> Any:
    """Every Extended JSON `{"$date": …}` → an aware `datetime` (UTC when the text names no offset)."""
    if isinstance(node, dict):
        if len(node) == 1 and "$date" in node:
            when = _date(node["$date"])
            if when is not None:
                return when
        return {k: decode_dates(v) for k, v in node.items()}
    if isinstance(node, list):
        return [decode_dates(v) for v in node]
    return node


def _date(v: Any) -> datetime | None:
    if isinstance(v, dict) and set(v) == {"$numberLong"}:
        v = v["$numberLong"]
        try:
            v = int(v)
        except (TypeError, ValueError):
            return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return datetime.fromtimestamp(v / 1000, tz=UTC)
    if isinstance(v, str):
        try:
            when = datetime.fromisoformat(v.strip())
        except ValueError:
            return None
        return when if when.tzinfo else when.replace(tzinfo=UTC)
    return None
