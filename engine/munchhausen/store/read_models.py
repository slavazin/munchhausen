"""Read models for the viewer (SPEC § 17): read-only aggregations over `munchhausen` and `world`.

The viewer's Atlas queries live here and nowhere else. Nothing in this module writes a store; the one
write is the change-stream consumer's resume token, through `CursorRepository.save_resume_token`.

Every read takes `at`, a stream index, so the replay scrubber can show the stores as they stood at that
index. Lifecycle transitions overwrite `lifecycle.at_idx`, so a decision's admission index is recovered
from the draft it was admitted from (`decision_id(draft_id)`, the draft's round) when the decision has
since left `admitted`. That recovery is a read-side approximation: the admission index is the last index
of the draft's round.

Atlas primitives exercised here: `$graphLookup` (lineage, both directions), `$lookup` (why, fires →
residuals), `$setWindowFields` (rolling accuracy, confidence, paired difference), `$densify` + `$fill`
(gap-free round curves), `$group` facets (`$searchMeta` needs `episodes_search`, over the index cap), change
streams with pre- and post-images and resume tokens, and `explain()` of the hook match.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from typing import Any, Self

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure, PyMongoError

from munchhausen.config import Settings
from munchhausen.domain.backtest import Backtest
from munchhausen.domain.common import FireRole, LifecycleStatus
from munchhausen.domain.decision import Decision
from munchhausen.domain.ids import backtest_id, decision_id
from munchhausen.ports.store import CursorRepository
from munchhausen.store.names import C, view_name

Doc = dict[str, Any]

# Fields never shipped to the browser: vectors are large and carry nothing a reader can use.
_HEAVY = frozenset({"emb"})


def jsonable(x: Any) -> Any:
    """BSON → JSON-ready: ObjectId and datetime to strings, vectors dropped."""
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items() if k not in _HEAVY}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, ObjectId):
        return str(x)
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, (bytes, bytearray)):
        return x.hex()
    return x


def _idx_le(field: str, at: int | None) -> Doc:
    return {} if at is None else {field: {"$lte": at}}


# --- pure projections (tested offline) --------------------------------------------------------------


def status_at(dec: Decision, admitted_at: int, at: int | None) -> str | None:
    """Lifecycle value at stream index `at`; None when the decision was not yet admitted."""
    if at is None:
        return dec.lifecycle.status.value
    if admitted_at > at:
        return None
    if dec.lifecycle.status is not LifecycleStatus.ADMITTED and dec.lifecycle.at_idx <= at:
        return dec.lifecycle.status.value
    return LifecycleStatus.ADMITTED.value


def evidence_at(dec: Decision, fires: Sequence[Doc], at: int | None) -> str:
    """`contested` iff a dispositive fire was open at `at`. A fire disposed by a lifecycle function closed
    when its decision left `admitted`; other dispositions carry no time, so they count as closed."""
    if at is None:
        return dec.evidence_state.value
    for f in fires:
        if f.get("role") != FireRole.DISPOSITIVE.value or f.get("at_idx", 0) > at:
            continue
        if f.get("disposition") == "open":
            return "contested"
        terminal = dec.lifecycle.status is not LifecycleStatus.ADMITTED
        if f.get("disposer") == "lifecycle" and terminal and dec.lifecycle.at_idx > at:
            return "contested"
    return "clear"


def backtest_view(bt: Doc | None) -> Doc | None:
    """The backtest record per sampled episode (SPEC § 7.4): fixed / broken / held out, plus totals."""
    if not bt:
        return None
    b = Backtest.model_validate(bt)
    rows = [{"episode_id": s.episode_id, "template": s.template, "original_correct": s.original_correct,
             "replay_correct": s.replay_correct, "baseline_correct": s.baseline_correct,
             "fixed": s.fixed, "broken": s.broken, "heldout": s.template not in b.source_templates,
             "context": list(s.context)} for s in b.sampled]
    return {"id": b.id, "draft_id": b.draft_id, "verdict": b.verdict.value, "fixed": b.fixed,
            "fixed_heldout": b.fixed_heldout, "broken": b.broken, "n": len(b.sampled),
            "source_templates": sorted(b.source_templates), "samples": rows}


def decision_view(dec: Decision, *, admitted_at: int, at: int | None, fires: Sequence[Doc],
                  backtest: Doc | None, view: str | None) -> Doc:
    """One decision as pane 1 shows it: kind, title/payload, latch fan, status and evidence at `at`."""
    hook = dec.hook
    floor = dec.floor
    retire = dec.retire_latch
    wiring = dec.wiring
    open_disp = [f for f in fires if f.get("disposition") == "open" and f.get("role") == FireRole.DISPOSITIVE.value]
    return {
        "id": dec.id, "arm": dec.arm, "kind": dec.kind.value, "title": dec.title, "payload": dec.payload,
        "forecloses": dec.forecloses, "residue": dec.residue,
        "fan": {
            "hook": {"terms": list(hook.fires_when.terms), "collections": list(hook.fires_when.collections),
                     "persona": hook.fires_when.persona,
                     "not_this": [{"terms": list(r.terms), "collections": list(r.collections),
                                   "persona": r.persona, "contrast": r.contrast} for r in hook.not_this]},
            "revisits": [{"id": r.id, "signature": r.signature.value, "min_residuals": r.guard.min_residuals,
                          "window": r.guard.window, "role": r.role.value} for r in dec.revisits],
            "floor": None if floor is None else {"collection": floor.collection, "match": floor.match,
                                                 "view": view or view_name(floor.collection, dec.id)},
            "retire": None if retire is None else {"id": retire.id, "idle": retire.moot_when.idle_episodes,
                                                   "max_fires": retire.max_fires},
            "wiring": {"supersedes": wiring.supersedes, "converged_from": list(wiring.converged_from),
                       "related": list(wiring.related)},
        },
        "options": [{"definition": o.definition, "verdict": o.verdict, "prior": o.prior} for o in dec.options],
        "lifecycle": {"status": dec.lifecycle.status.value, "at_idx": dec.lifecycle.at_idx,
                      "superseded_by": dec.lifecycle.superseded_by,
                      "converged_into": dec.lifecycle.converged_into, "reason": dec.lifecycle.reason,
                      "admitted_at": admitted_at, "seeded": dec.lifecycle.seeded},
        "status": status_at(dec, admitted_at, at),
        "evidence_state": evidence_at(dec, fires, at),
        "open_dispositive_fires": len(open_disp),
        "fires": len([f for f in fires if at is None or f.get("at_idx", 0) <= at]),
        "warrant": {"templates": dec.warrant.templates, "sources": len(dec.warrant.source_observation_ids),
                    "episodes": len(dec.warrant.source_episode_ids), "falsifier": dec.warrant.falsifier,
                    "lens": dec.warrant.lens, "lens_score": dec.warrant.lens_score,
                    "backtest_id": dec.warrant.backtest_id},
        "backtest": backtest_view(backtest),
        "amendments": [jsonable(a.model_dump(by_alias=True)) for a in dec.amendments],
    }


def floor_rewires(decisions: Sequence[Doc]) -> list[Doc]:
    """Floor-view rewires as events: one when a floor decision is admitted (logical → view) and one when
    it leaves `admitted` (view → logical restored). Live rewires also arrive as `tool_access` images."""
    out: list[Doc] = []
    for d in decisions:
        fl = (d.get("fan") or {}).get("floor")
        if not fl:
            continue
        lc = d["lifecycle"]
        out.append({"type": "rewire", "arm": d["arm"], "decision_id": d["id"], "title": d["title"],
                    "logical": fl["collection"], "before": fl["collection"], "after": fl["view"],
                    "at_idx": lc["admitted_at"], "op": "rewire"})
        if lc["status"] != LifecycleStatus.ADMITTED.value:
            out.append({"type": "rewire", "arm": d["arm"], "decision_id": d["id"], "title": d["title"],
                        "logical": fl["collection"], "before": fl["view"], "after": fl["collection"],
                        "at_idx": lc["at_idx"], "op": f"restore ({lc['status']})"})
    return out


def term_variants(target: str) -> list[str]:
    t = target.strip().lower()
    return sorted({t, t.replace("_", " "), t.replace("-", " "), t.replace(" ", "_")})


def _flatten(path: str) -> Doc:
    """`$latches.edges` yields one array per latch; flatten to one array of ids for `$graphLookup`."""
    return {"$reduce": {"input": {"$ifNull": [path, []]}, "initialValue": [],
                        "in": {"$concatArrays": ["$$value", {"$cond": [{"$isArray": "$$this"}, "$$this",
                                                                        ["$$this"]]}]}}}


# --- Atlas ------------------------------------------------------------------------------------------


class AtlasReadModel:
    """`ReadModel` over Atlas. Uniform construction: `create(name, settings, store)` takes the AtlasStore."""

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        if store is None:
            raise ValueError("AtlasReadModel needs the AtlasStore it reads through")
        return cls(settings, store.clients.store_db(), store.clients.world_db(write=False), store.cursors)

    def __init__(self, settings: Settings, db: AsyncDatabase[Doc], world: AsyncDatabase[Doc],
                 cursors: CursorRepository) -> None:
        self._s, self._db, self._world, self._cursors = settings, db, world, cursors

    def _c(self, c: C) -> Any:
        return self._db[c.value]

    async def _agg(self, c: C, pipeline: list[Doc]) -> list[Doc]:
        return await (await self._c(c).aggregate(pipeline)).to_list()

    # --- runs and the scrubber ---------------------------------------------------------------------

    async def runs(self) -> list[Doc]:
        rows = await self._agg(C.EPISODES, [
            {"$group": {"_id": "$run_id", "episodes": {"$sum": 1}, "arms": {"$addToSet": "$arm"},
                        "max_idx": {"$max": "$idx"}}},
            {"$sort": {"_id": 1}}])
        registered = {d["_id"]: d async for d in self._c(C.RUNS).find({}, {"_id": 1, "started_at": 1, "pack": 1})}
        out = [{"run_id": r["_id"], "episodes": r["episodes"], "arms": sorted(r["arms"]), "max_idx": r["max_idx"],
                "registered": r["_id"] in registered} for r in rows]
        seen = {r["run_id"] for r in out}
        out += [{"run_id": k, "episodes": 0, "arms": [], "max_idx": None, "registered": True}
                for k in registered if k not in seen]
        return jsonable(out)

    async def timeline(self, run_id: str) -> Doc:
        rows = await self._agg(C.EPISODES, [
            {"$match": {"run_id": run_id}},
            {"$facet": {
                "arms": [{"$group": {"_id": "$arm", "max_idx": {"$max": "$idx"}, "n": {"$sum": 1}}},
                         {"$sort": {"_id": 1}}],
                "templates": [{"$group": {"_id": "$template", "n": {"$sum": 1}}}, {"$sort": {"_id": 1}}],
                "streams": [{"$group": {"_id": "$stream", "n": {"$sum": 1}}}],
            }}])
        f = rows[0] if rows else {"arms": [], "templates": [], "streams": []}
        counts = {c.value: await self._c(c).count_documents({"run_id": run_id})
                  for c in (C.DECISIONS, C.DRAFTS, C.FIRES, C.BACKTESTS, C.OBSERVATIONS, C.ROUNDS)}
        arms = {r["_id"]: {"max_idx": r["max_idx"], "n": r["n"]} for r in f["arms"]}
        max_idx = max((a["max_idx"] for a in arms.values() if a["max_idx"] is not None), default=0)
        return jsonable({"run_id": run_id, "arms": arms, "max_idx": max_idx,
                         "templates": [t["_id"] for t in f["templates"]],
                         "streams": {s["_id"]: s["n"] for s in f["streams"]}, "counts": counts})

    # --- pane 1: decisions -------------------------------------------------------------------------

    async def _admission_index(self, run_id: str, arm: str) -> dict[str, int]:
        """decision id → admission index, from the admitted drafts' rounds (read-side approximation)."""
        out: dict[str, int] = {}
        async for d in self._c(C.DRAFTS).find({"run_id": run_id, "arm": arm, "status": "admitted"},
                                              {"_id": 1, "round": 1}):
            out[decision_id(d["_id"])] = (int(d.get("round", 0)) + 1) * self._s.round_size - 1
        return out

    async def _decision_rows(self, match: Doc, at: int | None) -> list[Doc]:
        docs = await self._agg(C.DECISIONS, [
            {"$match": match},
            {"$project": {"emb": 0}},
            {"$lookup": {"from": C.BACKTESTS.value, "localField": "warrant.backtest_id", "foreignField": "_id",
                         "as": "_backtest"}},
            {"$lookup": {"from": C.FIRES.value, "localField": "_id", "foreignField": "decision_id",
                         "as": "_fires", "pipeline": [{"$project": {"role": 1, "disposition": 1, "disposer": 1,
                                                                    "at_idx": 1}}]}},
            {"$lookup": {"from": C.TOOL_ACCESS.value, "localField": "_id", "foreignField": "decision_id",
                         "as": "_access"}},
        ])
        by_arm: dict[tuple[str, str], dict[str, int]] = {}
        out = []
        for d in docs:
            key = (d["run_id"], d["arm"])
            if key not in by_arm:
                by_arm[key] = await self._admission_index(*key)
            bt, fires, access = d.pop("_backtest"), d.pop("_fires"), d.pop("_access")
            dec = Decision.model_validate(d)
            admitted_at = (dec.lifecycle.at_idx if dec.is_admitted
                           else min(by_arm[key].get(dec.id, 0), dec.lifecycle.at_idx))
            view = access[0]["view"] if access else None
            out.append(decision_view(dec, admitted_at=admitted_at, at=at, fires=fires,
                                     backtest=bt[0] if bt else None, view=view))
        return out

    async def decisions(self, run_id: str, arm: str, *, at: int | None) -> list[Doc]:
        rows = await self._decision_rows({"run_id": run_id, "arm": arm}, at)
        rows = [r for r in rows if r["status"] is not None]
        order = {LifecycleStatus.ADMITTED.value: 0}
        rows.sort(key=lambda r: (order.get(r["status"], 1), -r["lifecycle"]["admitted_at"]))
        return jsonable(rows)

    # --- pane 2: fires and rewires -----------------------------------------------------------------

    async def fires(self, run_id: str, arms: Sequence[str], *, at: int | None, limit: int) -> list[Doc]:
        docs = await self._agg(C.FIRES, [
            {"$match": {"run_id": run_id, "arm": {"$in": list(arms)}, **_idx_le("at_idx", at)}},
            {"$sort": {"at_idx": -1, "_id": 1}},
            {"$limit": limit},
            {"$lookup": {"from": C.DECISIONS.value, "localField": "decision_id", "foreignField": "_id",
                         "as": "_d", "pipeline": [{"$project": {"title": 1, "kind": 1, "lifecycle": 1}}]}},
            {"$lookup": {"from": C.EPISODES.value, "localField": "episode_ids", "foreignField": "_id", "as": "_e",
                         "pipeline": [{"$project": {"idx": 1, "template": 1, "answer": 1, "figure": 1,
                                                    "residuals": 1}}]}},
        ])
        out: list[Doc] = []
        for f in docs:
            d = (f.pop("_d") or [{}])[0]
            eps = f.pop("_e")
            wanted = set(f.get("residual_ids") or [])
            residuals = [{**r, "idx": e.get("idx"), "template": e.get("template")}
                         for e in eps for r in (e.get("residuals") or []) if r.get("id") in wanted]
            out.append({"type": "fire", "id": f["_id"], "arm": f["arm"], "decision_id": f["decision_id"],
                        "title": d.get("title"), "kind": d.get("kind"),
                        "decision_status": (d.get("lifecycle") or {}).get("status"), "latch": f.get("latch"),
                        "role": f.get("role"), "cause": f.get("cause"), "disposition": f.get("disposition"),
                        "disposer": f.get("disposer"), "at_idx": f.get("at_idx"), "note": f.get("note"),
                        "episodes": [{"id": e["_id"], "idx": e.get("idx"), "template": e.get("template")}
                                     for e in eps], "residuals": residuals})
        floors = await self._decision_rows({"run_id": run_id, "arm": {"$in": list(arms)}, "kind": "floor"}, at)
        out += [r for r in floor_rewires(floors) if at is None or r["at_idx"] <= at]
        out.sort(key=lambda r: -(r.get("at_idx") or 0))
        return jsonable(out[:limit])

    # --- hero: the agent's latest episode ----------------------------------------------------------

    async def latest_episode(self, run_id: str, arm: str, *, at: int | None, stream: str | None = None) -> Doc | None:
        match: Doc = {"run_id": run_id, "arm": arm, **_idx_le("idx", at)}
        if stream:
            match["stream"] = stream
        docs = await self._agg(C.EPISODES, [
            {"$match": match}, {"$sort": {"idx": -1, "_id": -1}}, {"$limit": 1},
            {"$lookup": {"from": C.DECISIONS.value, "localField": "consulted.decision_id", "foreignField": "_id",
                         "as": "_d", "pipeline": [{"$project": {"title": 1, "kind": 1, "lifecycle.status": 1,
                                                                "evidence_state": 1}}]}},
        ])
        if not docs:
            return None
        e = docs[0]
        titles = {d["_id"]: d for d in e.pop("_d")}
        e["consulted"] = [{**c, "title": titles.get(c["decision_id"], {}).get("title"),
                           "kind": titles.get(c["decision_id"], {}).get("kind"),
                           "evidence_state": titles.get(c["decision_id"], {}).get("evidence_state")}
                          for c in e.get("consulted") or []]
        e["resolved_collection"] = (e.get("view_map") or {}).get(e.get("collection"), e.get("collection"))
        e["id"] = e.pop("_id")
        return jsonable(e)

    # --- drafts (injection result, owner port) -----------------------------------------------------

    async def drafts(self, run_id: str, arm: str, *, at: int | None, limit: int) -> list[Doc]:
        rows = await self._c(C.DRAFTS).find(
            {"run_id": run_id, "arm": arm}, {"_id": 1, "title": 1, "kind": 1, "status": 1, "route": 1,
                                             "round": 1, "adjudication": 1, "supersedes": 1, "explore": 1}
        ).sort([("round", -1), ("_id", 1)]).limit(limit).to_list()
        if at is not None:
            rows = [r for r in rows if r.get("round", 0) * self._s.round_size <= at]
        return jsonable([{**r, "id": r.pop("_id")} for r in rows])

    async def draft(self, draft_id: str) -> Doc | None:
        docs = await self._agg(C.DRAFTS, [
            {"$match": {"_id": draft_id}},
            {"$lookup": {"from": C.BACKTESTS.value, "pipeline": [{"$match": {"_id": backtest_id(draft_id)}}],
                         "as": "_backtest"}},
            {"$lookup": {"from": C.OBSERVATIONS.value, "localField": "source_observation_ids",
                         "foreignField": "_id", "as": "_sources",
                         "pipeline": [{"$project": {"emb": 0, "pipeline": 0, "retry_pipeline": 0}}]}},
        ])
        if not docs:
            return None
        d = docs[0]
        bt = d.pop("_backtest")
        d["backtest"] = backtest_view(bt[0]) if bt else None
        d["sources"] = d.pop("_sources")
        d["id"] = d.pop("_id")
        return jsonable(d)

    # --- pane 3: curves ----------------------------------------------------------------------------

    async def curves(self, run_id: str, *, reference: str, window: int, at: int | None) -> Doc:
        w = [-(window - 1), 0]
        rolling = await self._agg(C.EPISODES, [
            {"$match": {"run_id": run_id, "stream": "stream", **_idx_le("idx", at)}},
            {"$setWindowFields": {"partitionBy": "$arm", "sortBy": {"idx": 1}, "output": {
                "acc": {"$avg": {"$cond": ["$correct", 1, 0]}, "window": {"documents": w}},
                "conf": {"$avg": "$confidence", "window": {"documents": w}}}}},
            {"$project": {"_id": 0, "arm": 1, "idx": 1, "acc": 1, "conf": 1,
                          "gap": {"$subtract": ["$conf", "$acc"]}}},
            {"$sort": {"arm": 1, "idx": 1}},
        ])
        # V episodes carry a negative ordinal `idx` and their V point's stream index in `v_at` (S2 runner)
        v_points = await self._agg(C.EPISODES, [
            {"$match": {"run_id": run_id, "stream": "v", "v_at": {"$ne": None}, **_idx_le("v_at", at)}},
            {"$group": {"_id": {"arm": "$arm", "idx": "$v_at"}, "acc": {"$avg": {"$cond": ["$correct", 1, 0]}},
                        "n": {"$sum": 1}}},
            {"$project": {"_id": 0, "arm": "$_id.arm", "idx": "$_id.idx", "acc": 1, "n": 1}},
            {"$sort": {"arm": 1, "idx": 1}},
        ])
        paired = await self._agg(C.EPISODES, [
            {"$match": {"run_id": run_id, "stream": "stream", **_idx_le("idx", at)}},
            {"$group": {"_id": "$idx", "by": {"$push": {"k": "$arm", "v": {"$cond": ["$correct", 1, 0]}}}}},
            {"$project": {"_id": 0, "idx": "$_id", "m": {"$arrayToObject": "$by"}}},
            {"$match": {f"m.{reference}": {"$exists": True}}},
            {"$project": {"idx": 1, "d": {"$map": {
                "input": {"$filter": {"input": {"$objectToArray": "$m"}, "cond": {"$ne": ["$$this.k", reference]}}},
                "in": {"arm": "$$this.k", "d": {"$subtract": ["$$this.v", f"$m.{reference}"]}}}}}},
            {"$unwind": "$d"},
            {"$project": {"arm": "$d.arm", "idx": 1, "d": "$d.d"}},
            {"$setWindowFields": {"partitionBy": "$arm", "sortBy": {"idx": 1}, "output": {
                "diff": {"$avg": "$d", "window": {"documents": w}}}}},
            {"$project": {"_id": 0, "arm": 1, "idx": 1, "d": 1, "diff": 1}},
            {"$sort": {"arm": 1, "idx": 1}},
        ])
        rounds = await self._agg(C.ROUNDS, [
            {"$match": {"run_id": run_id}},
            {"$densify": {"field": "round", "partitionByFields": ["arm"], "range": {"step": 1, "bounds": "partition"}}},
            {"$fill": {"partitionByFields": ["arm"], "sortBy": {"round": 1},
                       "output": {"acc_v": {"method": "locf"}, "acc_stream": {"method": "locf"},
                                  "acc_self_assessed": {"method": "locf"}}}},
            {"$project": {"_id": 0}},
            {"$sort": {"arm": 1, "round": 1}},
        ])
        if at is not None:
            rounds = [r for r in rounds if (r.get("idx_range") or [0, 0])[0] <= at]
        if not v_points:   # V readings recorded on `rounds` only (S5's round close), placed at the round's end
            v_points = await self._agg(C.ROUNDS, [
                {"$match": {"run_id": run_id, "acc_v": {"$ne": None}}},
                {"$project": {"_id": 0, "arm": 1, "idx": {"$arrayElemAt": ["$idx_range", 1]}, "acc": "$acc_v"}},
                {"$match": _idx_le("idx", at)}, {"$sort": {"arm": 1, "idx": 1}}])
        return jsonable({"rolling": rolling, "v": v_points, "paired": paired, "rounds": rounds,
                         "reference": reference, "window": window})

    # --- pane 5: why -------------------------------------------------------------------------------

    async def _lineage(self, run_id: str, root: str) -> Doc | None:
        depth = self._s.viewer_why_depth
        docs = await self._agg(C.DECISIONS, [
            {"$match": {"_id": root}},
            {"$project": {"emb": 0}},
            {"$graphLookup": {"from": C.DECISIONS.value, "startWith": _flatten("$latches.edges"),
                              "connectFromField": "latches.edges", "connectToField": "_id", "as": "_ancestors",
                              "maxDepth": depth, "depthField": "depth", "restrictSearchWithMatch": {"run_id": run_id}}},
            {"$graphLookup": {"from": C.DECISIONS.value, "startWith": "$_id", "connectFromField": "_id",
                              "connectToField": "latches.edges", "as": "_descendants", "maxDepth": depth,
                              "depthField": "depth", "restrictSearchWithMatch": {"run_id": run_id}}},
            {"$project": {"_ancestors._id": 1, "_ancestors.depth": 1, "_descendants._id": 1,
                          "_descendants.depth": 1, "warrant": 1}},
        ])
        return docs[0] if docs else None

    async def _explain_hook_match(self, run_id: str, arm: str, terms: Sequence[str]) -> Doc | None:
        """`explain()` of the hook match prefilter (SPEC § 20.3): which index serves consultation."""
        query = {"run_id": run_id, "arm": arm, "lifecycle.status": LifecycleStatus.ADMITTED.value,
                 "latches.fires_when.terms": {"$in": list(terms)}}
        try:
            plan = await self._c(C.DECISIONS).find(query).explain()
        except PyMongoError:
            return None
        names: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if "indexName" in node:
                    names.append(node["indexName"])
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        winning = (plan.get("queryPlanner") or {}).get("winningPlan", {})
        walk(winning)
        return {"query": jsonable(query), "indexes": sorted(set(names)),
                "stage": winning.get("stage") or (winning.get("queryPlan") or {}).get("stage")}

    async def why(self, run_id: str, target: str, *, at: int | None, arm: str | None = None) -> Doc:
        root = await self._c(C.DECISIONS).find_one({"_id": target, "run_id": run_id}, {"_id": 1, "arm": 1})
        term_row = None
        if root is None:
            variants = term_variants(target)
            pattern = re.escape(target.strip()).replace("_", "[ _]").replace(r"\ ", "[ _]")
            matches = await self._c(C.DECISIONS).find(
                {"run_id": run_id, **({"arm": arm} if arm else {}),
                 "$or": [{"latches.fires_when.terms": {"$in": variants}},
                                           {"title": {"$regex": pattern, "$options": "i"}}]},
                {"_id": 1, "arm": 1, "lifecycle": 1}).to_list()
            term_row = await self._db[C.TERMS.value].find_one({"$or": [{"term": {"$in": variants}},
                                                                        {"aliases": {"$in": variants}}]})
            if not matches:
                return jsonable({"target": target, "kind": "term", "term": term_row, "decisions": [],
                                 "trail": None})
            # head of the chain: an admitted decision if any, else the newest by lifecycle index
            matches.sort(key=lambda m: (m["lifecycle"]["status"] != "admitted", -m["lifecycle"]["at_idx"]))
            root = matches[0]
            matched_ids = [m["_id"] for m in matches]
        else:
            matched_ids = [root["_id"]]
            variants = []
        lin = await self._lineage(run_id, root["_id"])
        chain_ids = [root["_id"]]
        if lin:
            chain_ids += [a["_id"] for a in lin["_ancestors"]] + [d["_id"] for d in lin["_descendants"]]
        chain_ids = list(dict.fromkeys(chain_ids + matched_ids))
        chain = await self._decision_rows({"_id": {"$in": chain_ids}}, at)
        depth = {root["_id"]: 0}
        if lin:
            depth |= {a["_id"]: -(a["depth"] + 1) for a in lin["_ancestors"]}
            depth |= {d["_id"]: d["depth"] + 1 for d in lin["_descendants"]}
        for c in chain:
            c["depth"] = depth.get(c["id"])
        chain.sort(key=lambda c: (c["lifecycle"]["admitted_at"], c["id"]))
        trail = await self._agg(C.DECISIONS, [
            {"$match": {"_id": {"$in": chain_ids}}},
            {"$project": {"_id": 1, "warrant": 1}},
            {"$lookup": {"from": C.OBSERVATIONS.value, "localField": "warrant.source_observation_ids",
                         "foreignField": "_id", "as": "observations",
                         "pipeline": [{"$project": {"noticed": 1, "via": 1, "template": 1, "persona": 1,
                                                    "surfaces": 1, "answer": 1, "figure": 1, "round": 1,
                                                    "episode_id": 1, "class": 1}}]}},
            {"$lookup": {"from": C.EPISODES.value, "localField": "warrant.source_episode_ids",
                         "foreignField": "_id", "as": "episodes",
                         "pipeline": [{"$project": {"idx": 1, "text": 1, "template": 1, "answer": 1,
                                                    "figure": 1, "confirmed_figure": 1, "phrasing": 1}}]}},
            {"$lookup": {"from": C.FIRES.value, "localField": "_id", "foreignField": "decision_id", "as": "fires",
                         "pipeline": [{"$match": _idx_le("at_idx", at)}, {"$sort": {"at_idx": 1}}]}},
        ])
        arm = root["arm"]
        hook_terms = next((c["fan"]["hook"]["terms"] for c in chain if c["id"] == root["_id"]), []) or variants
        return jsonable({"target": target, "kind": "term" if term_row is not None or variants else "decision",
                         "term": term_row, "root": root["_id"], "arm": arm, "chain": chain,
                         "trail": {t["_id"]: {k: t[k] for k in ("observations", "episodes", "fires")}
                                   for t in trail},
                         "explain": await self._explain_hook_match(run_id, arm, hook_terms) if hook_terms else None})

    # --- floor beat ------------------------------------------------------------------------------------

    async def floor(self, decision_id_: str) -> Doc | None:
        d = await self._c(C.DECISIONS).find_one({"_id": decision_id_}, {"emb": 0})
        if d is None:
            return None
        dec = Decision.model_validate(d)
        fl = dec.floor
        if fl is None:
            return None
        access = await self._c(C.TOOL_ACCESS).find_one({"decision_id": dec.id})
        view = access["view"] if access else view_name(fl.collection, dec.id)
        names = set(await self._world.list_collection_names())
        rows_logical = await self._world[fl.collection].count_documents({}) if fl.collection in names else None
        rows_view = await self._world[view].count_documents({}) if view in names else None
        rows_match = (await self._world[fl.collection].count_documents(fl.match)
                      if fl.collection in names else None)
        ep = await self._c(C.EPISODES).find_one(
            {"run_id": dec.run_id, "arm": dec.arm, "collection": fl.collection, "pipeline.0": {"$exists": True}},
            {"idx": 1, "text": 1, "pipeline": 1, "answer_path": 1, "view_map": 1, "answer": 1},
            sort=[("idx", -1)])
        rerun = None
        if ep is not None:
            rerun = {"episode_id": ep["_id"], "idx": ep["idx"], "text": ep.get("text"),
                     "pipeline": ep["pipeline"], "on_logical": await self._run(fl.collection, ep["pipeline"], names),
                     "on_view": await self._run(view, ep["pipeline"], names)}
        return jsonable({"decision_id": dec.id, "title": dec.title, "arm": dec.arm, "logical": fl.collection,
                         "view": view, "view_exists": view in names, "match": fl.match,
                         "status": dec.lifecycle.status.value, "residue": dec.residue,
                         "rows_logical": rows_logical, "rows_view": rows_view, "rows_kept_by_match": rows_match,
                         "rerun": rerun})

    async def _run(self, collection: str, pipeline: list[Doc], names: set[str]) -> Doc | None:
        """Re-run a recorded proposer pipeline read-only (executor role, `maxTimeMS`)."""
        if collection not in names:
            return None
        try:
            rows = await (await self._world[collection].aggregate(
                pipeline, maxTimeMS=self._s.execute_max_time_ms)).to_list()
        except PyMongoError as e:
            return {"error": type(e).__name__}
        return {"collection": collection, "n_rows": len(rows), "rows": rows[: self._s.viewer_floor_rows]}

    # --- facets ------------------------------------------------------------------------------------

    async def facets(self, run_id: str, *, at: int | None) -> list[Doc]:
        """Population: stream episodes (`stream: "stream"`, idx ≤ `at`) by arm × template × first-attempt
        correct. `$group`: `episodes_search` is over the sandbox's search-index cap, so `$searchMeta` is not used."""
        rows = await self._agg(C.EPISODES, [
            {"$match": {"run_id": run_id, "stream": "stream", **_idx_le("idx", at)}},
            {"$group": {"_id": {"arm": "$arm", "template": "$template", "correct": "$correct"}, "n": {"$sum": 1}}},
            {"$project": {"_id": 0, "arm": "$_id.arm", "template": "$_id.template", "correct": "$_id.correct",
                          "n": 1}},
            {"$sort": {"arm": 1, "template": 1, "correct": 1}},
        ])
        return jsonable(rows)

    # --- change streams --------------------------------------------------------------------------------

    async def changes(self, run_id: str, collections: Sequence[str]) -> AsyncIterator[Doc]:
        """One database-level change stream over the named stores. Pre-images arrive where enabled
        (`decisions`, `tool_access`); the token is saved after each event so a restarted viewer resumes."""
        consumer = self._s.viewer_consumer
        token = await self._cursors.resume_token(run_id, consumer)
        pipeline = [{"$match": {"ns.coll": {"$in": list(collections)}}}]
        try:
            stream = await self._db.watch(pipeline, full_document="updateLookup",
                                          full_document_before_change="whenAvailable", resume_after=token)
        except OperationFailure:      # an expired or foreign token: start from now
            stream = await self._db.watch(pipeline, full_document="updateLookup",
                                          full_document_before_change="whenAvailable")
        async with stream:
            async for ch in stream:
                await self._cursors.save_resume_token(run_id, consumer, ch["_id"])
                yield change_event(ch)


def change_event(ch: Doc) -> Doc:
    """A change-stream document → the viewer's event: store, op, ids, before/after images (no vectors)."""
    after = ch.get("fullDocument")
    before = ch.get("fullDocumentBeforeChange")
    doc = after or before or {}
    key = (ch.get("documentKey") or {}).get("_id")
    return jsonable({"collection": (ch.get("ns") or {}).get("coll"), "op": ch.get("operationType"),
                     "id": key, "run_id": doc.get("run_id"), "arm": doc.get("arm"),
                     "idx": doc.get("idx", doc.get("at_idx")), "before": before, "after": after,
                     "updated": (ch.get("updateDescription") or {}).get("updatedFields")})
