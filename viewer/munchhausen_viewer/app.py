"""Viewer (SPEC § 17): FastAPI + SSE + one static page. Reads through the engine's `ReadModel` port only;
the injection control and the owner port (L5) go through engine services handed in by the composition
root (`munchhausen viewer`). No route returns a secret or a connection string.

Panes: the agent's latest episode (the hero) · decision store per arm · fire ticker · curves (side pane)
· injection control · `why`. Change streams on `fires`, `decisions`, `rounds`, `tool_access` (and
`episodes`, for the hero) feed `/api/events`; when a change stream is unavailable the bus polls the
timeline every POLL_INTERVAL_S. Every read takes `at`, so the replay scrubber drives every pane.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from munchhausen.loop.inject import InjectionRequest, capped_templates
from munchhausen.metrics.paired import paired_difference
from munchhausen_viewer.services import ViewerServices

STATIC = Path(__file__).parent / "static"
ARMS_QUERY = Query(default=None)


class EventBus:
    """Fan-out of change events to SSE subscribers. `mode` says what feeds it: change-stream or poll."""

    def __init__(self) -> None:
        self._subs: set[asyncio.Queue[tuple[str, Any]]] = set()
        self.mode = "starting"
        self.last_error: str | None = None

    def subscribe(self) -> asyncio.Queue[tuple[str, Any]]:
        q: asyncio.Queue[tuple[str, Any]] = asyncio.Queue(maxsize=1000)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[tuple[str, Any]]) -> None:
        self._subs.discard(q)

    def publish(self, kind: str, data: Any) -> None:
        for q in list(self._subs):
            with contextlib.suppress(asyncio.QueueFull):
                q.put_nowait((kind, data))


async def pump(svc: ViewerServices, bus: EventBus) -> None:
    """Change streams first; on failure fall back to polling the timeline (SPEC § 20.2 fallback)."""
    s = svc.settings
    try:
        bus.mode = "change-stream"
        bus.publish("mode", {"mode": bus.mode})
        async for ev in svc.read_model.changes(svc.run_id, s.viewer_watch):
            bus.publish("change", ev)
    except asyncio.CancelledError:
        raise
    except Exception as e:  # noqa: BLE001 — any driver failure degrades to polling, never kills the viewer
        bus.last_error = type(e).__name__
    bus.mode = "poll"
    bus.publish("mode", {"mode": bus.mode, "error": bus.last_error})
    last: Any = None
    while True:
        try:
            tl = await svc.read_model.timeline(svc.run_id)
            sig = (tl.get("max_idx"), json.dumps(tl.get("counts"), sort_keys=True))
            if sig != last:
                last = sig
                bus.publish("change", {"collection": "_poll", "run_id": svc.run_id, "idx": tl.get("max_idx")})
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            bus.last_error = type(e).__name__
        await asyncio.sleep(s.poll_interval_s)


def readings(paired: list[dict[str, Any]], svc: ViewerServices) -> list[dict[str, Any]]:
    """Paired difference vs the reference arm per drift segment, with interval and n (SPEC § 22.7)."""
    s = svc.settings
    bounds = [0, s.d1_at, s.d2_at, s.run_length]
    out = []
    arms = sorted({p["arm"] for p in paired})
    for arm in arms:
        rows = [p for p in paired if p["arm"] == arm]
        last = max((p["idx"] for p in rows), default=0) + 1
        for lo, hi in zip(bounds, bounds[1:], strict=False):
            hi = min(hi, last)
            d = [p["d"] for p in rows if lo <= p["idx"] < hi]
            if not d:
                continue
            r = paired_difference(d, [0.0] * len(d), n_boot=s.bootstrap_n, level=s.ci_level, seed=s.stream_seed)
            out.append({"arm": arm, "reference": svc.reference_arm, "segment": [lo, hi], "diff": r.diff,
                        "lo": r.lo, "hi": r.hi, "n": r.n, "level": r.level,
                        "unit": "first-attempt accuracy, difference in proportion",
                        "population": f"stream episodes idx [{lo}, {hi}) present in both arms"})
    return out


class InjectBody(BaseModel):
    run: str | None = None
    arm: str | None = None
    templates: list[str] = Field(min_length=1)
    figure: float | list[str]
    phrasing: str = Field(min_length=1, max_length=200)
    per_template: int | None = Field(default=None, ge=1, le=5)


class OwnerBody(BaseModel):
    id: str
    verdict: str
    note: str = ""


def create_app(svc: ViewerServices | None = None) -> FastAPI:
    bus = EventBus()
    jobs: dict[str, dict[str, Any]] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        task = asyncio.create_task(pump(svc, bus)) if svc is not None else None
        yield
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        if svc is not None and svc.close is not None:
            await svc.close()

    app = FastAPI(title="Munchhausen", lifespan=lifespan)
    app.state.bus, app.state.jobs = bus, jobs
    if svc is not None:   # Host header check: a page on another origin cannot drive the engine via DNS rebinding
        app.add_middleware(TrustedHostMiddleware,
                           allowed_hosts=sorted({*svc.settings.viewer_allowed_hosts, svc.settings.viewer_host}))

    def prune_jobs(limit: int) -> None:
        done = [k for k, j in jobs.items() if j["status"] != "running"]
        while len(jobs) >= limit and done:
            jobs.pop(done.pop(0))

    def need() -> ViewerServices:
        if svc is None:
            raise HTTPException(503, "viewer started without services; run `munchhausen viewer`")
        return svc

    def run_of(run: str | None) -> str:
        return run or need().run_id

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "bus": bus.mode}

    @app.get("/api/config")
    async def config() -> dict[str, Any]:
        v = need()
        s = v.settings
        return {"run_id": v.run_id, "mode": v.mode, "bus": bus.mode, "default_arm": v.default_arm,
                "reference_arm": v.reference_arm, "window": v.window,
                "arms": [{"name": a, "authority": sp.authority, "write_path": sp.write_path.value,
                          "consultation": sp.consultation.value, "curator": sp.curator, "claim": sp.claim}
                         for a, sp in v.arms.items()],
                "d1_at": s.d1_at, "d2_at": s.d2_at, "round_size": s.round_size, "run_length": s.run_length,
                "v_every": s.v_every, "v_offset": s.v_offset, "inject_per_template": s.inject_per_template,
                "bar_min_obs": s.bar_min_obs, "bar_min_templates": s.bar_min_templates,
                "backtest": s.backtest_thresholds.model_dump(), "poll_interval_s": s.poll_interval_s,
                "injection": v.injector_for is not None, "owner": v.owner is not None}

    @app.get("/api/runs")
    async def runs() -> list[dict[str, Any]]:
        return await need().read_model.runs()

    @app.get("/api/timeline")
    async def timeline(run: str | None = None) -> dict[str, Any]:
        return await need().read_model.timeline(run_of(run))

    @app.get("/api/decisions")
    async def decisions(arm: str, run: str | None = None, at: int | None = None) -> list[dict[str, Any]]:
        return await need().read_model.decisions(run_of(run), arm, at=at)

    @app.get("/api/fires")
    async def fires(run: str | None = None, at: int | None = None,
                    arms: list[str] | None = ARMS_QUERY) -> list[dict[str, Any]]:
        v = need()
        return await v.read_model.fires(run_of(run), arms or list(v.arms), at=at, limit=v.settings.viewer_fire_limit)

    @app.get("/api/episode")
    async def episode(arm: str, run: str | None = None, at: int | None = None,
                      stream: str | None = None) -> dict[str, Any] | None:
        return await need().read_model.latest_episode(run_of(run), arm, at=at, stream=stream)

    @app.get("/api/drafts")
    async def drafts(arm: str, run: str | None = None, at: int | None = None) -> list[dict[str, Any]]:
        v = need()
        return await v.read_model.drafts(run_of(run), arm, at=at, limit=v.settings.viewer_draft_limit)

    @app.get("/api/draft/{draft_id}")
    async def draft(draft_id: str) -> dict[str, Any]:
        d = await need().read_model.draft(draft_id)
        if d is None:
            raise HTTPException(404, f"no draft {draft_id}")
        return d

    @app.get("/api/curves")
    async def curves(run: str | None = None, at: int | None = None) -> dict[str, Any]:
        v = need()
        c = await v.read_model.curves(run_of(run), reference=v.reference_arm, window=v.window, at=at)
        c["readings"] = readings(c.get("paired", []), v)
        c["drift"] = {"D1": v.settings.d1_at, "D2": v.settings.d2_at}
        return c

    @app.get("/api/why")
    async def why(target: str, run: str | None = None, at: int | None = None,
                  arm: str | None = None) -> dict[str, Any]:
        return await need().read_model.why(run_of(run), target, at=at, arm=arm)

    @app.get("/api/floor/{decision_id}")
    async def floor(decision_id: str) -> dict[str, Any]:
        f = await need().read_model.floor(decision_id)
        if f is None:
            raise HTTPException(404, f"{decision_id} is not a floor decision")
        return f

    @app.get("/api/facets")
    async def facets(run: str | None = None, at: int | None = None) -> list[dict[str, Any]]:
        return await need().read_model.facets(run_of(run), at=at)

    # --- pane 4: injection -------------------------------------------------------------------------

    @app.post("/api/inject")
    async def inject(body: InjectBody) -> dict[str, Any]:
        v = need()
        if v.injector_for is None:
            raise HTTPException(501, "injection is not wired in this mode")
        arm = body.arm or v.default_arm
        if arm not in v.arms or not v.arms[arm].authority:
            raise HTTPException(400, f"arm {arm!r} receives no authority; injection needs one")
        run_id = run_of(body.run)
        if run_id != v.settings.run_id:
            raise HTTPException(400, f"injection writes only to the engine's run {v.settings.run_id!r} (RUN_ID), "
                                     f"not {run_id!r}")
        try:
            templates = capped_templates(body.templates, v.settings.inject_max_templates)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        busy = [j for j in jobs.values() if j["status"] == "running" and j["key"] == (run_id, arm)]
        if busy:
            raise HTTPException(409, f"an injection is already running on {arm} (job {busy[0]['id']})")
        prune_jobs(v.settings.viewer_max_jobs)
        if len(jobs) >= v.settings.viewer_max_jobs:
            raise HTTPException(429, "too many injections in flight")
        job_id = uuid.uuid4().hex[:10]
        req = InjectionRequest(run_id=run_id, arm=arm, templates=templates, figure=body.figure,
                               phrasing=body.phrasing, per_template=body.per_template or v.settings.inject_per_template,
                               job_id=job_id)
        job: dict[str, Any] = {"id": job_id, "status": "running", "steps": [], "result": None, "error": None,
                               "key": (run_id, arm),
                               "request": {"arm": arm, "templates": list(templates), "figure": body.figure,
                                           "phrasing": body.phrasing}}
        jobs[job_id] = job

        def on_step(name: str, payload: dict[str, Any]) -> None:
            job["steps"].append({"step": name, **payload})
            bus.publish("inject", {"job": job_id, "step": name, **payload})

        async def go() -> None:
            try:
                injector = v.injector_for(arm)   # type: ignore[misc]
                if inspect.isawaitable(injector):   # the Atlas injector loads the world's schema first
                    injector = await injector
                res = await injector.run(req, on_step)
                job["result"], job["status"] = res.summary(), "done"
            except NotImplementedError as e:
                job["error"], job["status"] = f"not built yet — {e}", "blocked"
            except Exception as e:  # noqa: BLE001 — the beat reports its failure on screen
                job["error"], job["status"] = f"{type(e).__name__}: {e}", "failed"
            bus.publish("inject", {"job": job_id, "step": job["status"], "error": job["error"]})

        job["task"] = asyncio.create_task(go())
        return {k: x for k, x in job.items() if k not in ("task", "key")}

    @app.get("/api/inject/{job_id}")
    async def inject_status(job_id: str) -> dict[str, Any]:
        if job_id not in jobs:
            raise HTTPException(404, "no such injection")
        return {k: x for k, x in jobs[job_id].items() if k not in ("task", "key")}

    # --- L5 owner port -----------------------------------------------------------------------------

    async def _owner(kind: str, body: OwnerBody) -> dict[str, Any]:
        v = need()
        if v.owner is None:
            raise HTTPException(501, "M3: owner port (adjudication surface) is not wired")
        try:
            port = v.owner()
            fn = port.dispose_draft if kind == "draft" else port.dispose_fire
            return await fn(body.id, body.verdict, body.note)
        except NotImplementedError as e:
            raise HTTPException(501, str(e)) from e
        except ValueError as e:   # the owner port refuses (e.g. admitting injected evidence)
            raise HTTPException(409, str(e)) from e

    @app.post("/api/owner/draft")
    async def owner_draft(body: OwnerBody) -> dict[str, Any]:
        return await _owner("draft", body)

    @app.post("/api/owner/fire")
    async def owner_fire(body: OwnerBody) -> dict[str, Any]:
        return await _owner("fire", body)

    # --- SSE -----------------------------------------------------------------------------------------

    @app.get("/api/events")
    async def events(request: Request) -> StreamingResponse:
        keepalive = need().settings.viewer_sse_keepalive_s

        async def gen() -> AsyncIterator[str]:
            q = bus.subscribe()
            try:
                yield f"event: mode\ndata: {json.dumps({'mode': bus.mode})}\n\n"
                while not await request.is_disconnected():
                    try:
                        kind, data = await asyncio.wait_for(q.get(), timeout=keepalive)
                    except TimeoutError:
                        yield ": keepalive\n\n"
                        continue
                    yield f"event: {kind}\ndata: {json.dumps(data, default=str)}\n\n"
            finally:
                bus.unsubscribe(q)

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return app
