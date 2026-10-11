"""`munchhausen viewer` and `munchhausen viewer-seed` (S6). Composition root for the viewer: builds the
read model over the store, the injector per arm and the owner port, and hands them to the viewer app.

Seams: `Harness.forward_pass(arm, world, models)` (S2), `bootstrap_learn.nominator_for`,
`adjudicator_for` and `owner_port` (S3/S4). The injection's proposer spend is tagged INJECT_STAGE.
The server binds loopback unless VIEWER_ALLOW_PUBLIC is set.
"""

from __future__ import annotations

import asyncio
from typing import Any

import typer

from munchhausen.config import Settings
from munchhausen.config import settings as load_settings

LOOPBACK = ("127.0.0.1", "localhost", "::1")


def injector_for(h: Any, arm: str) -> Any:
    from munchhausen import bootstrap_learn
    from munchhausen.learn.episodic import Bar
    from munchhausen.loop.inject import InjectionModels, Injector, InjectParams

    s: Settings = h.settings
    models = h.models()
    tagged = InjectionModels(models, s.inject_stage)
    return Injector(
        world=h.world(), forward_for=lambda w: h.forward_pass(arm, w, models=tagged),
        nominator=bootstrap_learn.nominator_for(h, arm), adjudicator=bootstrap_learn.adjudicator_for(h, arm),
        observations=h.store.observations, drafts=h.store.drafts,
        backtests=h.store.backtests, cursors=h.store.cursors, episodes=h.store.episodes,
        bar=Bar(min_obs=s.bar_min_obs, min_templates=s.bar_min_templates, min_gap=s.bar_min_gap,
                min_matched=s.bar_min_matched),
        params=InjectParams(seed=s.inject_seed, scan_max=s.inject_scan_max, rel_tol=s.score_rel_tol,
                            idx_base=s.inject_idx_base, max_templates=s.inject_max_templates),
        observe=models.observe, trace=h.trace())


async def ready_injector(h: Any, arm: str) -> Any:
    """The injector over a World whose schema summary is loaded (`Harness.ready_world`, as the run path does):
    the viewer process never ran `build-world`, so a bare `h.world()` has no summary to pick questions from."""
    await h.ready_world()
    return injector_for(h, arm)


def atlas_services(s: Settings) -> Any:
    from munchhausen import bootstrap_learn
    from munchhausen.bootstrap import build_port, harness
    from munchhausen_viewer.services import ViewerServices

    h = harness(s)
    return ViewerServices(
        settings=s, read_model=build_port("read_model", s.store_impl, s, h.store), arms=h.arms,
        injector_for=lambda arm: ready_injector(h, arm), owner=lambda: bootstrap_learn.owner_port(h),
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
        if h not in LOOPBACK and not s.viewer_allow_public:
            raise typer.BadParameter(f"refusing to bind {h}: the viewer drives the engine; "
                                     "set VIEWER_ALLOW_PUBLIC=true to allow a non-loopback address")
        if h not in s.viewer_allowed_hosts:
            s = s.model_copy(update={"viewer_allowed_hosts": (*s.viewer_allowed_hosts, h)})
            svc.settings = s.model_copy(update={"viewer_run_id": svc.run_id})
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
