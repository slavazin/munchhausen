"""`munchhausen status <run_id> [--watch]`: a live operator view of a run, with ALARM lines.

Each refresh prints one row per arm and one `ALARM <arm> <kind>: <detail>` line per tripped alarm, so a
log watcher can match on `ALARM`. Alarms (knobs in `config.py`): an unfinished arm with no model call for
STATUS_STALL_S; failed model calls above STATUS_MAX_FAIL_SHARE of the arm's calls; any failed episode
(an unpaired index); the run's spend above RUN_BUDGET_USD. Read-only.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import typer


def alarms(snap: dict[str, Any], s: Any, length: int | None) -> list[str]:
    out: list[str] = []
    now = datetime.fromisoformat(snap["at"])
    total = 0.0
    for arm, a in snap["arms"].items():
        total += a["usd"]
        finished = length is not None and a["stream"] >= length
        if a["last_spend_at"] and not finished:
            idle = (now - datetime.fromisoformat(a["last_spend_at"]).replace(tzinfo=UTC)).total_seconds()
            if idle > s.status_stall_s:
                out.append(f"ALARM {arm} stall: no model call for {int(idle)}s "
                           f"(round {a['round']}, stream {a['stream']})")
        if a["calls"] and a["calls_failed"] / a["calls"] > s.status_max_fail_share:
            out.append(f"ALARM {arm} model-failures: {a['calls_failed']}/{a['calls']} calls failed "
                       f"{a['failed_by_model']}")
        if a["episodes_failed"]:
            out.append(f"ALARM {arm} failed-episodes: {a['episodes_failed']} (paired readings drop these indices)")
    if total > s.run_budget_usd:
        out.append(f"ALARM run budget: ${total:.2f} > ${s.run_budget_usd:.2f}")
    return out


def render(snap: dict[str, Any]) -> str:
    head = f"{snap['run_id']} @ {snap['at']}"
    rows = [head, f"{'arm':9} {'stream':>6} {'V':>4} {'rnd':>3} {'acc~':>5} {'obs':>18} {'drafts':>22} "
                  f"{'backtests':>20} {'decisions':>26} {'fires':>5} {'usd':>7} {'fail':>5}"]
    for arm, a in snap["arms"].items():
        acc = "-" if a["acc_recent"] is None else f"{a['acc_recent']:.2f}"
        rows.append(f"{arm:9} {a['stream']:>6} {a['v']:>4} {a['round'] if a['round'] is not None else '-':>3} {acc:>5} "
                    f"{json.dumps(a['observations'], separators=(',', ':')):>18} "
                    f"{json.dumps(a['drafts'], separators=(',', ':')):>22} "
                    f"{json.dumps(a['backtests'], separators=(',', ':')):>20} "
                    f"{json.dumps(a['decisions'], separators=(',', ':')):>26} {a['fires_open_dispositive']:>5} "
                    f"{a['usd']:>7.2f} {a['calls_failed']:>5}")
    return "\n".join(rows)


def register(app: typer.Typer) -> None:
    @app.command("status")
    def status_cmd(run_id: str, watch: bool = typer.Option(False, help="refresh every STATUS_INTERVAL_S"),
                   length: int | None = typer.Option(None, help="stream length, to tell finished arms from stalled"),
                   as_json: bool = typer.Option(False, "--json")) -> None:
        """Live per-arm progress of a run, with ALARM lines (stall, model failures, failed episodes, budget)."""
        from munchhausen.bootstrap import harness

        async def once(h: Any) -> None:
            snap = await h.store.progress(run_id, list(h.arms))
            typer.echo(json.dumps(snap, default=str) if as_json else render(snap))
            for line in alarms(snap, h.settings, length):
                typer.echo(line)

        async def go() -> None:
            h = harness()
            try:
                while True:
                    await once(h)
                    if not watch:
                        return
                    await asyncio.sleep(h.settings.status_interval_s)
            finally:
                await h.close()

        asyncio.run(go())
