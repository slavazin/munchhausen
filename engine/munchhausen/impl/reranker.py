"""Reranker implementations: Voyage rerank, and identity (keeps input order)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

from munchhausen.config import Settings
from munchhausen.impl._base import NoDeps, key


class VoyageReranker:
    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(name, key(settings, "voyage_api_key"))

    def __init__(self, model: str, api_key: str | None = None) -> None:
        import voyageai

        self._model = model
        self._client = voyageai.AsyncClient(api_key=api_key)

    async def rerank(self, query: str, documents: Sequence[str], top_k: int | None = None) -> list[tuple[int, float]]:
        if not documents:
            return []
        res = await self._client.rerank(query, list(documents), model=self._model, top_k=top_k)
        return [(r.index, float(r.relevance_score)) for r in res.results]


class IdentityReranker(NoDeps):
    async def rerank(self, query: str, documents: Sequence[str], top_k: int | None = None) -> list[tuple[int, float]]:
        n = len(documents) if top_k is None else min(top_k, len(documents))
        return [(i, 1.0) for i in range(n)]
