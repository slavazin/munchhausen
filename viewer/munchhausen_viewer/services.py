"""What the viewer is handed by its composition root (`munchhausen.commands.viewer`): a read model, an
injector per arm, and the owner port (L5). The viewer constructs none of them."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from munchhausen.config import Settings
from munchhausen.domain.arm import ArmSpec, WritePath
from munchhausen.loop.inject import Injector
from munchhausen.ports.store import ReadModel


class OwnerPort(Protocol):
    """L5 (SPEC § 7.3): an owner disposition on a draft or a fire, recorded as `disposer: owner`.
    Implemented by the adjudication surface; the viewer only calls it."""

    async def dispose_draft(self, draft_id: str, verdict: str, note: str) -> dict[str, Any]: ...

    async def dispose_fire(self, fire_id: str, disposition: str, note: str) -> dict[str, Any]: ...


@dataclass
class ViewerServices:
    settings: Settings
    read_model: ReadModel
    arms: dict[str, ArmSpec]
    injector_for: Callable[[str], Injector] | None = None   # may raise NotImplementedError until M2/M3 land
    owner: Callable[[], OwnerPort] | None = None            # built lazily; may raise NotImplementedError
    close: Callable[[], Awaitable[None]] | None = None
    mode: str = "atlas"                                      # atlas | synthetic (shown in the header)

    @property
    def run_id(self) -> str:
        return self.settings.viewer_run_id or self.settings.run_id

    @property
    def reference_arm(self) -> str:
        """The paired reference: the knob, else the arm with no write path (no name is assumed)."""
        if self.settings.viewer_reference_arm:
            return self.settings.viewer_reference_arm
        return next((a for a, s in self.arms.items() if s.write_path is WritePath.NONE and s.stream),
                    next(iter(self.arms)))

    @property
    def default_arm(self) -> str:
        return self.settings.viewer_arm if self.settings.viewer_arm in self.arms else next(reversed(self.arms))

    @property
    def window(self) -> int:
        return self.settings.viewer_curve_window or self.settings.round_size
