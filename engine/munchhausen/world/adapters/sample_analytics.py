"""Adapter over the Atlas sample database `sample_analytics` (SPEC § 4.2).

Reads `customers`, `accounts`, `transactions` from the source database, applies the pack's materialize
transforms in pack order, and writes the result to `world`. Field names are opaque by design (§ 4.1 Don't).
Deterministic under WORLD_SEED: source docs are ordered by `_id` and every assignment is a `stable_bucket`.
"""

from __future__ import annotations

import re
from typing import Any, Self

from munchhausen.domain.question import SchemaSummary
from munchhausen.ports.store import DocumentReader, WorldWriter
from munchhausen.world.pack import Pack
from munchhausen.world.transforms import MATERIALIZE, Data

SOURCE_COLLECTIONS = ("customers", "accounts", "transactions")
_MAP_KEY = re.compile(r"^[0-9a-f]{16,}$")       # hex-keyed maps (e.g. per-tier detail objects) → `$key`


def bson_type(v: Any) -> str:
    """Python value → the BSON type name a query author would use."""
    names = {"str": "string", "int": "int", "float": "double", "bool": "bool", "datetime": "date",
             "NoneType": "null", "ObjectId": "objectId", "Decimal128": "decimal", "list": "array",
             "dict": "object"}
    return names.get(type(v).__name__, type(v).__name__)


def field_types(docs: list[dict[str, Any]], max_depth: int) -> dict[str, str]:
    """Dotted field paths → BSON type over a sample: subdocuments and arrays of subdocuments are walked
    (`transactions.symbol`), a non-null type wins over `null`, scalar arrays read `array<int>`."""
    out: dict[str, str] = {}

    def note(path: str, t: str) -> None:
        if path not in out or out[path] == "null":
            out[path] = t

    def walk(prefix: str, doc: dict[str, Any], depth: int) -> None:
        for k, v in doc.items():
            key = "$key" if _MAP_KEY.match(str(k)) else str(k)
            path = f"{prefix}{key}"
            if isinstance(v, dict):
                note(path, "object")
                if depth < max_depth:
                    walk(f"{path}.", v, depth + 1)
            elif isinstance(v, list):
                inner = next((x for x in v if x is not None), None)
                if isinstance(inner, dict):
                    note(path, "array<object>")
                    if depth < max_depth:
                        for x in v:
                            if isinstance(x, dict):
                                walk(f"{path}.", x, depth + 1)
                else:
                    note(path, f"array<{bson_type(inner)}>" if inner is not None else "array")
            else:
                note(path, bson_type(v))

    for d in docs:
        walk("", d, 0)
    return out


def field_values(docs: list[dict[str, Any]], max_depth: int) -> dict[str, list[Any]]:
    """Dotted field path → every scalar value seen in the sample, walked like `field_types`."""
    out: dict[str, list[Any]] = {}

    def walk(prefix: str, doc: dict[str, Any], depth: int) -> None:
        for k, v in doc.items():
            path = f"{prefix}{'$key' if _MAP_KEY.match(str(k)) else k}"
            items = v if isinstance(v, list) else [v]
            for x in items:
                if isinstance(x, dict):
                    if depth < max_depth:
                        walk(f"{path}.", x, depth + 1)
                elif x is not None and not isinstance(x, list):
                    out.setdefault(path, []).append(x)

    for d in docs:
        walk("", d, 0)
    return out


def field_notes(docs: list[dict[str, Any]], max_depth: int, *, value_fields: set[str], value_max: int,
                note_lowercase: bool) -> dict[str, str]:
    """Storage-fidelity notes per field path, never meanings: `values: a, b` for an allowlisted field with
    at most `value_max` distinct string values in the sample; else `lowercase` for a string field whose
    sampled values all hold letters and no capitals (string comparison is case-sensitive); `numbers stored
    as text` for a string field whose every sampled value parses as a number."""
    notes: dict[str, str] = {}
    for path, values in field_values(docs, max_depth).items():
        strings = [v for v in values if isinstance(v, str)]
        if not strings or len(strings) != len(values):
            continue
        distinct = sorted(set(strings))
        if path in value_fields and len(distinct) <= value_max:
            notes[path] = "values: " + ", ".join(distinct)
        elif all(_numeric(v) for v in distinct):
            notes[path] = "numbers stored as text"
        elif note_lowercase and all(any(c.isalpha() for c in v) and v == v.lower() for v in distinct):
            notes[path] = "lowercase"
    return notes


def _numeric(v: str) -> bool:
    try:
        float(v)
    except ValueError:
        return False
    return True


class SampleAnalyticsAdapter:
    name = "sample_analytics"

    @classmethod
    def create(cls, name: str, settings: Any, store: Any) -> Self:
        return cls(store.source(), store.world_builder(), settings.schema_sample_docs, settings.schema_max_depth,
                   settings.execute_max_time_ms, value_fields=tuple(settings.schema_value_fields),
                   value_max=settings.schema_value_max, note_lowercase=settings.schema_note_lowercase)

    def __init__(self, source: DocumentReader, world: WorldWriter, sample_docs: int, max_depth: int,
                 max_time_ms: int, *, value_fields: tuple[str, ...] = (), value_max: int = 0,
                 note_lowercase: bool = False) -> None:
        self._source, self._world = source, world
        self._sample_docs, self._max_depth, self._max_time_ms = sample_docs, max_depth, max_time_ms
        self._value_fields, self._value_max, self._note_lowercase = value_fields, value_max, note_lowercase

    async def read_source(self) -> Data:
        data: Data = {}
        for c in SOURCE_COLLECTIONS:
            docs = await self._source.find(c)
            data[c] = sorted(docs, key=lambda d: str(d.get("_id")))
        return data

    async def build(self, pack: Pack, seed: int) -> dict[str, int]:
        data = materialize_pack(await self.read_source(), pack, seed)
        empty = [c for c in SOURCE_COLLECTIONS if not data[c]]
        if empty:
            raise RuntimeError(f"source collections empty: {empty} (load the Atlas sample dataset)")
        return {c: await self._world.replace_collection(c, docs) for c, docs in data.items()}

    async def counts(self) -> dict[str, int]:
        out = {}
        for c in SOURCE_COLLECTIONS:
            rows = await self._world.aggregate(c, [{"$count": "n"}], max_time_ms=self._max_time_ms)
            out[c] = rows[0]["n"] if rows else 0
        return out

    async def schema_summary(self) -> SchemaSummary:
        """Field paths and BSON types, sampled from `world`, plus storage-fidelity notes; never meanings."""
        out, notes = {}, {}
        for c in SOURCE_COLLECTIONS:
            docs = await self._world.find(c, limit=self._sample_docs)
            out[c] = field_types(docs, self._max_depth)
            allow = {f.removeprefix(f"{c}.") for f in self._value_fields if f.startswith(f"{c}.")}
            if n := field_notes(docs, self._max_depth, value_fields=allow, value_max=self._value_max,
                                note_lowercase=self._note_lowercase):
                notes[c] = n
        return SchemaSummary(collections=out, notes=notes)


def materialize_pack(data: Data, pack: Pack, seed: int) -> Data:
    """Apply every quirk's materialize transform in pack order (pure; the adapter and tests share it)."""
    for q in pack.quirks:
        if q.materialize is not None:
            data = MATERIALIZE[q.materialize.transform](data, q.materialize.params, seed)
    return data
