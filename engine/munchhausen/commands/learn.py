"""Adjudication surface commands: the owner port (L5), `why`, and the § 12 premise read.

- `munchhausen owner dispose <draft_id|fire_id> <disposition>`: drafts take `admit|refuse`, fires take
  `applied|rejected|deferred`; recorded `disposer: owner` (SPEC § 7.3 L5).
- `munchhausen why <decision_id|term>`: the trail as JSON (`$graphLookup` over `latches.edges`, successors,
  `$lookup` to observations, episodes, the backtest, fires and tool access).
- `munchhausen premise <arm>`: share of sampled first-attempt misses the paired replay fixed, over the
  arm's first ten backtests (SPEC § 12 second premise).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import typer

from munchhausen.domain.common import FireDisposition
from munchhausen.domain.draft import Verdict


def _print(obj: Any) -> None:
    typer.echo(json.dumps(obj, indent=2, default=str))


def register(app: typer.Typer) -> None:
    owner = typer.Typer(no_args_is_help=True, help="The owner port (L5).")
    app.add_typer(owner, name="owner")

    @owner.command("dispose")
    def dispose(target: str, disposition: str, note: str = typer.Option("", help="recorded with the disposition"),
                at_idx: int | None = typer.Option(None, help="admission index; default: the arm's cursor")) -> None:
        """Dispose a draft (admit|refuse) or a fire (applied|rejected|deferred) as the owner."""
        async def go() -> Any:
            from munchhausen.bootstrap import harness
            from munchhausen.bootstrap_learn import adjudicator_for

            h = harness()
            try:
                store = h.store
                fire = await store.fires.get(target)
                if fire is not None:
                    await adjudicator_for(h, fire.arm).owner_dispose_fire(target, FireDisposition(disposition), note)
                    return {"fire": target, "disposition": disposition, "disposer": "owner"}
                draft = await store.drafts.get(target)
                if draft is None:
                    raise typer.BadParameter(f"{target} is neither a fire nor a draft")
                idx = at_idx if at_idx is not None else (await store.cursors.get(draft.run_id, draft.arm)).next_idx
                rec = await adjudicator_for(h, draft.arm).owner_dispose_draft(target, Verdict(disposition), idx, note)
                return {"draft": target, "status": rec.status.value, "disposer": "owner", "at_idx": idx}
            finally:
                await h.close()
        _print(asyncio.run(go()))

    @app.command("why")
    def why(subject: str, arm: str | None = typer.Option(None, help="restrict a term to one arm")) -> None:
        """Why the agent holds a decision (or every decision hooked on a term): the full trail."""
        async def go() -> Any:
            from munchhausen.bootstrap import harness

            h = harness()
            try:
                d = h.store.decisions
                ids = [subject] if await d.get(subject) else await d.ids_with_term(h.settings.run_id, subject, arm)
                return {"subject": subject, "trails": [await d.trail(i) for i in ids]}
            finally:
                await h.close()
        _print(asyncio.run(go()))

    @app.command("premise")
    def premise(arm: str, first: int = typer.Option(10, help="backtests read, in insertion order")) -> None:
        """SPEC § 12: does the proposer apply an admitted decision? Misses fixed by the paired replay."""
        async def go() -> Any:
            from munchhausen.bootstrap import harness
            from munchhausen.learn.backtest import applied_premise

            h = harness()
            try:
                return {"run_id": h.settings.run_id, "arm": arm,
                        **applied_premise(await h.store.backtests.for_arm(h.settings.run_id, arm), first)}
            finally:
                await h.close()
        _print(asyncio.run(go()))
