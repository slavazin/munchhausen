"""Grouper implementations. Agglomerative clustering over observation embeddings (SPEC § 7.2 step 1)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from munchhausen.config import Settings
from munchhausen.domain.common import emb_key
from munchhausen.domain.draft import Shape
from munchhausen.domain.ids import shape_id
from munchhausen.domain.observation import Observation


class AgglomerativeGrouper:
    id = "agglomerative"

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(settings.embed_model, settings.cluster_distance)

    def __init__(self, embedder_id: str, distance_threshold: float) -> None:
        self._key, self._threshold = emb_key(embedder_id), distance_threshold

    async def group(self, observations: Sequence[Observation]) -> list[Shape]:
        obs = [o for o in observations if self._key in o.emb]
        if len(obs) < 2:
            return [_shape([o]) for o in obs]
        X = np.asarray([o.emb[self._key] for o in obs], dtype=np.float32)
        labels = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                         distance_threshold=self._threshold).fit_predict(X)
        groups: dict[int, list[Observation]] = {}
        for o, lab in zip(obs, labels, strict=True):
            groups.setdefault(int(lab), []).append(o)
        return [_shape(g) for g in groups.values()]


def _shape(members: Sequence[Observation]) -> Shape:
    ids = tuple(sorted(o.id for o in members))
    return Shape(
        id=shape_id(ids),
        observation_ids=ids,
        episode_ids=tuple(sorted({o.episode_id for o in members})),
        templates=frozenset(o.template for o in members),
        personas=frozenset(o.persona for o in members),
        terms=frozenset(t for o in members for t in o.surfaces.terms),
    )
