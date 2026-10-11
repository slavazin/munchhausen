"""Representation implementations: Voyage embeddings, and `none`.

`VoyageRepresentation.embed` keeps the port contract (one call, vectors in input order). Underneath, concurrent
calls of one input type coalesce in a micro-batcher (EMBED_BATCH_WINDOW_MS, EMBED_BATCH_MAX, deduplicated);
each batch reads the run-independent `embedding_cache` once (EMBED_CACHE), sends only its misses to Voyage in
one request, writes them back, and meters the request in `spend` with retries (impl/voyage.py).
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Self

import numpy as np

from munchhausen.config import Settings
from munchhausen.domain.registers import EmbeddingCacheRow
from munchhausen.impl._base import NoDeps, key
from munchhausen.impl.voyage import MicroBatcher, VoyageMeter, current_episode_id, embed_cache_key, sha256
from munchhausen.ports.representation import Role

_INPUT_TYPE = {"observation": "document", "decision": "document", "query": "query"}


class VoyageRepresentation:
    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(name, settings.embed_dim, key(settings, "voyage_api_key"), settings=settings, store=store)

    def __init__(self, model: str, dim: int, api_key: str | None = None, *, settings: Settings | None = None,
                 store: Any = None, client: Any = None) -> None:
        self.id, self.dim = model, dim
        self._s = settings or Settings()
        if client is None:
            import voyageai

            client = voyageai.AsyncClient(api_key=api_key, max_retries=0, timeout=self._s.voyage_timeout_s)
        self._client = client
        self._cache = getattr(store, "embedding_cache", None) if self._s.embed_cache else None
        self._meter = VoyageMeter(self._s, getattr(store, "spend", None), stage=self._s.embed_stage)
        self._batchers: dict[str, MicroBatcher] = {}

    def bind_arm(self, arm: str) -> None:
        """Composition root: the arm this instance serves, stamped on its spend rows."""
        self._meter.arm = arm

    def stats(self) -> dict[str, int]:
        """api_calls, api_errors, retries, texts_sent, tokens, cache_hits, cache_misses, lost writes."""
        return self._meter.stats()

    async def embed(self, texts: Sequence[str], role: Role) -> np.ndarray | None:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        vectors = await self._batcher(_INPUT_TYPE[role]).submit(texts, current_episode_id())
        return np.asarray(vectors, dtype=np.float32)

    def _batcher(self, input_type: str) -> MicroBatcher:
        if input_type not in self._batchers:
            s = self._s

            async def flush(batch: list[str], episode_id: str | None) -> list[list[float]]:
                return await self._resolve(batch, input_type, episode_id)

            self._batchers[input_type] = MicroBatcher(
                flush, window_s=s.embed_batch_window_ms / 1000, max_texts=s.embed_batch_max,
                max_tokens=s.embed_batch_max_tokens, chars_per_token=s.embed_chars_per_token)
        return self._batchers[input_type]

    async def _resolve(self, batch: list[str], input_type: str, episode_id: str | None) -> list[list[float]]:
        """One coalesced batch (unique texts): one cache read for all of it, one API request for its misses,
        then the write-back. Reading the cache inside the batch keeps concurrent callers together: a
        per-caller Atlas read spreads their arrivals past the batch window (live check: 11 requests, not 1)."""
        keys = [embed_cache_key(self.id, self.dim, input_type, t) for t in batch]
        found: dict[str, Sequence[float]] = {}
        if self._cache is not None:
            found = {k: r.vector for k, r in (await self._cache.get_many(keys)).items()}
        misses = [t for t, k in zip(batch, keys, strict=True) if k not in found]
        self._meter.counts["cache_hits"] += len(batch) - len(misses)
        self._meter.counts["cache_misses"] += len(misses)
        if misses:
            for t, v in zip(misses, await self._request(misses, input_type, episode_id), strict=True):
                found[embed_cache_key(self.id, self.dim, input_type, t)] = v
        return [list(found[k]) for k in keys]

    async def _request(self, batch: list[str], input_type: str, episode_id: str | None) -> list[list[float]]:
        """One embed request (with retries), then the cache write-back."""
        res = await self._meter.call(
            self.id, lambda: self._client.embed(batch, model=self.id, input_type=input_type,
                                                output_dimension=self.dim),
            n_texts=len(batch), episode_id=episode_id)
        vectors = [list(map(float, v)) for v in res.embeddings]
        if len(vectors) != len(batch):
            raise RuntimeError(f"{self.id}: {len(vectors)} vectors for {len(batch)} texts")
        if self._cache is not None:
            now = datetime.now(UTC)
            rows = [EmbeddingCacheRow(_id=embed_cache_key(self.id, self.dim, input_type, t), embedder_id=self.id,
                                      dim=self.dim, input_type=input_type, text_hash=sha256(t), vector=tuple(v),
                                      at=now) for t, v in zip(batch, vectors, strict=True)]
            try:
                await self._cache.put_many(rows)
            except Exception as e:   # the vectors are good; a lost write costs a future call, counted
                self._meter.counts["lost_cache_writes"] += 1
                print(f"[embed] cache rows not written ({type(e).__name__}): {len(rows)}", file=sys.stderr)
        return vectors


class NoRepresentation(NoDeps):
    """Non-embedding configurations (signature buckets, hook-only arms)."""

    id, dim = "none", 0

    async def embed(self, texts: Sequence[str], role: Role) -> np.ndarray | None:
        return None
