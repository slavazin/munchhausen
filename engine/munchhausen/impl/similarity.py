"""Similarity implementations: Atlas `$vectorSearch` (ANN or exact), and in-process numpy cosine."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Self

import numpy as np

from munchhausen.config import Settings
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
        raise NotImplementedError("M2: loader over Store reads of emb.<embedder_id>")

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
