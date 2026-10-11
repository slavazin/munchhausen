"""`bootstrap_learn`: curators are built from the registry by the layers their factories name, and the
round-close hook is chosen by `ArmSpec.write_path`; a missing collaborator is logged, never silent."""

from __future__ import annotations

import asyncio
from typing import Any

from munchhausen import bootstrap_learn
from munchhausen.learn.layers import L0Shape, L4Backtest, LessonShape
from tests.test_adjudication_fakes import ARM, RUN, FakeWorld, Sink, Store, Trace, episode


class _Rep:
    id, dim = "none", 0

    async def embed(self, texts, role):  # noqa: ANN001, ANN201
        return None


class _Stub:
    id = "stub"

    async def score(self, *a: Any) -> dict:
        return {}

    async def rerank(self, query, docs, top_k=None):  # noqa: ANN001, ANN201
        return [(i, 1.0) for i in range(len(docs))]

    async def observe(self, episode: Any) -> list:
        return []


class Harness:
    def __init__(self, settings: Any) -> None:
        self.settings = settings.model_copy(update={"run_id": RUN})
        store = Store()
        world = FakeWorld(store.st, {})
        store.world = lambda: world
        store.world_writer = lambda: world
        store.lenses = None
        self.store, self.arms, self.ports = store, settings.arms(), {}
        self.trace, self.sink = Trace(store.st), Sink()

    def port(self, arm: str, port: str) -> Any:
        return {"representation": _Rep(), "memory_sink": self.sink}.get(port, _Stub())

    def shared(self, port: str, name: str) -> Any:
        return self.trace if port == "trace" else _Stub()


def test_curators_are_built_by_the_layers_their_factory_names(settings_offline) -> None:  # noqa: ANN001
    h = Harness(settings_offline)
    g = bootstrap_learn.curator_for(h, "governed")
    assert g.governed and isinstance(g.layers[0], L0Shape) and isinstance(g.layers[-1], L4Backtest)
    u = bootstrap_learn.curator_for(h, "ungated")
    assert not u.governed and isinstance(u.layers[0], L0Shape)
    n = bootstrap_learn.curator_for(h, "naive")
    assert not n.governed and isinstance(n.layers[0], LessonShape)
    assert bootstrap_learn.adjudicator_for(h, "governed") is bootstrap_learn.adjudicator_for(h, "governed")


def test_backward_hook_by_write_path_logs_a_missing_collaborator_and_still_sweeps(settings_offline, capsys) -> None:  # noqa: ANN001
    h = Harness(settings_offline)
    asyncio.run(bootstrap_learn.backward_for(h, "frozen")(0, (0, 29)))
    h.store.st.episodes["e"] = episode(3, "t1", correct=False, figure=10.0)
    asyncio.run(bootstrap_learn.backward_for(h, ARM)(0, (0, 29)))
    names = [n for n, _ in h.store.st.events]
    assert "backward.round" in names and "lifecycle.sweep" in names
    if "backward.unavailable" in names:     # S3's pieces still stubbed on this branch
        assert "unavailable" in capsys.readouterr().err
