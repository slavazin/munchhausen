"""Telemetry and evidence commands (S5): `report`, `spend`, `runs`, `planted-map`.

`report <run_id>` writes `var/reports/<run_id>/{readings.json, report.md, report.html, manifest.json}`.
Every figure in the report has a manifest entry naming its query and n.
"""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Any

import typer

from munchhausen.bootstrap import harness
from munchhausen.metrics import report as rep


def _print(obj: Any) -> None:
    typer.echo(json.dumps(obj, indent=2, default=str))


def write_report(var_dir: Any, run: dict[str, Any], readings: dict[str, Any], *, chartjs_url: str,
                 against: dict[str, Any] | None = None) -> dict[str, str]:
    """Render and write the four report files; returns their paths."""
    out = var_dir / "reports" / readings["run_id"]
    out.mkdir(parents=True, exist_ok=True)
    if against is not None:
        readings = {**readings, "knob_diff": {"against": against.get("_id"),
                                              "diff": rep.run_diff(run, against)}}
    files = {
        "readings.json": json.dumps(readings, indent=2, default=str),
        "report.md": rep.markdown(readings, run, against=against),
        "report.html": rep.html_report(readings, run, chartjs_url=chartjs_url),
        "manifest.json": json.dumps(rep.manifest(readings, readings["run_id"]), indent=2, default=str),
    }
    for name, text in files.items():
        (out / name).write_text(text)
    return {name: str(out / name) for name in files}


def register(app: typer.Typer) -> None:
    @app.command()
    def report(run_id: str, against: str = typer.Option(None, help="another run id: print the knob diff")) -> None:
        """Readings for one run → var/reports/<run_id>/ (readings.json, report.md, report.html, manifest.json)."""
        from munchhausen.evidence import readings_for

        async def go() -> None:
            h = harness()
            try:
                run, readings = await readings_for(h, run_id)
                other = None
                if against:
                    o = await h.store.runs.get(against)
                    if o is None:
                        raise typer.BadParameter(f"no run record for {against}")
                    other = o.model_dump(mode="json", by_alias=True)
                paths = write_report(h.settings.var_dir, run.model_dump(mode="json", by_alias=True), readings,
                                     chartjs_url=h.settings.chartjs_url, against=other)
                _print(paths)
            finally:
                await h.close()

        asyncio.run(go())

    @app.command("report-demo")
    def report_demo() -> None:
        """Render the report over a SYNTHETIC run (no Atlas, no model calls) → var/reports/synthetic-demo/."""
        from munchhausen.config import settings
        from munchhausen.metrics import synthetic
        from munchhausen.metrics.readings import all_readings

        s = settings()
        arms = s.arms()
        ctx = synthetic.context(arms, s.forecasts(), run_id="synthetic-demo")
        rows = synthetic.rows(arms, run_id="synthetic-demo")
        readings = all_readings(rows, ctx, spend=synthetic.spend(arms), priced=s.model_prices_usd_per_mtok)
        readings["note"] = "SYNTHETIC run: planted rows for rendering and tests; not evidence of anything"
        run = {"_id": "synthetic-demo", "started_at": "synthetic", "git_sha": "synthetic", "isolation": "convention",
               "pack_hash": "synthetic", "knobs": s.knobs()}
        _print(write_report(s.var_dir, run, readings, chartjs_url=s.chartjs_url))

    @app.command()
    def spend(run_id: str = typer.Argument(None, help="defaults to RUN_ID")) -> None:
        """Model spend so far for a run, per arm × stage × model (list-price USD)."""
        async def go() -> None:
            h = harness()
            try:
                rid = run_id or h.settings.run_id
                rows = await h.store.evidence.spend_summary(rid)
                by_arm: dict[str, float] = {}
                for r in rows:
                    by_arm[r["arm"]] = by_arm.get(r["arm"], 0.0) + float(r["usd"])
                _print({"run_id": rid, "usd_by_arm": by_arm, "usd_total": sum(by_arm.values()), "rows": rows})
            finally:
                await h.close()

        asyncio.run(go())

    @app.command()
    def runs(limit: int = 20,
             diff: Annotated[list[str] | None, typer.Option(help="two run ids: print their knob diff")] = None) -> None:
        """List run records (newest first); with --diff A --diff B, the knobs that moved between two runs."""
        async def go() -> None:
            h = harness()
            try:
                if diff:
                    if len(diff) != 2:
                        raise typer.BadParameter("--diff takes exactly two run ids")
                    a, b = (await h.store.runs.get(diff[0])), (await h.store.runs.get(diff[1]))
                    if a is None or b is None:
                        raise typer.BadParameter("unknown run id")
                    _print({"this": a.id, "other": b.id,
                            "diff": rep.run_diff(a.model_dump(mode="json"), b.model_dump(mode="json"))})
                    return
                _print([{"run_id": r.id, "started_at": r.started_at, "ended_at": r.ended_at, "git_sha": r.git_sha,
                         "git_dirty": r.git_dirty, "isolation": r.isolation, "arms": sorted(r.ports),
                         "forecasts": sorted(r.forecast_register or r.forecasts)}
                        for r in await h.store.runs.list_runs(limit)])
            finally:
                await h.close()

        asyncio.run(go())

    @app.command("planted-map")
    def planted_map_cmd(run_id: str) -> None:
        """Evaluation only: map every decision of a run to a planted quirk id or none (Opus judge; spends)."""
        from munchhausen.domain.decision import Decision
        from munchhausen.domain.draft import Draft
        from munchhausen.impl.parties import planted_map as party
        from munchhausen.metrics.planted_map import pack_definitions, planted_map
        from munchhausen.world.pack import load_pack

        async def go() -> None:
            h = harness()
            s = h.settings
            try:
                run = await h.store.runs.get(run_id)
                if run is None:
                    raise typer.BadParameter(f"no run record for {run_id}")
                pack = load_pack(s.pack_path(run.pack))
                defs = pack_definitions(pack.quirks)
                rows = await h.store.evidence.snapshot(run_id)
                done = {m["decision_id"] for m in rows["planted_map"]}           # resume: skip mapped subjects
                backtested = {b.get("draft_id") for b in rows["backtests"]}
                subjects: list[tuple[str, Any]] = [
                    ("decision", Decision.model_validate(d)) for d in rows["decisions"] if d["_id"] not in done]
                for d in rows["drafts"]:
                    if d["_id"] in backtested and d["_id"] not in done:
                        try:
                            subjects.append(("draft", Draft.model_validate(d)))
                        except Exception:  # noqa: BLE001 - a draft row the model cannot read is reported below
                            typer.echo(f"[planted-map] draft {d['_id']} unreadable; not mapped", err=True)
                models = h.shared("models", s.models_impl)

                async def judge(subj: Any, model: str) -> str | None:
                    return await party.run(models, s, subj, defs, model=model)

                res = await planted_map(subjects, judge, [q.id for q in pack.quirks],
                                        models=[s.planted_map_model, s.planted_map_fallback_model],
                                        concurrency=s.planted_map_concurrency, sink=h.store.evidence.put_mapping)
                _print({"run_id": run_id, "mapped": len(res.mapped), "already_mapped": len(done),
                        "failed": res.failed, "by_model": res.by_model,
                        "by_quirk": {str(q): sum(1 for m in res.mapped if m.quirk == q)
                                     for q in {m.quirk for m in res.mapped}}})
            finally:
                await h.close()

        asyncio.run(go())
