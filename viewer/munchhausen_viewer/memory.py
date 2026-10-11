"""`MemoryReadModel`: the `ReadModel` port over in-memory records (tests, and `munchhausen viewer
--synthetic` when Atlas is out of reach). Projections are the same pure functions the Atlas read model
uses (`munchhausen.store.read_models`), so both render identical rows."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from typing import Any

from munchhausen.domain.decision import Decision
from munchhausen.domain.fire import Fire
from munchhausen.domain.ids import backtest_id, decision_id
from munchhausen.store.read_models import backtest_view, decision_view, floor_rewires, jsonable, term_variants
from munchhausen_viewer.synthetic import SyntheticRun, apply_plan

Doc = dict[str, Any]


class MemoryReadModel:
    def __init__(self, sr: SyntheticRun, round_size: int) -> None:
        self.sr, self._R = sr, round_size
        self.decisions_: dict[str, Decision] = {}
        self.fires_: list[Fire] = list(sr.fires)
        for _, plan in sr.admissions:
            apply_plan(self.decisions_, self.fires_, plan)
        self.events: asyncio.Queue[Doc] = asyncio.Queue()

    # helpers
    def _eps(self, run_id: str) -> list[Any]:
        return [e for e in self.sr.episodes if e.run_id == run_id]

    def _admitted_at(self, d: Decision) -> int:
        if d.is_admitted:
            return d.lifecycle.at_idx
        rounds = {decision_id(x.id): x.round for x in self.sr.drafts}
        return min((rounds.get(d.id, 0) + 1) * self._R - 1, d.lifecycle.at_idx)

    def _view(self, d: Decision, at: int | None) -> Doc:
        fires = [f.model_dump(mode="json") for f in self.fires_ if f.decision_id == d.id]
        bt = next((b for b in self.sr.backtests if b.id == d.warrant.backtest_id), None)
        return decision_view(d, admitted_at=self._admitted_at(d), at=at, fires=fires,
                             backtest=bt.model_dump(by_alias=True, mode="json") if bt else None, view=None)

    async def runs(self) -> list[Doc]:
        eps = self._eps(self.sr.run_id)
        return [{"run_id": self.sr.run_id, "episodes": len(eps), "arms": sorted({e.arm for e in eps}),
                 "max_idx": max(e.idx for e in eps), "registered": True}]

    async def timeline(self, run_id: str) -> Doc:
        eps = self._eps(run_id)
        arms: dict[str, Doc] = {}
        for e in eps:
            a = arms.setdefault(e.arm, {"max_idx": 0, "n": 0})
            a["max_idx"], a["n"] = max(a["max_idx"], e.idx), a["n"] + 1
        return {"run_id": run_id, "arms": arms, "max_idx": max((a["max_idx"] for a in arms.values()), default=0),
                "templates": sorted({e.template for e in eps}),
                "streams": {s: sum(e.stream == s for e in eps) for s in {e.stream for e in eps}},
                "counts": {"decisions": len(self.decisions_), "drafts": len(self.sr.drafts),
                           "fires": len(self.fires_), "backtests": len(self.sr.backtests)}}

    async def decisions(self, run_id: str, arm: str, *, at: int | None) -> list[Doc]:
        rows = [self._view(d, at) for d in self.decisions_.values() if d.run_id == run_id and d.arm == arm]
        rows = [r for r in rows if r["status"] is not None]
        rows.sort(key=lambda r: (r["status"] != "admitted", -r["lifecycle"]["admitted_at"]))
        return jsonable(rows)

    async def fires(self, run_id: str, arms: Sequence[str], *, at: int | None, limit: int) -> list[Doc]:
        eps = {e.id: e for e in self._eps(run_id)}
        out: list[Doc] = []
        for f in self.fires_:
            if f.arm not in arms or (at is not None and f.at_idx > at):
                continue
            d = self.decisions_.get(f.decision_id)
            res = [{**r.model_dump(mode="json"), "idx": eps[e].idx, "template": eps[e].template}
                   for e in f.episode_ids if e in eps for r in eps[e].residuals if r.id in f.residual_ids]
            out.append({"type": "fire", "id": f.id, "arm": f.arm, "decision_id": f.decision_id,
                        "title": d.title if d else None, "kind": d.kind.value if d else None,
                        "decision_status": d.lifecycle.status.value if d else None, "latch": f.latch,
                        "role": f.role.value, "cause": f.cause.value, "disposition": f.disposition.value,
                        "disposer": f.disposer.value if f.disposer else None, "at_idx": f.at_idx, "note": f.note,
                        "episodes": [{"id": e, "idx": eps[e].idx, "template": eps[e].template}
                                     for e in f.episode_ids if e in eps], "residuals": res})
        floors = [self._view(d, at) for d in self.decisions_.values() if d.arm in arms and d.floor is not None]
        out += [r for r in floor_rewires(floors) if at is None or r["at_idx"] <= at]
        out.sort(key=lambda r: -(r.get("at_idx") or 0))
        return jsonable(out[:limit])

    async def latest_episode(self, run_id: str, arm: str, *, at: int | None, stream: str | None = None) -> Doc | None:
        eps = [e for e in self._eps(run_id) if e.arm == arm and (at is None or e.idx <= at)
               and (stream is None or e.stream == stream)]
        if not eps:
            return None
        e = max(eps, key=lambda x: (x.idx, x.id))
        doc = e.model_dump(by_alias=True, mode="json")
        doc["consulted"] = [{**c, "title": getattr(self.decisions_.get(c["decision_id"]), "title", None),
                             "kind": getattr(getattr(self.decisions_.get(c["decision_id"]), "kind", None), "value",
                                             None)} for c in doc["consulted"]]
        doc["resolved_collection"] = doc["view_map"].get(doc["collection"], doc["collection"])
        doc["id"] = doc.pop("_id")
        return doc

    async def drafts(self, run_id: str, arm: str, *, at: int | None, limit: int) -> list[Doc]:
        rows = [d for d in self.sr.drafts if d.run_id == run_id and d.arm == arm
                and (at is None or d.round * self._R <= at)]
        rows.sort(key=lambda d: -d.round)
        return [{"id": d.id, "title": d.title, "kind": d.kind.value, "status": d.status.value,
                 "route": d.route.value, "round": d.round, "supersedes": d.supersedes,
                 "adjudication": {k: v.model_dump(mode="json") for k, v in d.adjudication.items()}}
                for d in rows[:limit]]

    async def draft(self, draft_id: str) -> Doc | None:
        d = next((x for x in self.sr.drafts if x.id == draft_id), None)
        if d is None:
            return None
        bt = next((b for b in self.sr.backtests if b.id == backtest_id(draft_id)), None)
        doc = d.model_dump(by_alias=True, mode="json")
        doc["id"] = doc.pop("_id")
        doc["backtest"] = backtest_view(bt.model_dump(by_alias=True, mode="json")) if bt else None
        doc["sources"] = [o.model_dump(by_alias=True, mode="json", exclude={"emb"})
                          for o in self.sr.observations if o.id in d.source_observation_ids]
        return doc

    async def curves(self, run_id: str, *, reference: str, window: int, at: int | None) -> Doc:
        stream = sorted((e for e in self._eps(run_id) if e.stream == "stream" and (at is None or e.idx <= at)),
                        key=lambda e: (e.arm, e.idx))
        rolling: list[Doc] = []
        by_arm: dict[str, list[Any]] = {}
        for e in stream:
            by_arm.setdefault(e.arm, []).append(e)
        for arm, eps in by_arm.items():
            for k, e in enumerate(eps):
                w = eps[max(0, k - window + 1): k + 1]
                acc = sum(x.correct for x in w) / len(w)
                conf = sum(x.confidence for x in w) / len(w)
                rolling.append({"arm": arm, "idx": e.idx, "acc": acc, "conf": conf, "gap": conf - acc})
        ref = {e.idx: int(e.correct) for e in by_arm.get(reference, [])}
        paired: list[Doc] = []
        for arm, eps in by_arm.items():
            if arm == reference:
                continue
            ds = [(e.idx, int(e.correct) - ref[e.idx]) for e in eps if e.idx in ref]
            for k, (idx, d) in enumerate(ds):
                w = ds[max(0, k - window + 1): k + 1]
                paired.append({"arm": arm, "idx": idx, "d": d, "diff": sum(x[1] for x in w) / len(w)})
        v: dict[tuple[str, int], list[int]] = {}
        for e in self._eps(run_id):
            if e.stream == "v" and (at is None or e.idx <= at):
                v.setdefault((e.arm, e.idx), []).append(int(e.correct))
        return {"rolling": rolling, "paired": paired, "reference": reference, "window": window,
                "v": [{"arm": a, "idx": i, "acc": sum(x) / len(x), "n": len(x)} for (a, i), x in sorted(v.items())],
                "rounds": [r.model_dump(mode="json") for r in self.sr.rounds
                           if at is None or r.idx_range[0] <= at]}

    async def why(self, run_id: str, target: str, *, at: int | None, arm: str | None = None) -> Doc:
        decs = {d.id: d for d in self.decisions_.values() if d.run_id == run_id}
        if target in decs:
            arm = decs[target].arm
        decs = {i: d for i, d in decs.items() if arm is None or d.arm == arm}
        if target in decs:
            matched = [decs[target]]
        else:
            vs = set(term_variants(target))
            matched = [d for d in decs.values() if vs & set(d.hook.fires_when.terms)
                       or target.lower().replace("_", " ") in d.title.lower()]
        if not matched:
            return {"target": target, "kind": "term", "term": None, "decisions": [], "trail": None}
        chain_ids: set[str] = set()
        frontier = [d.id for d in matched]
        while frontier:   # both directions over wiring edges, as the $graphLookup pair does
            x = frontier.pop()
            if x in chain_ids or x not in decs:
                continue
            chain_ids.add(x)
            frontier += list(decs[x].wiring.edges)
            frontier += [d.id for d in decs.values() if x in d.wiring.edges]
        chain = sorted((self._view(decs[i], at) for i in chain_ids), key=lambda c: c["lifecycle"]["admitted_at"])
        eps = {e.id: e for e in self._eps(run_id)}
        trail = {i: {"observations": [o.model_dump(by_alias=True, mode="json") for o in self.sr.observations
                                      if o.id in decs[i].warrant.source_observation_ids],
                     "episodes": [{"_id": e, "idx": eps[e].idx, "text": eps[e].text, "template": eps[e].template}
                                  for e in decs[i].warrant.source_episode_ids if e in eps],
                     "fires": [f.model_dump(by_alias=True, mode="json") for f in self.fires_
                               if f.decision_id == i and (at is None or f.at_idx <= at)]} for i in chain_ids}
        root = sorted(matched, key=lambda d: (not d.is_admitted, -d.lifecycle.at_idx))[0]
        return jsonable({"target": target, "kind": "decision" if target in decs else "term", "term": None,
                         "root": root.id, "arm": root.arm, "chain": chain, "trail": trail,
                         "explain": {"indexes": ["latches.fires_when.terms_1"], "stage": "memory"}})

    async def floor(self, decision_id_: str) -> Doc | None:
        d = self.decisions_.get(decision_id_)
        if d is None or d.floor is None:
            return None
        return {"decision_id": d.id, "title": d.title, "arm": d.arm, "logical": d.floor.collection,
                "view": f"{d.floor.collection}__{d.id}", "view_exists": False, "match": d.floor.match,
                "status": d.lifecycle.status.value, "residue": d.residue, "rows_logical": None,
                "rows_view": None, "rows_kept_by_match": None, "rerun": None}

    async def facets(self, run_id: str, *, at: int | None) -> list[Doc]:
        agg: dict[tuple[str, str, bool], int] = {}
        for e in self._eps(run_id):
            if at is None or e.idx <= at:
                k = (e.arm, e.template, e.correct)
                agg[k] = agg.get(k, 0) + 1
        return [{"arm": a, "template": t, "correct": c, "n": n} for (a, t, c), n in sorted(agg.items())]

    async def changes(self, run_id: str, collections: Sequence[str]) -> AsyncIterator[Doc]:
        while True:
            yield await self.events.get()
