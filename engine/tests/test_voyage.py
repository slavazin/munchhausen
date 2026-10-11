"""Voyage call path (impl/voyage.py): cache, micro-batching, spend rows, retries. Offline: fake client and store."""

from __future__ import annotations

import asyncio
import hashlib
import math
from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from munchhausen.agent.usage import CURRENT_EPISODE_ID
from munchhausen.config import Settings
from munchhausen.domain.registers import SpendRow
from munchhausen.impl.representation import VoyageRepresentation
from munchhausen.impl.reranker import VoyageReranker
from munchhausen.impl.voyage import embed_cache_key, rerank_cache_key, unwrap

DIM = 4


def vec(text: str, model: str = "voyage-4") -> list[float]:
    h = hashlib.sha256(f"{model}:{text}".encode()).digest()
    return [b / 255 for b in h[:DIM]]


class FakeVoyageError(Exception):
    def __init__(self, status: int, headers: dict[str, str] | None = None) -> None:
        super().__init__(f"status {status}")
        self.http_status, self.headers = status, headers or {}


class FakeClient:
    def __init__(self, fail: Sequence[Exception] = ()) -> None:
        self.embed_calls: list[dict[str, Any]] = []
        self.rerank_calls: list[dict[str, Any]] = []
        self._fail = list(fail)

    def _maybe_fail(self) -> None:
        if self._fail:
            raise self._fail.pop(0)

    async def embed(self, texts: list[str], *, model: str, input_type: str, output_dimension: int) -> Any:
        await asyncio.sleep(0)
        self.embed_calls.append({"texts": list(texts), "model": model, "input_type": input_type})
        self._maybe_fail()
        return SimpleNamespace(embeddings=[vec(t, model) for t in texts], total_tokens=3 * len(texts))

    async def rerank(self, query: str, documents: list[str], *, model: str, top_k: int | None) -> Any:
        await asyncio.sleep(0)
        self.rerank_calls.append({"query": query, "documents": list(documents), "top_k": top_k})
        self._maybe_fail()
        order = sorted(range(len(documents)), key=lambda i: -len(documents[i]))[: top_k or len(documents)]
        return SimpleNamespace(results=[SimpleNamespace(index=i, relevance_score=1.0 / (r + 1))
                                        for r, i in enumerate(order)], total_tokens=10)


class FakeCache:
    def __init__(self) -> None:
        self.rows: dict[str, Any] = {}

    async def get_many(self, ids: Sequence[str]) -> dict[str, Any]:
        return {i: self.rows[i] for i in ids if i in self.rows}

    async def put_many(self, rows: Sequence[Any]) -> None:
        for r in rows:
            self.rows[r.id] = r


class FakeSpend:
    def __init__(self) -> None:
        self.rows: list[SpendRow] = []

    async def record(self, row: SpendRow) -> None:
        self.rows.append(row)


def fake_store() -> Any:
    return SimpleNamespace(embedding_cache=FakeCache(), rerank_cache=FakeCache(), spend=FakeSpend())


@pytest.fixture
def s(settings_offline: Settings) -> Settings:
    return settings_offline.model_copy(update={"run_id": "wt-voy-test", "embed_batch_window_ms": 5})


def rep(s: Settings, store: Any, client: FakeClient, model: str = "voyage-4", dim: int = DIM) -> VoyageRepresentation:
    r = VoyageRepresentation(model, dim, settings=s, store=store, client=client)
    r.bind_arm("governed")
    return r


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_fifty_concurrent_embeds_coalesce(s: Settings) -> None:
    client, store = FakeClient(), fake_store()
    r = rep(s, store, client)

    async def go() -> list[np.ndarray]:
        return await asyncio.gather(*(r.embed([f"noticed {i}"], "observation") for i in range(50)))

    out = run(go())
    assert len(client.embed_calls) <= math.ceil(50 / s.embed_batch_max) == 1
    assert [o.shape for o in out] == [(1, DIM)] * 50
    assert all(np.allclose(o[0], vec(f"noticed {i}")) for i, o in enumerate(out))
    assert r.stats()["api_calls"] == 1 and r.stats()["cache_misses"] == 50


def test_batch_max_splits_requests(s: Settings) -> None:
    client = FakeClient()
    r = rep(s.model_copy(update={"embed_batch_max": 16}), fake_store(), client)

    async def go() -> None:
        await asyncio.gather(*(r.embed([f"q{i}"], "query") for i in range(50)))

    run(go())
    assert len(client.embed_calls) == math.ceil(50 / 16)
    assert all(len(c["texts"]) <= 16 for c in client.embed_calls)


def test_token_cap_splits_requests(s: Settings) -> None:
    client = FakeClient()
    r = rep(s.model_copy(update={"embed_batch_max_tokens": 100, "embed_chars_per_token": 1.0}), fake_store(), client)
    run(r.embed(["x" * 60, "y" * 60, "z" * 60], "query"))
    assert [len(c["texts"]) for c in client.embed_calls] == [1, 1, 1]


