"""Similarity implementations: Atlas `$vectorSearch` (ANN or exact), and in-process numpy cosine."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Self

import numpy as np

from munchhausen.config import Settings
from munchhausen.domain.common import emb_key
from munchhausen.ports.store import Store


class AtlasVectorSimilarity:
    @classmethod
    def create(cls, name: str, settings: Settings, store: Store) -> Self:
        return cls(store, settings.embed_model, exact=name == "atlas-exact")

    def __init__(self, store: Store, embedder_id: str, exact: bool = False) -> None:
        self._store, self._embedder, self._exact = store, embedder_id, exact

    async def knn(self, store: str, query: Sequence[float] | str, k: int,
                  filter: dict[str, Any]) -> list[tuple[str, float]]:
        if isinstance(query, str):
            raise TypeError("client-vector similarity needs a vector; autoEmbed text queries are M2 (§ 20.2)")
        return await self._store.vector_search(store, self._embedder, query, k, filter, exact=self._exact)


class NumpySimilarity:
    """Fallback when the index budget is spent (SPEC § 3 premises). `load` supplies (ids, matrix)."""

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(store_loader(store, emb_key(settings.embed_model)))

    def __init__(self, load: Callable[[str, dict[str, Any]], Any]) -> None:
        self._load = load

    async def knn(self, store: str, query: Sequence[float] | str, k: int,
                  filter: dict[str, Any]) -> list[tuple[str, float]]:
        if isinstance(query, str):
            raise TypeError("numpy similarity needs a vector")
        ids, mat = await self._load(store, filter)
        if not ids:
            return []
        q = np.asarray(query, dtype=np.float32)
        sims = (mat @ q) / (np.linalg.norm(mat, axis=1) * np.linalg.norm(q) + 1e-9)
        top = np.argsort(-sims)[:k]
        return [(ids[i], float(sims[i])) for i in top]


def store_loader(store: Store, key: str) -> Callable[[str, dict[str, Any]], Any]:
    """(store name, filter) → (ids, matrix) over records holding `emb.<key>`, read through the Store port.
    The filter's `run_id`/`arm` select the repository read; every other key is matched on the record."""

    async def load(name: str, filter: dict[str, Any]) -> tuple[list[str], np.ndarray]:
        run_id, arm = filter.get("run_id", ""), filter.get("arm", "")
        reads = {"decisions": lambda: store.decisions.admitted(run_id, arm),
                 "observations": lambda: store.observations.open_for_pass(run_id, arm, since_round=0)}
        if name not in reads:
            raise ValueError(f"numpy similarity has no loader for store {name!r}")
        ids, rows = [], []
        for rec in await reads[name]():
            doc = rec.model_dump(mode="json", by_alias=True)
            if all(_dig(doc, k) == v for k, v in filter.items() if k not in ("run_id", "arm")):
                vec = rec.emb.get(key)
                if vec:
                    ids.append(rec.id)
                    rows.append(vec)
        return ids, (np.asarray(rows, dtype=np.float32) if rows else np.zeros((0, 0), dtype=np.float32))

    return load


def _dig(doc: Any, path: str) -> Any:
    for part in path.split("."):
        doc = doc.get(part) if isinstance(doc, dict) else None
    return doc
