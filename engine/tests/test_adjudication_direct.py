"""The direct write path runs its model calls concurrently and admits in order: whatever order the lesson
calls finish in, the admitted and merged decisions equal the sequential result; concurrency stays within
DIRECT_CONCURRENCY; one failed call leaves the others applied."""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np

from munchhausen.domain.common import DecisionKind
from munchhausen.domain.lesson import Lesson
from munchhausen.learn.adjudicate import Adjudicator
from munchhausen.learn.curators import naive
from munchhausen.learn.direct import DirectWriter
from munchhausen.learn.layers import LessonShape
from tests.test_adjudication import World
from tests.test_adjudication_fakes import observation


class _Rep:
    """Two directions: lessons titled alike merge (cosine 1), the others never do (cosine 0)."""

    id, dim = "fake-emb", 2

    async def embed(self, texts, role):  # noqa: ANN001, ANN201
        return np.asarray([[1.0, 0.0] if "alpha" in t else [0.0, 1.0] for t in texts])


class SlowModels:
    """Lesson calls finish in reverse order of issue; tracks how many are in flight."""

    def __init__(self, n: int, fail: set[str] | None = None) -> None:
        self.n, self.fail, self.order, self.in_flight, self.peak = n, fail or set(), [], 0, 0

    async def lesson(self, episode: Any, obs: Any) -> Lesson:
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        k = len(self.order)
        self.order.append(obs.id)
        await asyncio.sleep(0.002 * (self.n - k))
        self.in_flight -= 1
        if obs.id in self.fail:
            raise RuntimeError("429")
        title = "Active customers alpha rule" if episode.idx % 3 else "Active customers beta rule"
        return Lesson(title=title, kind=DecisionKind.TAXONOMIC,
                      payload=f"Count by RULE status field {episode.idx % 3}.")


def _items(w: World) -> list[tuple[Any, list[Any]]]:
    misses = sorted((e for e in w.store.st.episodes.values() if not e.correct), key=lambda e: e.idx)
    out = []
    for e in misses:
        o = observation(e)
        w.store.st.observations[o.id] = o
        out.append((e, [o]))
    return out


def _writer(w: World, models: Any, concurrency: int) -> DirectWriter:
    s = w.store
    adj = Adjudicator(curator=naive(LessonShape()), drafts=s.drafts, decisions=s.decisions, fires=s.fires,
                      lifecycle=w.lifecycle(), view_name=lambda c, d: f"{c}__{d}", representation=_Rep(),
                      trace=w.trace)
    return DirectWriter(models=models, adjudicator=adj, decisions=s.decisions, observations=s.observations,
                        representation=_Rep(), merge=True, merge_cosine=0.92, concurrency=concurrency,
                        trace=w.trace)


def _snapshot(w: World) -> list[tuple[str, str, str | None, str]]:
    return [(d.id, d.lifecycle.status.value, d.lifecycle.converged_into, d.payload)
            for d in w.store.st.decisions.values()]


def _run(concurrency: int, fail: set[str] | None = None) -> tuple[World, SlowModels, list[str]]:
    w = World(n_per_template=4)
    items = _items(w)
    models = SlowModels(len(items), fail)
    out = asyncio.run(_writer(w, models, concurrency).write_round(items, round_=1, at_idx=30))
    return w, models, out


def test_concurrent_lessons_admit_exactly_as_sequential() -> None:
    seq_w, _, seq_out = _run(1)
    par_w, models, par_out = _run(6)
    assert models.peak > 1, "the calls ran concurrently"
    assert par_out == seq_out and _snapshot(par_w) == _snapshot(seq_w)
    statuses = [s for _, s, _, _ in _snapshot(par_w)]
    assert "converged" in statuses and statuses.count("admitted") == 2, "merges happened, in order"


def test_concurrency_never_exceeds_the_knob() -> None:
    _, models, _ = _run(3)
    assert models.peak == 3


def test_one_failed_call_leaves_the_others_applied() -> None:
    w0 = World(n_per_template=4)
    victim = _items(w0)[2][1][0].id
    w, models, out = _run(6, fail={victim})
    assert len(out) == len(models.order) - 1
    assert w.store.st.observations[victim].disposition.value == "open"
    spent = [o for o in w.store.st.observations.values() if o.disposition.value == "spent"]
    assert len(spent) == len(models.order) - 1
    assert any(n == "lesson.failed" for n, _ in w.store.st.events)