def test_input_types_batch_separately(s: Settings) -> None:
    client = FakeClient()
    r = rep(s, fake_store(), client)

    async def go() -> None:
        await asyncio.gather(r.embed(["a"], "query"), r.embed(["a"], "observation"), r.embed(["b"], "decision"))

    run(go())
    assert sorted((c["input_type"], tuple(c["texts"])) for c in client.embed_calls) == [
        ("document", ("a", "b")), ("query", ("a",))]


def test_cache_hit_makes_no_call(s: Settings) -> None:
    store = fake_store()
    first, second = FakeClient(), FakeClient()
    texts = [f"V question {i}" for i in range(40)]
    a = run(rep(s, store, first).embed(texts, "query"))
    r2 = rep(s, store, second)
    b = run(r2.embed(texts, "query"))
    assert len(first.embed_calls) == 1 and second.embed_calls == []
    assert np.array_equal(a, b)
    assert r2.stats()["cache_hits"] == 40 and r2.stats()["api_calls"] == 0
    assert len(store.spend.rows) == 1   # the hit pass writes no spend row


def test_partial_hit_sends_only_misses(s: Settings) -> None:
    store, client = fake_store(), FakeClient()
    run(rep(s, store, FakeClient()).embed(["a", "b"], "query"))
    out = run(rep(s, store, client).embed(["a", "c", "b"], "query"))
    assert [c["texts"] for c in client.embed_calls] == [["c"]]
    assert np.allclose(out, [vec("a"), vec("c"), vec("b")])


def test_other_embedder_or_dim_misses_the_cache(s: Settings) -> None:
    store = fake_store()
    run(rep(s, store, FakeClient()).embed(["same text"], "query"))
    lite, wide, doc = FakeClient(), FakeClient(), FakeClient()
    run(rep(s, store, lite, model="voyage-4-lite").embed(["same text"], "query"))
    run(rep(s, store, wide, dim=DIM + 1).embed(["same text"], "query"))
    run(rep(s, store, doc).embed(["same text"], "observation"))
    assert len(lite.embed_calls) == len(wide.embed_calls) == len(doc.embed_calls) == 1


def test_cache_off_always_calls(s: Settings) -> None:
    store, client = fake_store(), FakeClient()
    r = rep(s.model_copy(update={"embed_cache": False}), store, client)
    run(r.embed(["a"], "query"))
    run(r.embed(["a"], "query"))
    assert len(client.embed_calls) == 2 and store.embedding_cache.rows == {}


def test_order_preserved_with_duplicates(s: Settings) -> None:
    client = FakeClient()
    r = rep(s, fake_store(), client)
    texts = ["b", "a", "b", "c", "a", "b"]

    async def go() -> tuple[np.ndarray, np.ndarray]:
        return await asyncio.gather(r.embed(texts, "query"), r.embed(["c", "d", "a"], "query"))

    one, two = run(go())
    assert len(client.embed_calls) == 1 and sorted(client.embed_calls[0]["texts"]) == ["a", "b", "c", "d"]
    assert np.allclose(one, [vec(t) for t in texts]) and np.allclose(two, [vec(t) for t in ("c", "d", "a")])


def test_empty_input_makes_no_call(s: Settings) -> None:
    client = FakeClient()
    assert run(rep(s, fake_store(), client).embed([], "query")).shape == (0, DIM)
    assert client.embed_calls == []


def test_spend_row_per_api_call(s: Settings) -> None:
    store, client = fake_store(), FakeClient()
    r = rep(s.model_copy(update={"embed_batch_max": 2}), store, client)

    async def go() -> None:
        CURRENT_EPISODE_ID.set("E-7")
        await r.embed(["a", "b", "c"], "query")

    run(go())
    assert len(client.embed_calls) == len(store.spend.rows) == 2
    row = store.spend.rows[0]
    assert row.meta == {"run_id": "wt-voy-test", "arm": "governed", "stage": "embed", "model": "voyage-4",
                        "episode_id": "E-7"}
    assert row.ok and row.tokens_in == 6 and row.tokens_out == 0
    assert row.usd == pytest.approx(s.usd("voyage-4", 6, 0)) and row.usd > 0


def test_unbound_arm_is_unattributed(s: Settings) -> None:
    store = fake_store()
    run(VoyageRepresentation("voyage-4", DIM, settings=s, store=store, client=FakeClient()).embed(["a"], "query"))
    assert store.spend.rows[0].meta["arm"] == s.voyage_unattributed_arm


