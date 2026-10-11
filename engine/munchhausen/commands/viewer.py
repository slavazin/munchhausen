"""`munchhausen viewer` and `munchhausen viewer-seed` (S6). Composition root for the viewer: builds the
read model over the store, the injector per arm and the owner port, and hands them to the viewer app.

Contracts this module expects from other surfaces, looked up when first used (so the viewer starts and
renders before they land, and the injection control reports which piece is missing):
- S2 `bootstrap.forward_pass(h, arm, *, world) -> ForwardPass` — a forward pass for `arm` over `world`.
- S4 `bootstrap_learn.nominator_for(h, arm)` — an object with `nominate(run_id, arm, round_, shape)`.
- S4 `bootstrap_learn.adjudicator_for(h, arm) -> Adjudicator`.
- S4 `bootstrap_learn.owner_port(h)` — `dispose_draft(id, verdict, note)`, `dispose_fire(id, disposition, note)`.
"""

from __future__ import annotations

import asyncio
from typing import Any

import typer

from munchhausen.config import Settings
from munchhausen.config import settings as load_settings


def _contract(module: str, name: str, milestone: str) -> Any:
    import importlib

    fn = getattr(importlib.import_module(module), name, None)
    if fn is None:
        raise NotImplementedError(f"{milestone}: `{module}.{name}` is not built yet")
    return fn


def injector_for(h: Any, arm: str) -> Any:
    from munchhausen.learn.episodic import Bar
    from munchhausen.loop.inject import Injector, InjectParams

    s: Settings = h.settings
    forward_pass = _contract("munchhausen.bootstrap", "forward_pass", "M2 (S2)")
    nominator = _contract("munchhausen.bootstrap_learn", "nominator_for", "M3 (S3/S4)")(h, arm)
    adjudicator = _contract("munchhausen.bootstrap_learn", "adjudicator_for", "M3 (S4)")(h, arm)
    observe = None
    if s.anthropic_api_key is not None:
        observe = h.shared("models", s.models_impl).observe
    return Injector(
        world=h.world(), forward_for=lambda w: forward_pass(h, arm, world=w), nominator=nominator,
        adjudicator=adjudicator, observations=h.store.observations, drafts=h.store.drafts,
        backtests=h.store.backtests, cursors=h.store.cursors,
        bar=Bar(min_obs=s.bar_min_obs, min_templates=s.bar_min_templates, min_gap=s.bar_min_gap,
                min_matched=s.bar_min_matched),
        params=InjectParams(seed=s.inject_seed, scan_max=s.inject_scan_max, rel_tol=s.score_rel_tol),
        observe=observe)


def atlas_services(s: Settings) -> Any:
    from munchhausen.bootstrap import harness
    from munchhausen.store.read_models import AtlasReadModel
    from munchhausen_viewer.services import ViewerServices

    h = harness(s)
    return ViewerServices(
        settings=s, read_model=AtlasReadModel.create("atlas", s, h.store), arms=h.arms,
        injector_for=lambda arm: injector_for(h, arm),
        owner=lambda: _contract("munchhausen.bootstrap_learn", "owner_port", "M3 (S4)")(h),
        close=h.close, mode="atlas")


def synthetic_services(s: Settings, run_id: str) -> Any:
    from munchhausen_viewer.memory import MemoryReadModel
    from munchhausen_viewer.services import ViewerServices
    from munchhausen_viewer.synthetic import build

    return ViewerServices(settings=s.model_copy(update={"viewer_run_id": run_id}),
                          read_model=MemoryReadModel(build(s, run_id), s.round_size), arms=s.arms(),
                          mode="synthetic")


def register(app: typer.Typer) -> None:
    @app.command()
    def viewer(run: str = typer.Option(None, help="run id shown first (default VIEWER_RUN_ID or RUN_ID)"),
               host: str = typer.Option(None, help="bind address (default VIEWER_HOST, loopback)"),
               port: int = typer.Option(None, help="port (default VIEWER_PORT)"),
               synthetic: bool = typer.Option(False, help="serve an in-memory synthetic run; no Atlas")) -> None:
        """Serve the viewer (SPEC § 17): panes over change streams, replay scrubber, injection, why."""
        import uvicorn

        from munchhausen_viewer.app import create_app

        s = load_settings()
        if run:
            s = s.model_copy(update={"viewer_run_id": run})
        svc = synthetic_services(s, run or "synthetic") if synthetic else atlas_services(s)
        h, p = host or s.viewer_host, port or s.viewer_port
        typer.echo(f"viewer: http://{h}:{p}/  run={svc.run_id}  mode={svc.mode}")
        uvicorn.run(create_app(svc), host=h, port=p, log_level="warning")

    @app.command("viewer-seed")
    def viewer_seed(run: str = typer.Option(..., help="run id; must start with wt-s6- (sandbox rule)")) -> None:
        """Write a synthetic story-shaped run through the engine repositories, for developing the viewer."""
        from munchhausen.bootstrap import harness
        from munchhausen_viewer.synthetic import build, seed

        if not run.startswith("wt-s6-"):
            raise typer.BadParameter("synthetic runs are written only under run ids starting with wt-s6-")
        s = load_settings()

        async def go() -> dict[str, int]:
            h = harness(s)
            try:
                return await seed(h.store, build(s, run))
            finally:
                await h.close()

        typer.echo(asyncio.run(go()))
