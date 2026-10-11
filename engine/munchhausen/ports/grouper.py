"""Grouper and SignalSource ports (SPEC § 21, § 7.2, § 25.2)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from munchhausen.domain.draft import Shape
from munchhausen.domain.observation import Observation


@runtime_checkable
class Grouper(Protocol):
    """Observations → candidate shapes. The coherence guard runs on every grouper's output, so a grouper
    only locates; it never proposes a rule."""

    id: str

    async def group(self, observations: Sequence[Observation]) -> list[Shape]: ...


@runtime_checkable
class SignalSource(Protocol):
    """External read-back. Corroborating only: its shapes pass the same bar and L0–L4 as internal ones."""

    async def shapes(self, run_id: str, arm: str, since_idx: int) -> list[Shape]: ...