def test_rerank_cache_hits(s: Settings) -> None:
    store, client = fake_store(), FakeClient()
    rr = VoyageReranker("rerank-3", settings=s, store=store, client=client)
    rr.bind_arm("naive")
    docs = ["short", "a longer one", "mid size"]
    first = run(rr.rerank("q", docs, top_k=2))
    again = run(VoyageReranker("rerank-3", settings=s, store=store, client=client).rerank("q", docs, top_k=2))
    assert first == again == [(1, 1.0), (2, 0.5)]
    assert len(client.rerank_calls) == 1
    run(rr.rerank("q", docs, top_k=3))           # another top_k is another key
    run(rr.rerank("q", [*docs, "x"], top_k=2))   # another document set too
    assert len(client.rerank_calls) == 3
    assert [r.meta["stage"] for r in store.spend.rows] == ["rerank"] * 3
    assert store.spend.rows[0].meta["arm"] == "naive" and store.spend.rows[0].tokens_in == 10


def test_429_is_retried_then_succeeds(s: Settings) -> None:
    store = fake_store()
    client = FakeClient(fail=[FakeVoyageError(429, {"retry-after": "2"}), FakeVoyageError(503)])
    r = rep(s, store, client)
    slept: list[float] = []

    async def sleep(d: float) -> None:
        slept.append(d)

    r._meter.sleep = sleep
    out = run(r.embed(["a"], "query"))
    assert np.allclose(out, [vec("a")])
    assert len(client.embed_calls) == 3 and slept[0] == 2.0 and len(slept) == 2
    assert [(row.ok, row.error) for row in store.spend.rows] == [
        (False, "FakeVoyageError(429)"), (False, "FakeVoyageError(503)"), (True, None)]
    assert r.stats()["retries"] == 2 and r.stats()["api_errors"] == 2


def test_persistent_429_raises(s: Settings) -> None:
    store = fake_store()
    client = FakeClient(fail=[FakeVoyageError(429)] * 10)
    r = rep(s.model_copy(update={"voyage_max_retries": 2}), store, client)

    async def sleep(d: float) -> None:
        return None

    r._meter.sleep = sleep
    with pytest.raises(FakeVoyageError):
        run(r.embed(["a", "b"], "query"))
    assert len(client.embed_calls) == 3 and len(store.spend.rows) == 3
    assert store.embedding_cache.rows == {}


def test_retry_budget_bounds_total_wait(s: Settings) -> None:
    client = FakeClient(fail=[FakeVoyageError(429, {"retry-after": "20"})] * 3)
    r = rep(s.model_copy(update={"voyage_retry_max_wait_s": 30.0}), fake_store(), client)
    slept: list[float] = []

    async def sleep(d: float) -> None:
        slept.append(d)

    r._meter.sleep = sleep
    with pytest.raises(FakeVoyageError):
        run(r.embed(["a"], "query"))
    assert slept == [20.0]


def test_client_error_is_not_retried(s: Settings) -> None:
    client = FakeClient(fail=[FakeVoyageError(400)])
    with pytest.raises(FakeVoyageError):
        run(rep(s, fake_store(), client).embed(["a"], "query"))
    assert len(client.embed_calls) == 1


def test_failure_reaches_every_coalesced_caller(s: Settings) -> None:
    client = FakeClient(fail=[FakeVoyageError(401)])
    r = rep(s, fake_store(), client)

    async def go() -> list[Any]:
        return await asyncio.gather(*(r.embed([f"t{i}"], "query") for i in range(5)), return_exceptions=True)

    out = run(go())
    assert len(client.embed_calls) == 1 and all(isinstance(o, FakeVoyageError) for o in out)


def test_tenacity_wrapper_is_unwrapped() -> None:
    inner = FakeVoyageError(429)
    wrapped = Exception("RetryError")
    wrapped.last_attempt = SimpleNamespace(exception=lambda: inner)  # type: ignore[attr-defined]
    assert unwrap(wrapped) is inner and unwrap(inner) is inner


def test_slow_cache_reads_still_coalesce(s: Settings) -> None:
    """The cache is read once per batch, so Atlas latency cannot spread callers past the window."""

    class SlowCache(FakeCache):
        reads = 0

        async def get_many(self, ids: Sequence[str]) -> dict[str, Any]:
            SlowCache.reads += 1
            await asyncio.sleep(0.02)
            return await super().get_many(ids)

    store, client = fake_store(), FakeClient()
    store.embedding_cache = SlowCache()
    r = rep(s, store, client)

    async def go() -> None:
        await asyncio.gather(*(r.embed([f"q{i}", "shared"], "query") for i in range(40)))

    run(go())
    assert SlowCache.reads == 1 and len(client.embed_calls) == 1 and len(client.embed_calls[0]["texts"]) == 41


def test_cache_key_formats_are_pinned() -> None:
    """One-way door: changing either format orphans every cached row in Atlas."""
    assert embed_cache_key("voyage-4", 1024, "query", "How many?") == hashlib.sha256(
        b'["voyage-4",1024,"query","How many?"]').hexdigest()
    d = hashlib.sha256(b"doc").hexdigest()
    assert rerank_cache_key("rerank-3", "q", ["doc"], 5) == hashlib.sha256(
        f'["rerank-3","q",["{d}"],5]'.encode()).hexdigest()
