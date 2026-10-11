"""Fires: records a latch emits when its guard holds (SPEC § 2, § 6.3)."""

from __future__ import annotations

from enum import StrEnum

from munchhausen.domain.common import Disposer, FireDisposition, FireRole, Record


class FireCause(StrEnum):
    RESIDUALS = "residuals"        # a revisit guard over attributable residuals → dispositive
    UNATTRIBUTED = "unattributed"  # a residual that is not attributable → corroborating
    ANOMALY = "anomaly"            # a proposer anomaly → corroborating
    OWNER = "owner"


class Fire(Record):
    decision_id: str
    latch: str                     # the latch id that fired (T-<decision_id>-<k>)
    role: FireRole
    cause: FireCause
    episode_ids: tuple[str, ...]
    residual_ids: tuple[str, ...] = ()
    note: str | None = None        # the anomaly text, for corroborating fires
    disposer: Disposer | None = None
    disposition: FireDisposition = FireDisposition.OPEN
    at_idx: int
