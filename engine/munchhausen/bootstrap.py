"""Composition root: the one place that turns config into concrete port implementations and wires
application services. Application modules receive collaborators; they never construct them.

Construction is uniform: `registry.resolve(port, name).create(name, settings, store)`. Nothing here
branches on an implementation name. An implementation whose key is absent (`registry.REQUIRES_KEY`) is
replaced by the port's null implementation, loudly, and the effective selection is what `selection()`
reports for `runs.ports`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from munchhausen.config import Settings
from munchhausen.config import settings as load_settings
from munchhausen.domain.arm import ArmSpec, WritePath
from munchhausen.ports import registry
from munchhausen.ports.store import Store

log = logging.getLogger(__name__)


def build_port(port: str, name: str, s: Settings, store: Store | None = None) -> Any:
    return registry.resolve(port, name).create(name, s, store)


def effective_name(port: str, name: str, s: Settings) -> str:
    """`name`, or the port's null implementation when `name` needs a key that is not set."""
    needs = registry.REQUIRES_KEY.get(port, {}).get(name)
    if needs is not None and getattr(s, needs, None) is None:
        return registry.NULL_IMPLEMENTATION[port]
    return name


@dataclass
class Harness:
    settings: Settings
    store: Store
    arms: dict[str, ArmSpec]
    ports: dict[str, dict[str, Any]] = field(default_factory=dict)   # arm → port → instance

    def selection(self) -> dict[str, dict[str, str]]:
        """Effective port selections per arm, written to `runs.ports` at run start (SPEC § 21)."""
        return {a: {p: effective_name(p, n, self.settings) for p, n in spec.ports.items()}
                for a, spec in self.arms.items()}

    def port(self, arm: str, port: str) -> Any:
        cache = self.ports.setdefault(arm, {})
        if port not in cache:
            wanted = self.arms[arm].ports[port]
            name = effective_name(port, wanted, self.settings)
            if name != wanted:
                log.warning("[%s] port %s: %r needs %s, which is not set; using %r", arm, port, wanted,
                            registry.REQUIRES_KEY[port][wanted].upper(), name)
            cache[port] = build_port(port, name, self.settings, self.store)
            bind = getattr(cache[port], "bind_arm", None)   # metered ports stamp their arm on spend rows
            if callable(bind):
                bind(arm)
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
                self.settings.world_impl, self.settings, _EvaluationStore(self.store), truth_db=truth_db)
        return self.ports["_run"]["world"]

    # --- S2 (M2): the forward pass and the arm runner ---------------------------------------------------

    async def ready_world(self) -> Any:
        """The World with its schema summary loaded from the built `world` (a run that did not build it)."""
        w = self.world()
        try:
            w.schema_summary()
        except RuntimeError:
            await w.load_schema()
        return w

    def trace(self) -> Any:
        return self.shared("trace", self.settings.trace_impl)

    def models(self) -> Any:
        return self.shared("models", self.settings.models_impl)

    def consulter(self, arm: str) -> Any:
        """The arm's consulter, one per arm (cached under `ports[arm]["consulter"]`): the forward pass and
        the backtest's replays consult through the same instance."""
        cache = self.ports.setdefault(arm, {})
        if "consulter" not in cache:
            cache["consulter"] = self._build_consulter(arm)
        return cache["consulter"]

    def _build_consulter(self, arm: str) -> Any:
        from munchhausen.agent.consultation import consulter_for

        s, spec = self.settings, self.arms[arm]
        return consulter_for(spec, decisions=self.store.decisions, terms=self.store.terms,
                             representation=self.port(arm, "representation"),
                             similarity=self.port(arm, "similarity"), reranker=self.port(arm, "reranker"),
                             top_k=s.naive_top_k, budget_tokens=s.context_budget_tokens)

    def forward_pass(self, arm: str, world: Any | None = None, models: Any | None = None) -> Any:
        """`models` (additive, S6): the injection passes a stage-tagging wrapper so its proposer spend is
        recorded under INJECT_STAGE; None keeps the run's models."""
        from munchhausen.agent.proposer import Proposer
        from munchhausen.loop.episode import ForwardParams, ForwardPass

        s = self.settings
        return ForwardPass(
            run_id=s.run_id, arm=self.arms[arm], world=world or self.world(), store=self.store,
            consulter=self.consulter(arm), proposer=Proposer(models or self.models()), trace=self.trace(),
            params=ForwardParams(max_time_ms=s.execute_max_time_ms, rel_tol=s.score_rel_tol,
                                 propose_attempts=s.propose_attempts, rounding_base=s.rounding_unit_base,
                                 fire_fetch_factor=s.fire_fetch_factor))

    def round_hook(self, arm: str) -> Any:
        """`on_round_close`: the arm's backward pass (S4), then the round record (S5). Arms with
        `write_path: none` skip the backward pass. Unbuilt seams log loudly and are skipped, so `frozen`
        runs before M3/M4 land."""
        from munchhausen import bootstrap_learn, evidence

        backward = None
        if self.arms[arm].write_path is not WritePath.NONE:
            try:
                backward = bootstrap_learn.backward_for(self, arm)
            except NotImplementedError as e:
                log.error("[%s] BACKWARD PASS NOT BUILT (%s): rounds close without learning", arm, e)

        async def close(round_: int, idx_range: tuple[int, int]) -> None:
            if backward is not None:
                try:
                    await backward(round_, idx_range)
                except NotImplementedError as e:
                    log.error("[%s] round %d: BACKWARD PASS NOT BUILT (%s)", arm, round_, e)
            try:
                await evidence.close_round(self, arm, round_, idx_range)
            except NotImplementedError as e:
                log.error("[%s] round %d: ROUND RECORD NOT BUILT (%s)", arm, round_, e)

        return close

    def arm_runner(self, arm: str, world: Any | None = None) -> Any:
        from munchhausen.loop.runner import ArmRunner

        s, w = self.settings, world or self.world()
        return ArmRunner(run_id=s.run_id, forward=self.forward_pass(arm, w), world=w, store=self.store,
                         workers=s.workers_per_arm, round_size=s.round_size, run_length=s.run_length,
                         v_every=s.v_every, v_offset=s.v_offset, on_round_close=self.round_hook(arm),
                         stream_seed=s.stream_seed, stream=self.arms[arm].stream, attempts=s.episode_attempts,
                         poll_interval_s=s.poll_interval_s, lease_wait_s=s.lease_ttl_s + 2 * s.poll_interval_s)

    async def close(self) -> None:
        await self.store.close()


class _EvaluationStore:
    """The Store as the World implementation sees it: `world()` is the evaluation-side read (unguarded, no row
    cap) when the store offers one, so gold's whole-collection reads never meet the sandbox meant for
    model-written pipelines. Every other attribute is the store's own."""

    def __init__(self, store: Store) -> None:
        self._store = store

    def world(self) -> Any:
        read = getattr(self._store, "world_evaluation", None)
        return read() if read is not None else self._store.world()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._store, name)


def harness(s: Settings | None = None) -> Harness:
    s = s or load_settings()
    return Harness(settings=s, store=build_port("store", s.store_impl, s), arms=s.arms())
