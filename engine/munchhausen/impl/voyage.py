"""The shared Voyage call path (embed + rerank): content-hash cache keys, retries with backoff, spend rows,
and the micro-batcher that coalesces concurrent embed calls into one request.

Every actual API call (each attempt, failed ones too) writes one `spend` row; a cache hit writes none and is
counted in `VoyageMeter.stats()`. A persistent failure raises after the retry budget: nothing degrades
silently to a null vector.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import sys
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from munchhausen.agent.usage import CURRENT_EPISODE_ID
from munchhausen.config import Settings
from munchhausen.domain.registers import SpendRow

log = logging.getLogger(__name__)


# --- cache keys (one-way doors: changing either orphans every cached row) ---------------------------------


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _key(parts: list[Any]) -> str:
    return sha256(json.dumps(parts, ensure_ascii=False, separators=(",", ":")))


def embed_cache_key(embedder_id: str, dim: int, input_type: str, text: str) -> str:
    """sha256 of the compact JSON array `[embedder_id, dim, input_type, text]`."""
    return _key([embedder_id, dim, input_type, text])


def rerank_cache_key(model: str, query: str, documents: Sequence[str], top_k: int | None) -> str:
    """sha256 of the compact JSON array `[model, query, [sha256(doc)…], top_k]`."""
    return _key([model, query, [sha256(d) for d in documents], top_k])


# --- errors -----------------------------------------------------------------------------------------------


_TRANSIENT = ("RateLimitError", "ServiceUnavailableError", "ServerError", "Timeout", "TryAgain",
              "APIConnectionError", "TimeoutError")


def unwrap(error: BaseException) -> BaseException:
    """The Voyage client wraps a retryable error in tenacity's `RetryError` even with `max_retries=0`."""
    attempt = getattr(error, "last_attempt", None)
    inner = attempt.exception() if attempt is not None else None
    return inner if isinstance(inner, BaseException) else error


def status_of(error: BaseException) -> int | None:
    status = getattr(error, "http_status", None) or getattr(error, "status_code", None)
    return int(status) if status is not None else None


def error_label(error: BaseException) -> str:
    status = status_of(error)
    return f"{type(error).__name__}({status})" if status is not None else type(error).__name__


def transient(error: BaseException, statuses: Sequence[int]) -> bool:
    status = status_of(error)
    if status is not None:
        return status in statuses
    return type(error).__name__ in _TRANSIENT or isinstance(error, (asyncio.TimeoutError, ConnectionError))


def retry_after_s(error: BaseException) -> float | None:
    headers = getattr(error, "headers", None) or {}
    raw = None
    for k in ("retry-after", "Retry-After"):
        if k in headers:
            raw = headers[k]
            break
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


# --- meter: retries, spend, stats -------------------------------------------------------------------------


@dataclass
class VoyageMeter:
    """One per port instance. `arm` is bound by the composition root (`bind_arm`); spend rows carry it."""

    settings: Settings
    spend: Any = None                       # SpendRepository | None
    stage: str = ""
    arm: str | None = None
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
    counts: dict[str, int] = field(default_factory=lambda: {
        "api_calls": 0, "api_errors": 0, "retries": 0, "texts_sent": 0, "tokens": 0,
        "cache_hits": 0, "cache_misses": 0, "lost_spend_writes": 0, "lost_cache_writes": 0})

    def stats(self) -> dict[str, int]:
        return dict(self.counts)

    async def call(self, model: str, fn: Callable[[], Awaitable[Any]], *, n_texts: int,
                   episode_id: str | None) -> Any:
        """Run `fn` (one API request) with backoff on transient errors; one spend row per attempt."""
        s = self.settings
        waited = 0.0
        for attempt in range(s.voyage_max_retries + 1):
            t0 = time.monotonic()
            try:
                res = await fn()
            except Exception as raw:
                err = unwrap(raw)
                self.counts["api_calls"] += 1
                self.counts["api_errors"] += 1
                await self._record(model, tokens=0, latency_ms=_ms(t0), episode_id=episode_id, error=err)
                if not transient(err, s.voyage_retry_statuses) or attempt >= s.voyage_max_retries:
                    raise err from (raw if err is not raw else None)
                hinted = retry_after_s(err)
                delay = hinted if hinted is not None else random.uniform(  # noqa: S311 (jitter, not crypto)
                    0.0, min(s.voyage_retry_cap_s, s.voyage_retry_base_s * 2 ** attempt))
                delay = min(delay, s.voyage_retry_cap_s)
                if waited + delay > s.voyage_retry_max_wait_s:
                    raise err from (raw if err is not raw else None)
                waited += delay
                self.counts["retries"] += 1
                log.warning("voyage %s %s: %s; retry %d in %.1fs", self.stage, model, error_label(err),
                            attempt + 1, delay)
                await self.sleep(delay)
                continue
            tokens = int(getattr(res, "total_tokens", 0) or 0)
            self.counts["api_calls"] += 1
            self.counts["texts_sent"] += n_texts
            self.counts["tokens"] += tokens
            await self._record(model, tokens=tokens, latency_ms=_ms(t0), episode_id=episode_id)
            return res
        raise AssertionError("unreachable: the loop returns or raises")

    async def _record(self, model: str, *, tokens: int, latency_ms: int, episode_id: str | None,
                      error: BaseException | None = None) -> None:
        if self.spend is None:
            return
        s = self.settings
        meta = {"run_id": s.run_id, "arm": self.arm or s.voyage_unattributed_arm, "stage": self.stage,
                "model": model, **({"episode_id": episode_id} if episode_id else {})}
        row = SpendRow(at=datetime.now(UTC), meta=meta, tokens_in=tokens, tokens_out=0, latency_ms=latency_ms,
                       usd=s.usd(model, tokens, 0), request_id=getattr(error, "request_id", None),
                       ok=error is None, error=error_label(error) if error is not None else None)
        try:
            await self.spend.record(row)
        except Exception as e:   # a lost spend row must not fail the call; counted in stats()
            self.counts["lost_spend_writes"] += 1
            print(f"[spend] voyage row not written ({type(e).__name__}): {self.stage} {model}", file=sys.stderr)


