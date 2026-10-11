"""Adapter over the Atlas sample database `sample_analytics` (SPEC § 4.2).

Reads `customers`, `accounts`, `transactions` from the source database, applies the pack's materialize
transforms in order, and writes the result to `world`. Field names are opaque by design (§ 4.1 Don't).
"""

from __future__ import annotations

from typing import Any, Self

from munchhausen.domain.question import SchemaSummary
from munchhausen.ports.store import DocumentReader, WorldWriter
from munchhausen.world.pack import Pack
from munchhausen.world.transforms import MATERIALIZE

SOURCE_COLLECTIONS = ("customers", "accounts", "transactions")


class SampleAnalyticsAdapter:
    name = "sample_analytics"

    @classmethod
    def create(cls, name: str, settings: Any, store: Any) -> Self:
        return cls(store.source(), store.world_writer())

    def __init__(self, source: DocumentReader, world: WorldWriter) -> None:
        self._source, self._world = source, world

    async def build(self, pack: Pack, seed: int) -> dict[str, int]:
        data: dict[str, list[dict[str, Any]]] = {c: await self._source.find(c) for c in SOURCE_COLLECTIONS}
        for q in pack.quirks:
            if q.materialize is not None:
                data = MATERIALIZE[q.materialize.transform](data, q.materialize.params, seed)
        return {c: await self._world.replace_collection(c, docs) for c, docs in data.items()}

    async def schema_summary(self) -> SchemaSummary:
        """Field names and BSON types, sampled from `world`; never meanings."""
        out: dict[str, dict[str, str]] = {}
        for c in SOURCE_COLLECTIONS:
            fields: dict[str, str] = {}
            for doc in await self._world.find(c, limit=50):
                for k, v in doc.items():
                    fields.setdefault(k, type(v).__name__)
            out[c] = fields
        return SchemaSummary(collections=out)
