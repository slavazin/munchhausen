"""Representation, Similarity and Reranker ports (SPEC § 21, § 24.1)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, Protocol, runtime_checkable

import numpy as np

Role = Literal["observation", "decision", "query"]


@runtime_checkable
class Representation(Protocol):
    """Embedding or non-embedding representation. Each vector is stamped with `id` (`emb.<id>`), so
    versions coexist and switching never re-embeds history in place (E10)."""

    id: str
    dim: int

    async def embed(self, texts: Sequence[str], role: Role) -> np.ndarray | None: ...


@runtime_checkable
class Similarity(Protocol):
    """How neighbours are found: Atlas vector, exact (ENN), hybrid, numpy, or behavioural."""

    async def knn(self, store: str, query: Sequence[float] | str, k: int,
                  filter: dict[str, Any]) -> list[tuple[str, float]]: ...


@runtime_checkable
class Reranker(Protocol):
    """Orders candidates by relevance to a query (Voyage `rerank-3`, or identity)."""

    async def rerank(self, query: str, documents: Sequence[str], top_k: int | None = None) -> list[tuple[int, float]]:
        """Return (index into documents, relevance) pairs, most relevant first."""
        ...
