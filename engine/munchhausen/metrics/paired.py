"""Paired arm differences (SPEC § 11). Arms share the stream by index, so two arms' first attempts on the
same index are a pair: the reading is the mean paired difference with a bootstrap interval and its n, and
a forecast's verdict is three-way against its pre-registered margin (`conf/forecasts.yaml`)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

Verdict = Literal["above", "within", "below"]


@dataclass(frozen=True)
class PairedReading:
    diff: float          # mean of a − b
    lo: float
    hi: float
    n: int               # pairs
    level: float

    def verdict(self, margin: float) -> Verdict:
        if self.lo > margin:
            return "above"
        if self.hi < -margin:
            return "below"
        return "within"


def paired_difference(a: Sequence[float], b: Sequence[float], *, n_boot: int, level: float,
                      seed: int) -> PairedReading:
    """Percentile bootstrap over pairs. `a[i]` and `b[i]` are the two arms' outcomes on stream index i."""
    if len(a) != len(b):
        raise ValueError("paired readings need equal-length sequences aligned by stream index")
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if d.size == 0:
        return PairedReading(diff=float("nan"), lo=float("nan"), hi=float("nan"), n=0, level=level)
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, d.size, size=(n_boot, d.size))].mean(axis=1)
    tail = (1.0 - level) / 2.0
    lo, hi = np.quantile(means, [tail, 1.0 - tail])
    return PairedReading(diff=float(d.mean()), lo=float(lo), hi=float(hi), n=int(d.size), level=level)


def difference_of_means(after: Sequence[float], before: Sequence[float], *, n_boot: int, level: float,
                        seed: int) -> PairedReading:
    """Unpaired percentile bootstrap of mean(after) − mean(before): two windows of one arm (F1). Each window
    is resampled on its own. `n` is the smaller window, the one that bounds the interval."""
    a, b = np.asarray(after, dtype=float), np.asarray(before, dtype=float)
    if a.size == 0 or b.size == 0:
        return PairedReading(diff=float("nan"), lo=float("nan"), hi=float("nan"), n=0, level=level)
    rng = np.random.default_rng(seed)
    ma = a[rng.integers(0, a.size, size=(n_boot, a.size))].mean(axis=1)
    mb = b[rng.integers(0, b.size, size=(n_boot, b.size))].mean(axis=1)
    tail = (1.0 - level) / 2.0
    lo, hi = np.quantile(ma - mb, [tail, 1.0 - tail])
    return PairedReading(diff=float(a.mean() - b.mean()), lo=float(lo), hi=float(hi),
                         n=int(min(a.size, b.size)), level=level)
