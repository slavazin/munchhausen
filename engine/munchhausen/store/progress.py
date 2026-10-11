"""Live progress of a run, per arm, read from the stores while the run is in flight (operator view).

One read-only snapshot: stream/V episodes, cursor round, rolling accuracy, failed episodes, observations,
drafts by status, backtests by verdict, decisions by lifecycle, open dispositive fires, spend (usd, failed
calls by model), and the time of the arm's newest model call (stall detection). Alarms are computed by the caller
against knobs; nothing on the learning path reads this.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from munchhausen.store.names import C

Doc = dict[str, Any]


async def _counts(db: AsyncDatabase[Doc], coll: str, match: Doc, field: str) -> dict[str, int]:
    pipeline = [{"$match": match}, {"$group": {"_id": f"${field}", "n": {"$sum": 1}}}]
    rows = await (await db[coll].aggregate(pipeline)).to_list()
    return {str(r["_id"]): r["n"] for r in rows}


async def progress(db: AsyncDatabase[Doc], run_id: str, arms: list[str], window: int) -> dict[str, Any]:
    now = datetime.now(UTC)
    out: dict[str, Any] = {"run_id": run_id, "at": now.isoformat(timespec="seconds"), "arms": {}}
    for arm in arms:
        q = {"run_id": run_id, "arm": arm}
        stream = {**q, "stream": "stream"}
        n = await db[C.EPISODES.value].count_documents(stream)
        last = await (db[C.EPISODES.value].find(stream, {"idx": 1, "correct": 1, "error": 1})
                      .sort("idx", -1).limit(window).to_list())
        recent_ok = [e for e in last if not str(e.get("error") or "").startswith("episode_failed")]
        cursor = await db[C.CURSORS.value].find_one(q) or {}
        spend = await (await db[C.SPEND.value].aggregate([
            {"$match": {"meta.run_id": run_id, "meta.arm": arm}},
            {"$group": {"_id": None, "usd": {"$sum": {"$ifNull": ["$usd", 0]}}, "calls": {"$sum": 1},
                        "failed": {"$sum": {"$cond": [{"$eq": ["$ok", False]}, 1, 0]}},
                        "last": {"$max": "$at"}}}])).to_list()
        failed_by_model = await (await db[C.SPEND.value].aggregate([
            {"$match": {"meta.run_id": run_id, "meta.arm": arm, "ok": False}},
            {"$group": {"_id": {"model": "$meta.model", "error": "$error"}, "n": {"$sum": 1}}}])).to_list()
        sp = spend[0] if spend else {"usd": 0.0, "calls": 0, "failed": 0, "last": None}
        out["arms"][arm] = {
            "stream": n,
            "v": await db[C.EPISODES.value].count_documents({**q, "stream": "v"}),
            "round": cursor.get("round"),
            "next_idx": cursor.get("next_idx"),
            "acc_recent": round(sum(1 for e in recent_ok if e.get("correct")) / len(recent_ok), 3) if recent_ok else None,
            "recent_n": len(recent_ok),
            "episodes_failed": await db[C.EPISODES.value].count_documents({**q, "error": {"$regex": "^episode_failed"}}),
            "observations": await _counts(db, C.OBSERVATIONS.value, q, "disposition"),
            "drafts": await _counts(db, C.DRAFTS.value, q, "status"),
            "backtests": await _counts(db, C.BACKTESTS.value, q, "verdict"),
            "decisions": await _counts(db, C.DECISIONS.value, q, "lifecycle.status"),
            "fires_open_dispositive": await db[C.FIRES.value].count_documents(
                {**q, "role": "dispositive", "disposition": "open"}),
            "usd": round(float(sp.get("usd") or 0.0), 3),
            "calls": sp.get("calls", 0),
            "calls_failed": sp.get("failed", 0),
            "failed_by_model": {f"{r['_id'].get('model')}:{str(r['_id'].get('error'))[:40]}": r["n"]
                                for r in failed_by_model},
            "last_spend_at": sp["last"].isoformat(timespec="seconds") if sp.get("last") else None,
        }
    return out
