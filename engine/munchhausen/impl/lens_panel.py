"""LensPanel implementations: TypeSafe Jev (corroborating), and `none`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

from munchhausen.config import Settings
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Draft
from munchhausen.domain.lens import LensEntry
from munchhausen.domain.observation import Observation
from munchhausen.impl._base import NoDeps, key


class JevLensPanel:
    """One `system_one` call per lens (LENS_CALL_MODE=isolated) or per draft (joint). M3."""

    id = "jev"

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(settings.lenses(), key(settings, "typesafe_api_key"))

    def __init__(self, lenses: Sequence[LensEntry], api_key: str | None = None) -> None:
        self._lenses = [lens for lens in lenses if lens.status == "active"]
        self._api_key = api_key

    async def score(self, draft: Draft, sources: Sequence[Observation],
                    neighbours: Sequence[Decision]) -> dict[str, float]:
        raise NotImplementedError("M3: typesafe-sdk AsyncTypeSafeClient.system_one per lens (§ 7.3 L3)")


class NoLensPanel(NoDeps):
    """No corroborating panel: L3 passes every draft through to the dispositive backtest."""

    id = "none"

    async def score(self, draft: Draft, sources: Sequence[Observation],
                    neighbours: Sequence[Decision]) -> dict[str, float]:
        return {}
