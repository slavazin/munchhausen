"""Grouper implementations (SPEC § 7.2 step 1, § 24.1 E2). A grouper only locates; the coherence guard
(`learn/episodic.coherence_guard`) runs on every grouper's output.

- `agglomerative`: cosine, average linkage, `CLUSTER_DISTANCE`, over `emb.<embedder>` of each observation.
  Observations without a vector (null representation, or a failed embed) are grouped by signature bucket
  rather than dropped, so shaping keeps working with no embedder.
- `signature-buckets` (E2): no text at all. Bucket key = (signature guess, direction of the gap, collection):
  a quirk moves answers the same way on the same population, whatever the template's wording.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from munchhausen.config import Settings
from munchhausen.domain.common import emb_key
from munchhausen.domain.draft import Shape
from munchhausen.domain.observation import Observation
from munchhausen.learn.episodic import shape_of


def _direction(o: Observation) -> str:
    if o.delta is None:
        return "?"
    return "+" if o.delta > 0 else "-" if o.delta < 0 else "0"


def bucket_key(o: Observation) -> tuple[str, str, str]:
    sig = o.signature_guess.value if o.signature_guess is not None else "none"
    return sig, _direction(o), o.surfaces.collection or ""


def buckets(observations: Sequence[Observation]) -> list[Shape]:
    groups: dict[tuple[str, str, str], list[Observation]] = {}
    for o in observations:
        groups.setdefault(bucket_key(o), []).append(o)
    return [shape_of(g) for _, g in sorted(groups.items())]


class AgglomerativeGrouper:
    id = "agglomerative"

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(settings.embed_model, settings.cluster_distance)

    def __init__(self, embedder_id: str, distance_threshold: float) -> None:
        self._key, self._threshold = emb_key(embedder_id), distance_threshold

    async def group(self, observations: Sequence[Observation]) -> list[Shape]:
        obs = [o for o in observations if self._key in o.emb and np.any(o.emb[self._key])]
        located = {o.id for o in obs}
        rest = [o for o in observations if o.id not in located]
        out = buckets(rest) if rest else []
        if len(obs) < 2:
            return out + [shape_of([o]) for o in obs]
        X = np.asarray([o.emb[self._key] for o in obs], dtype=np.float32)
        labels = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                         distance_threshold=self._threshold).fit_predict(X)
        groups: dict[int, list[Observation]] = {}
        for o, lab in zip(obs, labels, strict=True):
            groups.setdefault(int(lab), []).append(o)
        return out + [shape_of(g) for _, g in sorted(groups.items())]


class SignatureBucketGrouper:
    """E2: shapes from residual signatures alone. Cheap, deterministic, needs no representation."""

    id = "signature-buckets"

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls()

    async def group(self, observations: Sequence[Observation]) -> list[Shape]:
        return buckets(observations)
