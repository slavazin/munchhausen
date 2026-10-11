"""Composition root, backward half: builds each arm's round-close hook from its `ArmSpec`.

`bootstrap.py` wires the forward pass and the `ArmRunner`; it asks this module for the `on_round_close`
hook of an arm. The hook is chosen by the arm's `write_path` (none | direct | self_grade | episodic) and
its `curator`, never by the arm's name. Owner: adjudication surface (M3).

Collaborators owned by other surfaces (S3's `Observer`, `Nominator`, `EpisodicPass`; S2's consulter) are
constructed from the dependencies their dataclass fields name (`_build`), so their constructors can settle
without an edit here. A piece that still raises `NotImplementedError` is logged loudly (stderr + trace
event `backward.unavailable`) and the round continues to the lifecycle sweep.
"""

from __future__ import annotations

import asyncio
import dataclasses
import inspect
import sys
from collections.abc import Callable
from typing import Any

from munchhausen.agent.consultation import Consulter
from munchhausen.agent.proposer import Proposer
from munchhausen.domain.arm import ArmSpec, WritePath
from munchhausen.domain.episode import Episode
from munchhausen.domain.question import Question, QuestionKeys
from munchhausen.learn.adjudicate import Adjudicator
from munchhausen.learn.backtest import Backtester
from munchhausen.learn.direct import DirectWriter, blind
from munchhausen.learn.layers import L0Shape, L1Bar, L2Neighbours, L3Lenses, L4Backtest, LessonShape
from munchhausen.learn.lifecycle import LifecycleService
from munchhausen.loop.episode import failed
from munchhausen.loop.runner import RoundHook
from munchhausen.ports import registry
from munchhausen.store.names import view_name

LESSON_PATHS = (WritePath.DIRECT, WritePath.SELF_GRADE)


def _cache(h: Any, arm: str) -> dict[str, Any]:
    return h.ports.setdefault(arm, {})


def _trace(h: Any) -> Any:
    return h.shared("trace", h.settings.trace_impl)


def _build(cls: Any, deps: dict[str, Any]) -> Any:
    """Construct a collaborator from the deps its dataclass fields (or `__init__` parameters) name."""
    if dataclasses.is_dataclass(cls):
        params = {f.name: f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
                  for f in dataclasses.fields(cls) if f.init}
    else:
        params = {n: p.default is inspect.Parameter.empty
                  for n, p in inspect.signature(cls).parameters.items() if n not in ("self", "args", "kwargs")}
    missing = sorted(n for n, required in params.items() if required and n not in deps)
    if missing:
        raise TypeError(f"{getattr(cls, '__name__', cls)}: no dependency named {missing}")
    return cls(**{n: deps[n] for n in params if n in deps})


class _LazyConsulter:
    """The arm's own consulter, resolved at the first replay (S2 owns `consulter_for`)."""

    def __init__(self, factory: Callable[[], Consulter]) -> None:
        self._factory, self._c = factory, None

    async def consult(self, run_id: str, arm: str, question: Question) -> tuple[QuestionKeys, list[Any]]:
        if self._c is None:
            self._c = self._factory()
        return await self._c.consult(run_id, arm, question)


def consulter(h: Any, arm: str) -> Consulter:
    """The arm's consulter: the forward pass's own (`Harness.consulter`, cached under
    `h.ports[arm]["consulter"]`), so replays consult exactly as episodes do."""
    return h.consulter(arm)


def lifecycle_for(h: Any, arm: str) -> LifecycleService:
    cache = _cache(h, arm)
    if "lifecycle" not in cache:
        s, store = h.settings, h.store
        cache["lifecycle"] = LifecycleService(
            decisions=store.decisions, world=store.world_writer(), sink=h.port(arm, "memory_sink"),
            tool_access=store.tool_access, fires=store.fires, episodes=store.episodes, trace=_trace(h),
            retire_idle=s.retire_idle, retire_fires=s.retire_fires)
    return cache["lifecycle"]


def backtester_for(h: Any, arm: str) -> Backtester:
    cache = _cache(h, arm)
    if "backtester" not in cache:
        s, store = h.settings, h.store
        cache["backtester"] = Backtester(
            episodes=store.episodes, fires=store.fires, consulter=_LazyConsulter(lambda: consulter(h, arm)),
            proposer=Proposer(h.shared("models", s.models_impl)), world=store.world(),
            thresholds=s.backtest_thresholds, n=s.backtest_n, rel_tol=s.score_rel_tol,
            max_time_ms=s.execute_max_time_ms, backtests=store.backtests, tool_access=store.tool_access,
            schema=lambda: h.world().schema_summary(),
            seed=s.backtest_seed if s.backtest_sample == "hashed" else None,
            concurrency=s.backtest_concurrency, trace=_trace(h))
    return cache["backtester"]


