"""`munchhausen` CLI (typer). M0 commands: doctor, ping, setup, arms; surfaces add theirs in `commands/`."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import typer

from munchhausen.bootstrap import harness
from munchhausen.config import settings

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _run(fn: Callable[[], Awaitable[Any]]) -> Any:
    return asyncio.run(fn())


def _print(obj: Any) -> None:
    typer.echo(json.dumps(obj, indent=2, default=str))


@app.command()
def doctor() -> None:
    """Show which knobs and keys are configured (never prints secret values)."""
    s = settings()
    keys = ["mongodb_uri", "mongodb_uri_learner", "mongodb_uri_evaluator", "mongodb_uri_executor",
            "anthropic_api_key", "voyage_api_key", "typesafe_api_key", "raindrop_write_key", "raindrop_query_key"]
    _print({"keys": {k: getattr(s, k) is not None for k in keys}, "arms": sorted(s.arms()),
            "run_id": s.run_id, "pack": s.world_pack, "models": {"proposer": s.proposer_model,
            "observer": s.observer_model, "nominator": s.nominator_model}})


@app.command()
def ping() -> None:
    """Connect to Atlas and report server capabilities (read-only)."""
    async def go() -> None:
        h = harness()
        try:
            await h.store.ping()
            _print(await h.store.capabilities())
        finally:
            await h.close()
    _run(go)


@app.command()
def setup() -> None:
    """Create collections, validators, B-tree and search indexes in `munchhausen` (idempotent)."""
    async def go() -> None:
        h = harness()
        try:
            _print(await h.store.setup())
        finally:
            await h.close()
    _run(go)


@app.command()
def arms() -> None:
    """List arm specs and their port selections."""
    _print({name: spec.model_dump() for name, spec in settings().arms().items()})


from munchhausen.commands import register as _register  # noqa: E402

_register(app)


if __name__ == "__main__":
    app()
