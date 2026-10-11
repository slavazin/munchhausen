"""Atlas repositories for every store except `decisions` (which has its own module)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from munchhausen.domain.backtest import Backtest
from munchhausen.domain.common import Disposer, FireDisposition, Pipeline
from munchhausen.domain.draft import DirectionRead, Draft, DraftStatus, LayerOutcome
from munchhausen.domain.episode import EVALUATION_ONLY_FIELDS, Episode
from munchhausen.domain.fire import Fire
from munchhausen.domain.lens import LensEntry, LensWeights
from munchhausen.domain.observation import Observation, ObservationDisposition
from munchhausen.domain.registers import Cursor, RoundRecord, RunRecord, SpendRow, Term
from munchhausen.store.codec import from_doc, to_doc
from munchhausen.store.names import C

Doc = dict[str, Any]


class _Ledger[M: BaseModel]:
    """Records keyed by deterministic `_id`; `put` is an idempotent upsert (resume-safe, § 10.4)."""

    model: type[M]

    def __init__(self, coll: AsyncCollection[Doc]) -> None:
        self._c = coll

    async def put(self, record: M) -> None:
        doc = to_doc(record)
        await self._c.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    async def get(self, id_: str) -> M | None:
        return from_doc(self.model, await self._c.find_one({"_id": id_}))


class AtlasEpisodes(_Ledger[Episode]):
    model = Episode

    async def exists(self, run_id: str, arm: str, idx: int) -> bool:
        return await self._c.count_documents({"run_id": run_id, "arm": arm, "idx": idx}, limit=1) > 0

    async def for_learner(self, run_id: str, arm: str, *, with_authority: bool,
                          filter: dict[str, Any] | None = None) -> list[Doc]:
        projection = None if with_authority else {f: 0 for f in EVALUATION_ONLY_FIELDS}
        return await self._c.find({"run_id": run_id, "arm": arm, **(filter or {})}, projection).to_list()

    async def backtest_population(self, run_id: str, arm: str, keys_filter: dict[str, Any], *,
                                  exclude_ids: Sequence[str], after_idx: int | None, n: int) -> list[Episode]:
        match: Doc = {"run_id": run_id, "arm": arm, "stream": "stream", "_id": {"$nin": list(exclude_ids)},
                      **keys_filter}
        if after_idx is not None:
            match["idx"] = {"$gt": after_idx}
        half = max(1, n // 2)
        pipeline: Pipeline = [
            {"$match": match},
            {"$facet": {"hits": [{"$match": {"correct": True}}, {"$sample": {"size": half}}],
                        "misses": [{"$match": {"correct": False}}, {"$sample": {"size": n - half}}]}},
        ]
        docs = await (await self._c.aggregate(pipeline)).to_list()
        rows = docs[0]["hits"] + docs[0]["misses"] if docs else []
        return [Episode.model_validate(d) for d in rows]

    async def consultations_of(self, run_id: str, arm: str, decision_id: str, last_n: int) -> list[Episode]:
        cur = self._c.find({"run_id": run_id, "arm": arm, "consulted.decision_id": decision_id}
                           ).sort("idx", -1).limit(last_n)
        return [Episode.model_validate(d) async for d in cur]

    async def direction_read(self, run_id: str, arm: str, inside: dict[str, Any], *, before_idx: int) -> DirectionRead:
        pipeline: Pipeline = [
            {"$match": {"run_id": run_id, "arm": arm, "stream": "stream", "idx": {"$lt": before_idx}}},
            {"$facet": {side: [{"$match": f}, {"$group": {"_id": None, "n": {"$sum": 1},
                                                          "misses": {"$sum": {"$cond": ["$correct", 0, 1]}}}}]
                        for side, f in (("in", inside), ("out", {"$nor": [inside]}))}},
        ]
        docs = await (await self._c.aggregate(pipeline)).to_list()
        row = {side: (docs[0][side][0] if docs and docs[0][side] else {"n": 0, "misses": 0}) for side in ("in", "out")}
        return DirectionRead(misses_in=row["in"]["misses"], n_in=row["in"]["n"],
                             misses_out=row["out"]["misses"], n_out=row["out"]["n"])


class AtlasObservations(_Ledger[Observation]):
    model = Observation

    async def open_for_pass(self, run_id: str, arm: str, *, since_round: int) -> list[Observation]:
        cur = self._c.find({"run_id": run_id, "arm": arm, "disposition": ObservationDisposition.OPEN.value,
                            "round": {"$gte": since_round}})
        return [Observation.model_validate(d) async for d in cur]

    async def dispose(self, ids: Sequence[str], disposition: ObservationDisposition, by: str) -> None:
        await self._c.update_many({"_id": {"$in": list(ids)}},
                                  {"$set": {"disposition": disposition.value, "disposed_by": by}})


class AtlasFires(_Ledger[Fire]):
    model = Fire

    async def open_for(self, decision_id: str) -> list[Fire]:
        cur = self._c.find({"decision_id": decision_id, "disposition": FireDisposition.OPEN.value})
        return [Fire.model_validate(d) async for d in cur]

    async def dispose(self, fire_ids: Sequence[str], disposition: FireDisposition, disposer: Disposer) -> None:
        await self._c.update_many({"_id": {"$in": list(fire_ids)}},
                                  {"$set": {"disposition": disposition.value, "disposer": disposer.value}})


class AtlasDrafts(_Ledger[Draft]):
    model = Draft

    async def record(self, draft_id: str, outcome: LayerOutcome) -> None:
        await self._c.update_one({"_id": draft_id}, {"$set": {f"adjudication.{outcome.layer}": to_doc(outcome)}})

    async def held(self, run_id: str, arm: str) -> list[Draft]:
        cur = self._c.find({"run_id": run_id, "arm": arm, "status": DraftStatus.HELD.value})
        return [Draft.model_validate(d) async for d in cur]


class AtlasBacktests(_Ledger[Backtest]):
    model = Backtest


class AtlasCursors:
    def __init__(self, coll: AsyncCollection[Doc]) -> None:
        self._c = coll

    async def get(self, run_id: str, arm: str) -> Cursor:
        doc = await self._c.find_one_and_update(
            {"run_id": run_id, "arm": arm}, {"$setOnInsert": {"next_idx": 0, "round": 0, "resume_tokens": {}}},
            upsert=True, return_document=ReturnDocument.AFTER)
        return Cursor.model_validate(doc)

    async def claim_next(self, run_id: str, arm: str, *, limit: int) -> int | None:
        doc = await self._c.find_one_and_update(
            {"run_id": run_id, "arm": arm, "next_idx": {"$lt": limit}}, {"$inc": {"next_idx": 1}},
            return_document=ReturnDocument.BEFORE)
        return None if doc is None else int(doc["next_idx"])

    async def set_round(self, run_id: str, arm: str, round_: int) -> None:
        await self._c.update_one({"run_id": run_id, "arm": arm}, {"$set": {"round": round_}})

    async def save_resume_token(self, run_id: str, consumer: str, token: dict[str, Any]) -> None:
        await self._c.update_one({"run_id": run_id, "arm": "_consumers"},
                                 {"$set": {f"resume_tokens.{consumer}": token}}, upsert=True)


class AtlasLeases:
    def __init__(self, coll: AsyncCollection[Doc], episodes: AsyncCollection[Doc], ttl_s: int) -> None:
        self._c, self._episodes, self._ttl = coll, episodes, ttl_s

    async def acquire(self, run_id: str, arm: str, idx: int, worker: str) -> bool:
        try:
            await self._c.insert_one({"run_id": run_id, "arm": arm, "idx": idx, "worker": worker,
                                      "expires_at": datetime.now(UTC) + timedelta(seconds=self._ttl)})
            return True
        except DuplicateKeyError:
            return False

    async def release(self, run_id: str, arm: str, idx: int) -> None:
        await self._c.delete_one({"run_id": run_id, "arm": arm, "idx": idx})

    async def orphaned(self, run_id: str, arm: str, below_idx: int) -> list[int]:
        done = set(await self._episodes.distinct("idx", {"run_id": run_id, "arm": arm, "idx": {"$lt": below_idx}}))
        leased = set(await self._c.distinct("idx", {"run_id": run_id, "arm": arm}))
        return sorted(set(range(below_idx)) - done - leased)


class AtlasToolAccess:
    def __init__(self, coll: AsyncCollection[Doc]) -> None:
        self._c = coll

    async def view_map(self, run_id: str, arm: str) -> dict[str, str]:
        return {d["logical"]: d["view"] async for d in self._c.find({"run_id": run_id, "arm": arm})}


class AtlasTerms:
    def __init__(self, coll: AsyncCollection[Doc]) -> None:
        self._c = coll

    async def all(self) -> list[Term]:
        return [Term.model_validate(d) async for d in self._c.find({})]

    async def add(self, term: Term) -> None:
        await self._c.update_one({"term": term.term}, {"$setOnInsert": to_doc(term)}, upsert=True)

    async def extract(self, text: str) -> frozenset[str]:
        raise NotImplementedError("M2: $search over `terms` with synonyms; fallback agent/terms.longest_match")


class AtlasRuns:
    def __init__(self, runs: AsyncCollection[Doc], rounds: AsyncCollection[Doc]) -> None:
        self._runs, self._rounds = runs, rounds

    async def start(self, run: RunRecord) -> RunRecord:
        try:
            await self._runs.insert_one(to_doc(run))
            return run
        except DuplicateKeyError:   # resume: the pre-registered record is never edited
            return RunRecord.model_validate(await self._runs.find_one({"_id": run.id}))

    async def put_round(self, round_: RoundRecord) -> None:
        doc = to_doc(round_)
        await self._rounds.replace_one({"run_id": round_.run_id, "arm": round_.arm, "round": round_.round},
                                       doc, upsert=True)


class AtlasSpend:
    def __init__(self, coll: AsyncCollection[Doc]) -> None:
        self._c = coll

    async def record(self, row: SpendRow) -> None:
        await self._c.insert_one(to_doc(row))


class AtlasLenses:
    def __init__(self, entries: AsyncCollection[Doc], weights: AsyncCollection[Doc], seed: LensWeights) -> None:
        self._entries, self._weights, self._seed = entries, weights, seed

    async def entries(self) -> list[LensEntry]:
        return [LensEntry.model_validate(d) async for d in self._entries.find({})]

    async def current_weights(self) -> LensWeights:
        doc = await self._weights.find_one(sort=[("version", -1)])
        return self._seed if doc is None else LensWeights.model_validate(doc)

    async def put_weights(self, weights: LensWeights) -> None:
        await self._weights.insert_one(to_doc(weights))


def repositories(db: AsyncDatabase[Doc], lease_ttl_s: int, seed_weights: LensWeights) -> dict[str, Any]:
    return {
        "episodes": AtlasEpisodes(db[C.EPISODES.value]),
        "observations": AtlasObservations(db[C.OBSERVATIONS.value]),
        "fires": AtlasFires(db[C.FIRES.value]),
        "drafts": AtlasDrafts(db[C.DRAFTS.value]),
        "backtests": AtlasBacktests(db[C.BACKTESTS.value]),
        "cursors": AtlasCursors(db[C.CURSORS.value]),
        "leases": AtlasLeases(db[C.LEASES.value], db[C.EPISODES.value], lease_ttl_s),
        "tool_access": AtlasToolAccess(db[C.TOOL_ACCESS.value]),
        "terms": AtlasTerms(db[C.TERMS.value]),
        "runs": AtlasRuns(db[C.RUNS.value], db[C.ROUNDS.value]),
        "spend": AtlasSpend(db[C.SPEND.value]),
        "lenses": AtlasLenses(db[C.LENSES.value], db[C.LENS_WEIGHTS.value], seed_weights),
    }
