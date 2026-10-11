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


class SampleAnalyticsAdapter:
    name = "sample_analytics"

    @classmethod
    def create(cls, name: str, settings: Any, store: Any) -> Self:
        return cls(store.source(), store.world_writer(), settings.schema_sample_docs, settings.schema_max_depth,
                   settings.execute_max_time_ms)

    def __init__(self, source: DocumentReader, world: WorldWriter, sample_docs: int, max_depth: int,
                 max_time_ms: int) -> None:
        self._source, self._world = source, world
        self._sample_docs, self._max_depth, self._max_time_ms = sample_docs, max_depth, max_time_ms

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
        """Field paths and BSON types, sampled from `world`; never meanings."""
        out = {}
        for c in SOURCE_COLLECTIONS:
            out[c] = field_types(await self._world.find(c, limit=self._sample_docs), self._max_depth)
        return SchemaSummary(collections=out)


def materialize_pack(data: Data, pack: Pack, seed: int) -> Data:
    """Apply every quirk's materialize transform in pack order (pure; the adapter and tests share it)."""
    for q in pack.quirks:
        if q.materialize is not None:
            data = MATERIALIZE[q.materialize.transform](data, q.materialize.params, seed)
    return data