def curator_for(h: Any, arm: str) -> Any:
    """The arm's curator from the registry; its factory names the layers it takes (l0 … l4), and only
    those are built. Lesson write paths take `LessonShape` as L0 (SPEC § 5)."""
    cache = _cache(h, arm)
    if "curator" not in cache:
        s, store, spec = h.settings, h.store, h.arms[arm]
        layers: dict[str, Callable[[], Any]] = {
            "l0": (lambda: LessonShape()) if spec.write_path in LESSON_PATHS else (lambda: L0Shape(store.terms)),
            "l1": lambda: L1Bar(min_templates=s.bar_min_templates, min_templates_floor=s.bar_min_templates_floor),
            "l2": lambda: L2Neighbours(threshold=s.neighbour_rerank, decisions=store.decisions, fires=store.fires,
                                       route_contested=s.l2_route_contested),
            "l3": lambda: L3Lenses(panel=h.port(arm, "lens_panel"), weights=store.lenses, mode=s.lens_mode,
                                   threshold=s.lens_threshold, explore_eps=s.lens_explore_eps, seed=s.world_seed),
            "l4": lambda: L4Backtest(backtester_for(h, arm)),
        }
        factory = registry.resolve("curator", spec.curator)
        cache["curator"] = factory(**{n: layers[n]() for n in inspect.signature(factory).parameters})
    return cache["curator"]


def adjudicator_for(h: Any, arm: str) -> Adjudicator:
    """The `ports.curation.Adjudicator` for an arm (S3's episodic pass and S6's injection hand drafts here)."""
    cache = _cache(h, arm)
    if "adjudicator" not in cache:
        store = h.store
        cache["adjudicator"] = Adjudicator(
            curator=curator_for(h, arm), drafts=store.drafts, decisions=store.decisions, fires=store.fires,
            lifecycle=lifecycle_for(h, arm), view_name=view_name,
            representation=_representation(h, arm), trace=_trace(h))
    return cache["adjudicator"]


def direct_writer_for(h: Any, arm: str) -> DirectWriter:
    cache = _cache(h, arm)
    if "direct_writer" not in cache:
        s = h.settings
        cache["direct_writer"] = DirectWriter(
            models=h.shared("models", s.models_impl), adjudicator=adjudicator_for(h, arm), decisions=h.store.decisions,
            observations=h.store.observations,
            representation=_representation(h, arm), merge=s.direct_merge, merge_cosine=s.naive_merge_cosine,
            concurrency=s.workers_per_arm, trace=_trace(h))
    return cache["direct_writer"]


def _representation(h: Any, arm: str) -> Any:
    rep = h.port(arm, "representation")
    return rep if getattr(rep, "dim", 0) else None


def _deps(h: Any, arm: str) -> dict[str, Any]:
    """Everything a backward collaborator of another surface may ask for, by field name."""
    from munchhausen.learn.episodic import Bar

    s, store, spec = h.settings, h.store, h.arms[arm]
    deps: dict[str, Any] = {
        "run_id": s.run_id, "arm": arm, "spec": spec, "arm_spec": spec, "settings": s, "store": store,
        "episodes": store.episodes, "observations": store.observations, "decisions": store.decisions,
        "drafts": store.drafts, "fires": store.fires, "terms": store.terms, "backtests": store.backtests,
        "world": store.world(), "models": h.shared("models", s.models_impl), "trace": _trace(h),
        "representation": h.port(arm, "representation"), "similarity": h.port(arm, "similarity"),
        "reranker": h.port(arm, "reranker"), "grouper": h.port(arm, "grouper"),
        "signal_source": h.shared("signal_source", s.signal_source_impl),
        "bar": Bar(min_obs=s.bar_min_obs, min_templates=s.bar_min_templates, min_gap=s.bar_min_gap,
                   min_matched=s.bar_min_matched),
        "neighbour_k": s.neighbour_k, "carry_rounds": s.carry_rounds, "authority": spec.authority,
        "with_authority": spec.authority, "lifecycle": lifecycle_for(h, arm), "round_size": s.round_size,
        "embed_mask": s.embed_mask, "residual_window": getattr(s, "nominator_residual_window", s.fire_window),
    }
    if spec.curator is not None:
        deps["curator"] = curator_for(h, arm)
        deps["adjudicator"] = adjudicator_for(h, arm)
    return deps