def _ms(t0: float) -> int:
    return int((time.monotonic() - t0) * 1000)


def current_episode_id() -> str | None:
    return CURRENT_EPISODE_ID.get()


# --- micro-batcher ----------------------------------------------------------------------------------------


Flush = Callable[[list[str], str | None], Awaitable[list[list[float]]]]


class MicroBatcher:
    """Coalesces concurrent `submit` calls into requests of at most `max_texts` texts and `max_tokens`
    estimated tokens, waiting at most `window_s` after the first queued text. Identical texts share one
    slot while queued or in flight. Results return to each caller in its own order."""

    def __init__(self, flush: Flush, *, window_s: float, max_texts: int, max_tokens: int,
                 chars_per_token: float) -> None:
        self._flush_fn = flush
        self._window_s, self._max_texts, self._max_tokens = window_s, max(1, max_texts), max_tokens
        self._cpt = chars_per_token
        self._queue: list[str] = []
        self._queue_tokens = 0
        self._queue_episodes: set[str | None] = set()
        self._futures: dict[str, asyncio.Future[list[float]]] = {}   # queued or in flight
        self._timer: asyncio.TimerHandle | None = None
        self._tasks: set[asyncio.Task[None]] = set()

    async def submit(self, texts: Sequence[str], episode_id: str | None = None) -> list[list[float]]:
        loop = asyncio.get_running_loop()
        futs: list[asyncio.Future[list[float]]] = []
        for t in texts:
            fut = self._futures.get(t)
            if fut is None:
                est = self._tokens(t)
                if self._queue and (len(self._queue) >= self._max_texts or self._queue_tokens + est > self._max_tokens):
                    self._flush_now()
                fut = loop.create_future()
                self._futures[t] = fut
                self._queue.append(t)
                self._queue_tokens += est
                self._queue_episodes.add(episode_id)
                if len(self._queue) >= self._max_texts:
                    self._flush_now()
                elif self._timer is None:
                    self._timer = loop.call_later(self._window_s, self._flush_now)
            futs.append(fut)
        out = await asyncio.gather(*(asyncio.shield(f) for f in futs), return_exceptions=True)
        for r in out:
            if isinstance(r, BaseException):
                raise r
        return list(out)  # type: ignore[arg-type]

    def _tokens(self, text: str) -> int:
        return int(len(text) / self._cpt) + 1

    def _flush_now(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        if not self._queue:
            return
        batch, episodes = self._queue, self._queue_episodes
        self._queue, self._queue_tokens, self._queue_episodes = [], 0, set()
        episode_id = next(iter(episodes)) if len(episodes) == 1 else None
        task = asyncio.get_running_loop().create_task(self._send(batch, episode_id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _send(self, batch: list[str], episode_id: str | None) -> None:
        try:
            vectors = await self._flush_fn(batch, episode_id)
            if len(vectors) != len(batch):
                raise RuntimeError(f"embedder returned {len(vectors)} vectors for {len(batch)} texts")
        except Exception as e:
            for t in batch:
                fut = self._futures.pop(t)
                if not fut.done():
                    fut.set_exception(e)
                    fut.exception()   # retrieved: every caller re-raises it through gather
            return
        except BaseException:         # cancelled (loop shutdown): the waiting callers are cancelled too
            for t in batch:
                self._futures.pop(t).cancel()
            raise
        for t, v in zip(batch, vectors, strict=True):
            fut = self._futures.pop(t)
            if not fut.done():
                fut.set_result(v)
