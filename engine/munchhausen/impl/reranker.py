"""Reranker implementations: Voyage rerank, and identity (keeps input order).

`VoyageReranker.rerank` reads the run-independent `rerank_cache` first (RERANK_CACHE), keyed by model,
query, document hashes and top_k; a miss is one metered request with retries (impl/voyage.py).
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Self

from munchhausen.config import Settings
from munchhausen.domain.registers import RerankCacheRow
from munchhausen.impl._base import NoDeps, key
from munchhausen.impl.voyage import VoyageMeter, current_episode_id, rerank_cache_key, sha256


class VoyageReranker:
    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(name, key(settings, "voyage_api_key"), settings=settings, store=store)

    def __init__(self, model: str, api_key: str | None = None, *, settings: Settings | None = None,
                 store: Any = None, client: Any = None) -> None:
        self._model = model
        self._s = settings or Settings()
        if client is None:
            import voyageai

            client = voyageai.AsyncClient(api_key=api_key, max_retries=0, timeout=self._s.voyage_timeout_s)
        self._client = client
        self._cache = getattr(store, "rerank_cache", None) if self._s.rerank_cache else None
        self._meter = VoyageMeter(self._s, getattr(store, "spend", None), stage=self._s.rerank_stage)

    def bind_arm(self, arm: str) -> None:
        """Composition root: the arm this instance serves, stamped on its spend rows."""
        self._meter.arm = arm

    def stats(self) -> dict[str, int]:
        return self._meter.stats()

    async def rerank(self, query: str, documents: Sequence[str], top_k: int | None = None) -> list[tuple[int, float]]:
        if not documents:
            return []
        docs = list(documents)
        k = rerank_cache_key(self._model, query, docs, top_k)
        if self._cache is not None:
            row = (await self._cache.get_many([k])).get(k)
            if row is not None:
                self._meter.counts["cache_hits"] += 1
                return list(zip(row.indices, row.scores, strict=True))
        self._meter.counts["cache_misses"] += 1
        res = await self._meter.call(
            self._model, lambda: self._client.rerank(query, docs, model=self._model, top_k=top_k),
            n_texts=len(docs) + 1, episode_id=current_episode_id())
        out = [(int(r.index), float(r.relevance_score)) for r in res.results]
        if self._cache is not None:
            row = RerankCacheRow(_id=k, model=self._model, query_hash=sha256(query),
                                 doc_hashes=tuple(sha256(d) for d in docs), top_k=top_k,
                                 indices=tuple(i for i, _ in out), scores=tuple(s for _, s in out),
                                 at=datetime.now(UTC))
            try:
                await self._cache.put_many([row])
            except Exception as e:   # the result is good; a lost write costs a future call, counted
                self._meter.counts["lost_cache_writes"] += 1
                print(f"[rerank] cache row not written ({type(e).__name__})", file=sys.stderr)
        return out


class IdentityReranker(NoDeps):
    async def rerank(self, query: str, documents: Sequence[str], top_k: int | None = None) -> list[tuple[int, float]]:
        n = len(documents) if top_k is None else min(top_k, len(documents))
        return [(i, 1.0) for i in range(n)]
