"""Composition root: the one place that turns config into concrete port implementations and wires
application services. Application modules receive collaborators; they never construct them.

Construction is uniform: `registry.resolve(port, name).create(name, settings, store)`. Nothing here
branches on an implementation name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from munchhausen.config import Settings
from munchhausen.config import settings as load_settings
from munchhausen.domain.arm import ArmSpec
from munchhausen.ports import registry
from munchhausen.ports.store import Store


def build_port(port: str, name: str, s: Settings, store: Store | None = None) -> Any:
    return registry.resolve(port, name).create(name, s, store)


@dataclass
class Harness:
    settings: Settings
    store: Store
    arms: dict[str, ArmSpec]
    ports: dict[str, dict[str, Any]] = field(default_factory=dict)   # arm → port → instance

    def selection(self) -> dict[str, dict[str, str]]:
        """Port selections per arm, written to `runs.ports` at run start (SPEC § 21)."""
        return {a: dict(spec.ports) for a, spec in self.arms.items()}

    def port(self, arm: str, port: str) -> Any:
        cache = self.ports.setdefault(arm, {})
        if port not in cache:
            cache[port] = build_port(port, self.arms[arm].ports[port], self.settings, self.store)
        return cache[port]

    def shared(self, port: str, name: str) -> Any:
        """Run-wide ports (models, trace, signal source), one instance per run."""
        cache = self.ports.setdefault("_run", {})
        if port not in cache:
            cache[port] = build_port(port, name, self.settings, self.store)
        return cache[port]

    def world(self) -> Any:
        """The World port plus its evaluation-side Truth (`world.truth`), wired with the evaluator handle."""
        if "world" not in self.ports.setdefault("_run", {}):
            from munchhausen.store.atlas import open_truth  # composition root: allowed to know the store

            truth_db = open_truth(self.settings, self.store.clients)  # type: ignore[attr-defined]
            self.ports["_run"]["world"] = registry.resolve("world", self.settings.world_impl).create(
                self.settings.world_impl, self.settings, self.store, truth_db=truth_db)
        return self.ports["_run"]["world"]

    async def close(self) -> None:
        await self.store.close()


def harness(s: Settings | None = None) -> Harness:
    s = s or load_settings()
    return Harness(settings=s, store=build_port("store", s.store_impl, s), arms=s.arms())
