"""Lens entries and lens weights (SPEC § 23.2, § 7.3, § 9)."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import Field

from munchhausen.domain.common import LayerRole, Value


class LensStatus(StrEnum):
    ACTIVE = "active"
    FOLDED = "folded"
    REVERSED = "reversed"
    DEAD = "dead"
    RETIRED = "retired"


class LensWarrant(Value):
    lensfit_version: int
    delta_logloss: float
    auc_contribution: float


class LensEntry(Value):
    id: str
    angle: str
    counterfactual: str
    product: Literal["noul", "choice", "score"]
    levels: tuple[str, ...] = ()
    pointer: tuple[str, ...]
    role: Literal[LayerRole.ROUTING, LayerRole.CORROBORATING]   # never dispositive
    consumer: Literal["L3"] = "L3"
    counterfactual_anchor: str = "seed"
    phrasings: tuple[str, str, str]
    status: LensStatus = LensStatus.ACTIVE
    warrant: tuple[LensWarrant, ...] = ()


class LensWeights(Value):
    version: int
    weights: dict[str, float]
    bias: float = 0.0
    folds: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    n_labels: int = 0
    auc_prequential: float | None = None
    auc_ci: tuple[float, float] | None = None

    def score(self, p: dict[str, float]) -> float:
        """score = σ(b + Σ wᵢ·logit(pᵢ)) over the lenses that carry a weight."""
        z = self.bias + sum(w * _logit(p[k]) for k, w in self.weights.items() if k in p and w)
        return 1.0 / (1.0 + math.exp(-z))


def _logit(p: float, eps: float = 1e-6) -> float:
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))