def _collaborator(h: Any, arm: str, key: str, module: str, cls_name: str, deps: dict[str, Any]) -> Any:
    cache = _cache(h, arm)
    if key not in cache:
        import importlib

        cache[key] = _build(getattr(importlib.import_module(module), cls_name), deps)
    return cache[key]


def _unavailable(h: Any, arm: str, round_: int, what: str, e: BaseException) -> None:
    msg = f"[backward] {arm} round {round_}: {what} unavailable: {type(e).__name__}: {e}"
    print(msg, file=sys.stderr)
    _trace(h).event("backward.unavailable", {"arm": arm, "round": round_, "what": what, "error": str(e)})


async def round_episodes(h: Any, arm: str, lo: int, hi: int) -> list[Episode]:
    """The round's stream episodes, through the learner read: full for arms with an authority, blind
    (evaluation-only fields projected away) otherwise. `idx_range` is read inclusively; every write
    downstream is idempotent per episode, so an overlap costs nothing."""
    spec: ArmSpec = h.arms[arm]
    docs = await h.store.episodes.for_learner(h.settings.run_id, arm, with_authority=spec.authority,
                                              filter={"stream": "stream", "idx": {"$gte": lo, "$lte": hi}})
    rows = [Episode.model_validate(d) if spec.authority else blind(d) for d in docs]
    rows = [e for e in rows if not failed(e)]   # S2: failed-episode records keep pairing, never feed learning
    return sorted(rows, key=lambda e: e.idx)


def backward_for(h: Any, arm: str) -> RoundHook:
    """Return `async (round, (lo, hi)) -> None`: observe the round's misses, then the arm's write path
    (episodic pass → adjudicator → lifecycle, or the direct writer), then the lifecycle sweep."""
    spec: ArmSpec = h.arms[arm]
    s = h.settings

    async def none(round_: int, idx_range: tuple[int, int]) -> None:
        _trace(h).event("backward.round", {"arm": arm, "round": round_, "write_path": spec.write_path.value})

    if spec.write_path is WritePath.NONE:
        return none

    async def hook(round_: int, idx_range: tuple[int, int]) -> None:
        lo, hi = idx_range
        trace = _trace(h)
        trace.event("backward.round", {"arm": arm, "round": round_, "idx_range": [lo, hi],
                                       "write_path": spec.write_path.value})
        episodes = await round_episodes(h, arm, lo, hi)
        try:
            if spec.write_path is WritePath.SELF_GRADE:
                await direct_writer_for(h, arm).grade(episodes, round_=round_, at_idx=hi)
            elif not spec.authority:
                raise RuntimeError(f"write path {spec.write_path} needs an authority to read misses")
            else:
                deps = _deps(h, arm)
                observer = _collaborator(h, arm, "observer", "munchhausen.learn.observe", "Observer", deps)
                misses = [e for e in episodes if not e.correct]
                sem = asyncio.Semaphore(max(1, s.workers_per_arm))

                async def observe(e: Episode) -> list[Any]:
                    async with sem:
                        return await observer.observe(e, round_)

                observed = await asyncio.gather(*(observe(e) for e in misses))
                if spec.write_path is WritePath.DIRECT:
                    writer = direct_writer_for(h, arm)
                    for e, obs in zip(misses, observed, strict=True):
                        await writer.write(e, obs, round_=round_, at_idx=hi)
                else:
                    deps["nominator"] = _collaborator(h, arm, "nominator", "munchhausen.learn.nominate",
                                                      "Nominator", deps)
                    episodic = _collaborator(h, arm, "episodic", "munchhausen.learn.episodic", "EpisodicPass", deps)
                    if "idx_range" in inspect.signature(episodic.run).parameters:
                        await episodic.run(s.run_id, arm, round_, idx_range=(lo, hi))
                    else:
                        await episodic.run(s.run_id, arm, round_)
        except NotImplementedError as e:
            _unavailable(h, arm, round_, spec.write_path.value, e)
        await lifecycle_for(h, arm).sweep(s.run_id, arm, hi)

    return hook
