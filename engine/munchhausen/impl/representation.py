"""Representation implementations: Voyage embeddings, and `none`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

import numpy as np

from munchhausen.config import Settings
from munchhausen.impl._base import NoDeps, key
from munchhausen.ports.representation import Role

_INPUT_TYPE = {"observation": "document", "decision": "document", "query": "query"}


class VoyageRepresentation:
    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(name, settings.embed_dim, key(settings, "voyage_api_key"))

    def __init__(self, model: str, dim: int, api_key: str | None = None) -> None:
        import voyageai

        self.id, self.dim = model, dim
        self._client = voyageai.AsyncClient(api_key=api_key)

    async def embed(self, texts: Sequence[str], role: Role) -> np.ndarray | None:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        res = await self._client.embed(list(texts), model=self.id, input_type=_INPUT_TYPE[role],
                                       output_dimension=self.dim)
        return np.asarray(res.embeddings, dtype=np.float32)


class NoRepresentation(NoDeps):
    """Non-embedding configurations (signature buckets, hook-only arms)."""

    id, dim = "none", 0

    async def embed(self, texts: Sequence[str], role: Role) -> np.ndarray | None:
        return None
