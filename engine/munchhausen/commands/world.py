"""World commands (S1): `build-world`, `kickoff-check`, `pilot`.

- `build-world`: materialize `world` from the source under WORLD_SEED; print counts, the pack hash, the schema
  summary, and the gold checks over the live data (isolation, per-template quirk effect).
- `kickoff-check`: profile the source (SPEC § 4.2 verify): types of price/total, the ticker set, trade years,
  `accounts.limit` distribution, products, birth years. Read-only.
- `pilot`: the SPEC § 12 gate. The frozen proposer (no consultation, no authority) answers PILOT_N stream
  questions; accuracy on quirk-bearing questions vs controls against PILOT_QUIRK_MAX / PILOT_CONTROL_MIN.
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from typing import Any

import typer

from munchhausen.config import Settings
from munchhausen.config import settings as load_settings


def _print(obj: Any) -> None:
    typer.echo(json.dumps(obj, indent=2, default=str))


def _group(key: Any, unwind: str | None = None) -> list[dict[str, Any]]:
    stages: list[dict[str, Any]] = [{"$unwind": f"${unwind}"}] if unwind else []
    return [*stages, {"$group": {"_id": key, "n": {"$sum": 1}}}, {"$sort": {"_id": 1}}]


async def kickoff_check(s: Settings) -> dict[str, Any]:
    from munchhausen.bootstrap import harness

    h = harness(s)
    try:
        src, t = h.store.source(), s.kickoff_max_time_ms
        names = await src.collection_names()
        out: dict[str, Any] = {"source_db": s.source_db, "collections": sorted(names)}
        if "transactions" not in names:
            out["verdict"] = "source not loaded: Atlas → Load Sample Dataset, keep sample_analytics"
            return out
        sample = await src.find("transactions", limit=20)
        types: Counter[str] = Counter()
        for b in sample:
            for tr in b.get("transactions", [])[:5]:
                types.update(f"{k}:{type(v).__name__}" for k, v in tr.items())
        out["trade_field_types"] = dict(types)

        async def agg(coll: str, pipe: list[dict[str, Any]]) -> dict[str, int]:
            return {str(r["_id"]): r["n"] for r in await src.aggregate(coll, pipe, max_time_ms=t)}

        out["counts"] = {c: (await src.aggregate(c, [{"$count": "n"}], max_time_ms=t) or [{"n": 0}])[0]["n"]
                         for c in ("customers", "accounts", "transactions")}
        out["tickers"] = await agg("transactions", _group("$transactions.symbol", "transactions"))
        out["trade_years"] = await agg("transactions", _group({"$year": "$transactions.date"}, "transactions"))
        out["trade_codes"] = await agg("transactions", _group("$transactions.transaction_code", "transactions"))
        out["bucket_start_years"] = await agg("transactions", _group({"$year": "$bucket_start_date"}))
        out["account_limits"] = await agg("accounts", _group("$limit"))
        out["products"] = await agg("accounts", _group("$products", "products"))
        out["birth_years"] = await agg("customers", _group({"$year": "$birthdate"}))
        out["customer_fields"] = sorted({k for d in await src.find("customers", limit=20) for k in d})
        return out
    finally:
        await h.close()


async def build_world(s: Settings) -> dict[str, Any]:
    from munchhausen.bootstrap import harness
    from munchhausen.world.checks import drift_direction, isolation_violations, poison_collisions, quirk_effects

    h = harness(s)
    try:
        w = h.world()
        counts = await w.build(s.world_seed)
        data = await w.truth.data()
        pack, bank, gold = w.pack, w.bank, w.truth
        return {"world": w.id, "seed": s.world_seed, "counts": counts, "pack_hash": w.pack_hash,
                "schema_summary": w.schema_summary().collections,
                "st": dict(Counter(c.get("st") for c in data["customers"])),
                "rs": dict(Counter(b.get("rs") for b in data["transactions"])),
                "decoy_set": sum(b.get("deleted_at") is not None for b in data["transactions"]),
                "isolation_violations": isolation_violations(gold, bank, pack, data, s.gold_check_combos),
                "quirk_effect_share": quirk_effects(gold, bank, pack, data, s.gold_check_combos),
                "drift_direction": drift_direction(gold, bank, pack, data, s.gold_check_combos),
                "poison_collisions": poison_collisions(gold, bank, pack, data, s.gold_check_combos),
                "v_set_by_quirk": dict(Counter((bank.hidden(q.id).quirks or ("control",))[0] for q in w.v_set())),
                "zero_gold": _zero_gold(w, data, s.gold_check_combos)}
    finally:
        await h.close()


def _zero_gold(w: Any, data: Any, limit: int) -> dict[str, float]:
    """template → share of combos whose gold is 0 (params outside the data: fix them in the pack)."""
    from munchhausen.world.checks import combos

    out = {}
    for t in w.bank.templates:
        cs = combos(t, limit)
        zeros = sum(w.truth.compute(w.bank.pose(t.id, w.pack.personas[0], p), "v0", data) == 0 for p in cs)
        if zeros:
            out[t.id] = zeros / len(cs)
    return out


async def pilot(s: Settings) -> dict[str, Any]:
    from munchhausen.agent.execute import ExecutionError, execute
    from munchhausen.bootstrap import harness
    from munchhausen.ports.models import ProposerInput

    h = harness(s)
    try:
        w = h.world()
        schema = await w.load_schema()
        models = h.shared("models", s.models_impl)
        reader = h.store.world()
        sem = asyncio.Semaphore(s.workers_per_arm)
        questions = [w.bank.question_at(s.stream_seed, i) for i in range(s.pilot_n)]

        async def one(i: int, q: Any) -> dict[str, Any]:
            async with sem:
                proposal = await models.propose(ProposerInput(question=q, schema=schema, consulted=(), arm="frozen"))
                try:
                    answer = (await execute(proposal, {}, reader, max_time_ms=s.execute_max_time_ms)).answer
                    err = None
                except ExecutionError as e:
                    answer, err = None, str(e)
                j = await w.judge(q, answer, i, with_authority=False)
                return {"idx": i, "template": q.template, "persona": q.persona, "quirk": w.is_quirk_bearing(q.id),
                        "correct": j.correct, "answer": answer, "gold": await w.truth.gold(q, w.world_version(i)),
                        "error": err}

        try:
            rows = await asyncio.gather(*(one(i, q) for i, q in enumerate(questions)))
        except NotImplementedError as e:
            raise typer.Exit(_fail(f"pilot needs the proposer (S2, M2): {e}")) from e
        quirk = [r for r in rows if r["quirk"]]
        ctl = [r for r in rows if not r["quirk"]]
        acc_q = sum(r["correct"] for r in quirk) / len(quirk) if quirk else None
        acc_c = sum(r["correct"] for r in ctl) / len(ctl) if ctl else None
        holds = (acc_q is not None and acc_q <= s.pilot_quirk_max and acc_c is not None
                 and acc_c >= s.pilot_control_min)
        by_template: dict[str, list[int]] = {}
        for r in rows:
            by_template.setdefault(r["template"], [0, 0])
            by_template[r["template"]][0] += r["correct"]
            by_template[r["template"]][1] += 1
        return {"n": len(rows), "model": s.proposer_model,
                "quirk_bearing": {"n": len(quirk), "accuracy": acc_q, "max": s.pilot_quirk_max},
                "controls": {"n": len(ctl), "accuracy": acc_c, "min": s.pilot_control_min},
                "gate": "holds" if holds else "fails",
                "by_template": {t: f"{c}/{n}" for t, (c, n) in sorted(by_template.items())},
                "rows": rows}
    finally:
        await h.close()


def _fail(msg: str) -> int:
    typer.echo(msg, err=True)
    return 2


def register(app: typer.Typer) -> None:
    @app.command("build-world")
    def build_world_cmd() -> None:
        """Materialize `world` from the source (deterministic under WORLD_SEED); print counts and gold checks."""
        _print(asyncio.run(build_world(load_settings())))

    @app.command("kickoff-check")
    def kickoff_check_cmd() -> None:
        """Profile the source database (SPEC § 4.2 verify). Read-only."""
        _print(asyncio.run(kickoff_check(load_settings())))

    @app.command("pilot")
    def pilot_cmd(rows: bool = typer.Option(False, help="print every row")) -> None:
        """SPEC § 12 pilot gate: frozen proposer over PILOT_N stream questions."""
        out = asyncio.run(pilot(load_settings()))
        if not rows:
            out.pop("rows")
        _print(out)
