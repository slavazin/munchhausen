"""Atlas repositories for every store except `decisions` (which has its own module)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError, OperationFailure

from munchhausen.agent.terms import present_terms
from munchhausen.domain.backtest import Backtest
from munchhausen.domain.common import Disposer, FireDisposition, Pipeline
from munchhausen.domain.draft import DirectionRead, Draft, DraftStatus, LayerOutcome
from munchhausen.domain.episode import EVALUATION_ONLY_FIELDS, Episode
from munchhausen.domain.fire import Fire
from munchhausen.domain.lens import LensEntry, LensWeights
from munchhausen.domain.observation import Observation, ObservationDisposition
from munchhausen.domain.registers import Cursor, PlantedMapping, RoundRecord, RunRecord, SpendRow, Term, ToolAccess
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

    async def backtest_sample(self, run_id: str, arm: str, match: dict[str, Any], *, n: int,
                              seed: int | None, prefer_terms: Sequence[str] = ()) -> list[Episode]:
        def branch(correct: bool) -> Pipeline:
            head: Pipeline = [{"$match": {"correct": correct}}]
            # misses whose terms meet the hook's come first (M3: collection-only matches dilute the read)
            prefer = bool(prefer_terms) and not correct
            tm = {"$cond": [{"$gt": [{"$size": {"$setIntersection": [{"$ifNull": ["$terms", []]},
                                                                      sorted(prefer_terms)]}}, 0]}, 0, 1]}
            if seed is None:
                if not prefer:
                    return [*head, {"$sample": {"size": n}}]
                return [*head, {"$addFields": {"_tm": tm, "_r": {"$rand": {}}}}, {"$sort": {"_tm": 1, "_r": 1}},
                        {"$limit": n}, {"$project": {"_tm": 0, "_r": 0}}]
            key = {"$toHashedIndexKey": {"$concat": [f"{seed}:", {"$toString": "$_id"}]}}
            fields: dict[str, Any] = {"_bk": key, "_tm": tm if prefer else 0}
            return [*head, {"$addFields": fields}, {"$sort": {"_tm": 1, "_bk": 1, "_id": 1}}, {"$limit": n},
                    {"$project": {"_bk": 0, "_tm": 0}}]

        pipeline: Pipeline = [{"$match": {**match, "run_id": run_id, "arm": arm}},
                              {"$facet": {"hits": branch(True), "misses": branch(False)}}]
        docs = await (await self._c.aggregate(pipeline)).to_list()
        hits, misses = (docs[0]["hits"], docs[0]["misses"]) if docs else ([], [])
        return [Episode.model_validate(d) for d in balance(hits, misses, n)]

    async def direction_read_window(self, run_id: str, arm: str, inside: dict[str, Any], *, before_idx: int,
                                    after_idx: int | None = None, last_n: int | None = None) -> DirectionRead:
        lo = after_idx if after_idx is not None else 0
        if last_n is not None:
            cur = self._c.find({"run_id": run_id, "arm": arm, "stream": "stream",
                                "idx": {"$gte": lo, "$lt": before_idx}, **inside}, {"idx": 1}
                               ).sort("idx", -1).skip(max(0, last_n - 1)).limit(1)
            nth = [d async for d in cur]
            if nth:
                lo = max(lo, int(nth[0]["idx"]))
        pipeline: Pipeline = [
            {"$match": {"run_id": run_id, "arm": arm, "stream": "stream", "idx": {"$gte": lo, "$lt": before_idx}}},
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

    async def open_for_pass(self, run_id: str, arm: str, *, since_round: int,
                            exclude_via: Sequence[str] = ("injection",)) -> list[Observation]:
        q: Doc = {"run_id": run_id, "arm": arm, "disposition": ObservationDisposition.OPEN.value,
                  "round": {"$gte": since_round}}
        if exclude_via:
            q["via"] = {"$nin": list(exclude_via)}
        cur = self._c.find(q)
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

    async def for_decision(self, decision_id: str) -> list[Fire]:
        cur = self._c.find({"decision_id": decision_id}).sort("at_idx", 1)
        return [Fire.model_validate(d) async for d in cur]


class AtlasDrafts(_Ledger[Draft]):
    model = Draft

    async def record(self, draft_id: str, outcome: LayerOutcome) -> None:
        await self._c.update_one({"_id": draft_id}, {"$set": {f"adjudication.{outcome.layer}": to_doc(outcome)}})

    async def held(self, run_id: str, arm: str) -> list[Draft]:
        cur = self._c.find({"run_id": run_id, "arm": arm, "status": DraftStatus.HELD.value})
        return [Draft.model_validate(d) async for d in cur]

    async def set_status(self, draft_id: str, status: DraftStatus) -> None:
        await self._c.update_one({"_id": draft_id}, {"$set": {"status": status.value}})


class AtlasBacktests(_Ledger[Backtest]):
    model = Backtest

    async def for_arm(self, run_id: str, arm: str) -> list[Backtest]:
        cur = self._c.find({"run_id": run_id, "arm": arm}).sort("$natural", 1)
        return [Backtest.model_validate(d) async for d in cur]


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

    async def resume_token(self, run_id: str, consumer: str) -> dict[str, Any] | None:
        doc = await self._c.find_one({"run_id": run_id, "arm": "_consumers"}, {f"resume_tokens.{consumer}": 1})
        return ((doc or {}).get("resume_tokens") or {}).get(consumer)


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

    async def take_over(self, run_id: str, arm: str, idx: int, worker: str) -> bool:
        """S2 (M2): take a lease whose TTL has passed (Atlas's TTL monitor deletes expired rows only
        about once a minute), so a resumed worker re-issues an orphaned index without waiting for it."""
        now = datetime.now(UTC)
        doc = await self._c.find_one_and_update(
            {"run_id": run_id, "arm": arm, "idx": idx, "expires_at": {"$lt": now}},
            {"$set": {"worker": worker, "expires_at": now + timedelta(seconds=self._ttl)}})
        return doc is not None or await self.acquire(run_id, arm, idx, worker)


class AtlasToolAccess:
    def __init__(self, coll: AsyncCollection[Doc]) -> None:
        self._c = coll

    async def view_map(self, run_id: str, arm: str) -> dict[str, str]:
        return {d["logical"]: d["view"] async for d in self._c.find({"run_id": run_id, "arm": arm})}

    async def rewires(self, run_id: str, arm: str) -> list[ToolAccess]:
        return [ToolAccess.model_validate(d) async for d in self._c.find({"run_id": run_id, "arm": arm})]


class AtlasTerms:
    def __init__(self, coll: AsyncCollection[Doc]) -> None:
        self._c = coll

    async def all(self) -> list[Term]:
        return [Term.model_validate(d) async for d in self._c.find({})]

    async def add(self, term: Term) -> None:
        await self._c.update_one({"term": term.term}, {"$setOnInsert": to_doc(term)}, upsert=True)

    async def extract(self, text: str) -> frozenset[str]:
        """`$search` over `terms_search` (with the `term_synonyms` mapping) for candidate rows, then the one
        definition of presence (`agent.terms.present_terms`) over them. When the index is absent or not READY,
        the same definition runs over every row (the in-process fallback, SPEC § 20.3)."""
        if not text or not text.strip():
            return frozenset()
        rows: list[Term] | None = None
        if self._search_ok is None:
            self._search_ok = await self._search_ready()
        if self._search_ok:
            try:
                pipeline: Pipeline = [
                    {"$search": {"index": "terms_search",
                                 "text": {"query": text, "path": ["term", "aliases"], "synonyms": "term_synonyms"}}},
                    {"$limit": self._search_limit},
                ]
                rows = [Term.model_validate(d) async for d in await self._c.aggregate(pipeline)]
                self._search_ok = True
            except OperationFailure:          # index absent, not READY, or synonyms not compiled yet
                self._search_ok, rows = False, None
        if rows is None:
            rows = await self.all()
        return present_terms(text, rows)

    # --- S2 (M2) additions ------------------------------------------------------------------------------

    _search_ok: bool | None = None            # None: untried; False: fall back for this process
    _search_limit: int = 100                  # AtlasStore sets TERMS_SEARCH_LIMIT

    def configure_search(self, *, limit: int) -> None:
        self._search_limit = limit

    async def _search_ready(self) -> bool:
        try:
            async for ix in await self._c.list_search_indexes("terms_search"):
                return bool(ix.get("queryable")) and ix.get("status") == "READY"
        except OperationFailure:
            return False
        return False

    async def compile_synonyms(self) -> int:
        """Write the `term_synonyms` mapping `terms_search` reads: one equivalence row per term with aliases.
        Idempotent (keyed by the term); returns the number of mappings."""
        syn = self._c.database[C.TERM_SYNONYMS.value]
        n = 0
        async for d in self._c.find({"aliases.0": {"$exists": True}}):
            await syn.replace_one({"_id": d["term"]}, {"_id": d["term"], "mappingType": "equivalent",
                                                      "synonyms": [d["term"], *d["aliases"]]}, upsert=True)
            n += 1
        return n


class AtlasRuns:
    def __init__(self, runs: AsyncCollection[Doc], rounds: AsyncCollection[Doc],
                 episodes: AsyncCollection[Doc] | None = None) -> None:
        self._runs, self._rounds, self._episodes = runs, rounds, episodes

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

    # --- M4 evidence (additive) ------------------------------------------------------------------------

    async def get(self, run_id: str) -> RunRecord | None:
        return from_doc(RunRecord, await self._runs.find_one({"_id": run_id}))

    async def list_runs(self, limit: int) -> list[RunRecord]:
        cur = self._runs.find({}).sort("started_at", -1).limit(limit)
        return [RunRecord.model_validate(d) async for d in cur]

    async def finish(self, run_id: str, at: datetime, models_served: dict[str, Any] | None = None,
                     lost_spend_writes: int = 0) -> None:
        await self._runs.update_one({"_id": run_id}, {"$set": {"ended_at": at, "models_served": models_served or {}},
                                                      "$inc": {"lost_spend_writes": lost_spend_writes}})

    async def append_resume(self, run_id: str, entry: dict[str, Any]) -> None:
        await self._runs.update_one({"_id": run_id}, {"$push": {"resumes": entry}})

    async def merge_round(self, run_id: str, arm: str, round_: int, idx_range: tuple[int, int]) -> None:
        if self._episodes is None:
            raise RuntimeError("AtlasRuns was built without the episodes collection")
        await (await self._episodes.aggregate(round_pipeline(run_id, arm, round_, idx_range))).to_list()
        key = {"run_id": run_id, "arm": arm, "round": round_}
        if not await self._rounds.count_documents(key, limit=1):   # no episodes in range: an empty record
            await self.put_round(RoundRecord(run_id=run_id, arm=arm, round=round_, idx_range=idx_range,
                                             closed_at=datetime.now(UTC)))


PLANTED_MAP = "planted_map"     # evaluation-only collection (S5); created on first write, no validator


INJECTION = "injection"   # Draft.source / Observation.via / spend meta.source of the injection beat (S6)


def round_pipeline(run_id: str, arm: str, round_: int, idx_range: tuple[int, int],
                   inject_stage: str = "inject") -> Pipeline:
    """The round record, computed in Atlas and `$merge`d into `rounds` (SPEC § 20.2). Run over `episodes`.

    Populations: stream accuracy, self-assessed accuracy and the calibration gap over stream episodes with
    `idx` in `idx_range` (half-open: lo ≤ idx < hi, as the runner emits it);
    V accuracy over `stream: "v"` episodes whose `v_at` (else `idx`) is in
    range; lifecycle counts from `drafts` of this round (admitted/refused) and from `decisions` whose
    `lifecycle.at_idx` is in range (superseded/moot/retired/converged); fires by role with `at_idx` in range;
    `usd_cum` = the arm's spend so far, `usd` = `usd_cum` − the previous round's `usd_cum`.
    The injection beat is excluded throughout: drafts with `source: injection`, observations with
    `via: injection`, spend with `meta.stage == inject_stage` (INJECT_STAGE) or `meta.source: injection`.
    Accuracy, self-assessed accuracy and the gap exclude episodes with `error` (counted in `n_error`).
    Tokens come from `spend` rows whose `meta.episode_id` is one of the round's stream episodes; with none
    attributed they are null, never 0."""
    lo, hi = idx_range
    in_range = {"$gte": lo, "$lt": hi}
    is_stream = {"$eq": ["$stream", "stream"]}
    v_at = {"$ifNull": ["$v_at", "$idx"]}
    is_v = {"$and": [{"$eq": ["$stream", "v"]}, {"$gte": [v_at, lo]}, {"$lt": [v_at, hi]}]}
    in_idx = {"$and": [{"$gte": ["$idx", lo]}, {"$lt": ["$idx", hi]}]}
    stream_in = {"$and": [is_stream, in_idx]}
    errored = {"$gt": [{"$ifNull": ["$error", None]}, None]}
    scored = {"$and": [stream_in, {"$not": [errored]}]}

    def when(cond: Any, val: Any) -> Doc:
        return {"$sum": {"$cond": [cond, val, 0]}}

    return [
        {"$match": {"run_id": run_id, "arm": arm}},
        {"$match": {"$or": [{"idx": in_range}, {"v_at": in_range}]}},
        {"$group": {
            "_id": None,
            "n_stream": when(stream_in, 1),
            "n_error": when({"$and": [stream_in, errored]}, 1),
            "n_scored": when(scored, 1),
            "correct": when({"$and": [scored, "$correct"]}, 1),
            "conf": when(scored, "$confidence"),
            "ids": {"$push": {"$cond": [stream_in, "$_id", "$$REMOVE"]}},
            "n_v": when(is_v, 1),
            "correct_v": when({"$and": [is_v, "$correct"]}, 1),
            "view_filtered": when({"$and": [stream_in, {"$gt": [{"$size": {"$objectToArray": {
                "$ifNull": ["$view_map", {}]}}}, 0]}]}, 1),
        }},
        {"$lookup": {"from": C.SPEND.value, "let": {"ids": "$ids"}, "pipeline": [
            {"$match": {"meta.run_id": run_id, "meta.arm": arm, "meta.episode_id": {"$exists": True}}},
            {"$match": {"$expr": {"$in": ["$meta.episode_id", "$$ids"]}}},
            {"$group": {"_id": None, "tin": {"$sum": "$tokens_in"}, "tout": {"$sum": "$tokens_out"},
                        "eps": {"$addToSet": "$meta.episode_id"}}}], "as": "toks"}},
        {"$lookup": {"from": C.DRAFTS.value, "pipeline": [
            {"$match": {"run_id": run_id, "arm": arm, "round": round_, "source": {"$ne": INJECTION}}},
            {"$group": {"_id": "$status", "n": {"$sum": 1}}}], "as": "drafts"}},
        {"$lookup": {"from": C.DECISIONS.value, "pipeline": [
            {"$match": {"run_id": run_id, "arm": arm, "lifecycle.at_idx": in_range}},
            {"$group": {"_id": "$lifecycle.status", "n": {"$sum": 1}}}], "as": "flips"}},
        {"$lookup": {"from": C.DECISIONS.value, "pipeline": [
            {"$match": {"run_id": run_id, "arm": arm, "lifecycle.status": "admitted"}},
            {"$count": "n"}], "as": "store_admitted"}},
        {"$lookup": {"from": C.OBSERVATIONS.value, "pipeline": [
            {"$match": {"run_id": run_id, "arm": arm, "disposition": "open", "via": {"$ne": INJECTION}}},
            {"$count": "n"}], "as": "store_open_obs"}},
        {"$lookup": {"from": C.FIRES.value, "pipeline": [
            {"$match": {"run_id": run_id, "arm": arm, "at_idx": in_range}},
            {"$group": {"_id": "$role", "n": {"$sum": 1}}}], "as": "fires"}},
        {"$lookup": {"from": C.SPEND.value, "pipeline": [
            {"$match": {"meta.run_id": run_id, "meta.arm": arm, "meta.stage": {"$ne": inject_stage},
                        "meta.source": {"$ne": INJECTION}}},
            {"$group": {"_id": None, "usd": {"$sum": "$usd"}}}], "as": "spend"}},
        {"$lookup": {"from": C.ROUNDS.value, "pipeline": [
            {"$match": {"run_id": run_id, "arm": arm, "round": round_ - 1}},
            {"$project": {"usd_cum": 1}}], "as": "prev"}},
        {"$set": {
            "_cnt": {"$arrayToObject": {"$map": {"input": "$drafts", "in": {"k": "$$this._id", "v": "$$this.n"}}}},
            "_flip": {"$arrayToObject": {"$map": {"input": "$flips", "in": {"k": "$$this._id", "v": "$$this.n"}}}},
            "_usd_cum": {"$ifNull": [{"$first": "$spend.usd"}, 0]},
            "_usd_prev": {"$ifNull": [{"$first": "$prev.usd_cum"}, 0]},
            "_tin": {"$first": "$toks.tin"}, "_tout": {"$first": "$toks.tout"},
        }},
        {"$project": {
            "_id": 0, "run_id": {"$literal": run_id}, "arm": {"$literal": arm}, "round": {"$literal": round_},
            "idx_range": {"$literal": [lo, hi]},
            "n_stream": 1, "n_error": 1,
            "acc_stream": {"$cond": [{"$gt": ["$n_scored", 0]}, {"$divide": ["$correct", "$n_scored"]}, None]},
            "acc_self_assessed": {"$cond": [{"$gt": ["$n_scored", 0]}, {"$divide": ["$conf", "$n_scored"]}, None]},
            "calibration_gap": {"$cond": [{"$gt": ["$n_scored", 0]},
                                          {"$divide": [{"$subtract": ["$conf", "$correct"]}, "$n_scored"]}, None]},
            "acc_v": {"$cond": [{"$gt": ["$n_v", 0]}, {"$divide": ["$correct_v", "$n_v"]}, None]},
            "store_sizes": {"decisions_admitted": {"$ifNull": [{"$first": "$store_admitted.n"}, 0]},
                            "observations_open": {"$ifNull": [{"$first": "$store_open_obs.n"}, 0]}},
            "admitted": {"$ifNull": ["$_cnt.admitted", 0]},
            "refused": {"$ifNull": ["$_cnt.refused", 0]},
            "superseded": {"$ifNull": ["$_flip.superseded", 0]},
            "retired": {"$ifNull": ["$_flip.retired", 0]},
            "moot": {"$ifNull": ["$_flip.moot", 0]},
            "converged": {"$ifNull": ["$_flip.converged", 0]},
            "fires": {"$arrayToObject": {"$map": {"input": "$fires", "in": {"k": "$$this._id", "v": "$$this.n"}}}},
            "view_filtered": 1,
            "tokens_in": {"$ifNull": ["$_tin", None]}, "tokens_out": {"$ifNull": ["$_tout", None]},
            "tokens_per_episode": {"$cond": [{"$and": [{"$gt": ["$n_stream", 0]},
                                                       {"$ne": [{"$ifNull": ["$_tin", None]}, None]}]},
                                             {"$divide": [{"$add": ["$_tin", "$_tout"]}, "$n_stream"]}, None]},
            "usd_cum": "$_usd_cum",
            "usd": {"$subtract": ["$_usd_cum", "$_usd_prev"]},
            "usd_per_episode": {"$cond": [{"$gt": ["$n_stream", 0]},
                                          {"$divide": [{"$subtract": ["$_usd_cum", "$_usd_prev"]}, "$n_stream"]},
                                          None]},
            "schema_version": {"$literal": 1},
            "closed_at": "$$NOW",
        }},
        {"$merge": {"into": C.ROUNDS.value, "on": ["run_id", "arm", "round"],
                    "whenMatched": "replace", "whenNotMatched": "insert"}},
    ]


_HEAVY = {"emb": 0}
_EPISODE_FIELDS = {f: 1 for f in ("run_id", "arm", "idx", "stream", "question_id", "template", "persona", "terms",
                                  "consulted", "view_map", "answer", "confidence", "correct", "figure",
                                  "confirmed_figure", "retry_correct", "error", "tokens", "latency_ms",
                                  "world_version", "v_at", "residuals", "matched_ids", "collections")}


class AtlasEvidence:
    """Read-only evidence over one run, plus the planted map (evaluation-only)."""

    def __init__(self, db: AsyncDatabase[Doc]) -> None:
        self._db = db

    async def episode_count(self, run_id: str) -> int:
        return await self._db[C.EPISODES.value].count_documents({"run_id": run_id})

    async def snapshot(self, run_id: str) -> dict[str, list[Doc]]:
        q = {"run_id": run_id}
        out: dict[str, list[Doc]] = {
            "episodes": await self._db[C.EPISODES.value].find(q, _EPISODE_FIELDS).sort("idx", 1).to_list(),
        }
        for name in (C.DECISIONS, C.FIRES, C.BACKTESTS, C.DRAFTS, C.ROUNDS, C.TOOL_ACCESS):
            out[name.value] = await self._db[name.value].find(q, _HEAVY).to_list()
        out[PLANTED_MAP] = await self._db[PLANTED_MAP].find(q).to_list()
        return out

    async def spend_summary(self, run_id: str) -> list[Doc]:
        pipeline: Pipeline = [
            {"$match": {"meta.run_id": run_id}},
            {"$group": {"_id": {"arm": "$meta.arm", "stage": "$meta.stage", "model": "$meta.model"},
                        "calls": {"$sum": 1},
                        "errors": {"$sum": {"$cond": [{"$eq": ["$ok", False]}, 1, 0]}},
                        "tokens_in": {"$sum": "$tokens_in"}, "tokens_out": {"$sum": "$tokens_out"},
                        "cache_read": {"$sum": {"$ifNull": ["$tokens_cache_read", 0]}},
                        "cache_write": {"$sum": {"$ifNull": ["$tokens_cache_write", 0]}},
                        "usd": {"$sum": "$usd"}, "latency_ms_mean": {"$avg": "$latency_ms"},
                        "served": {"$addToSet": "$served_model"},
                        "error_kinds": {"$push": "$error"}}},
            {"$set": {"served": {"$filter": {"input": "$served", "cond": {"$ne": ["$$this", None]}}},
                      "error_kinds": {"$filter": {"input": "$error_kinds", "cond": {"$ne": ["$$this", None]}}}}},
            {"$replaceWith": {"$mergeObjects": ["$_id", "$$ROOT"]}},
            {"$project": {"_id": 0}},
            {"$sort": {"arm": 1, "stage": 1, "model": 1}},
        ]
        return await (await self._db[C.SPEND.value].aggregate(pipeline)).to_list()

    async def put_mapping(self, mapping: PlantedMapping) -> None:
        doc = to_doc(mapping)
        await self._db[PLANTED_MAP].replace_one({"_id": doc["_id"]}, doc, upsert=True)


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
        "runs": AtlasRuns(db[C.RUNS.value], db[C.ROUNDS.value], db[C.EPISODES.value]),
        "evidence": AtlasEvidence(db),
        "spend": AtlasSpend(db[C.SPEND.value]),
        "lenses": AtlasLenses(db[C.LENSES.value], db[C.LENS_WEIGHTS.value], seed_weights),
    }


def balance[T](hits: Sequence[T], misses: Sequence[T], n: int) -> list[T]:
    """Half from each stratum; a short stratum is topped up from the other's remainder, in branch order."""
    h, m = list(hits[: n // 2]), list(misses[: n - n // 2])
    short = n - len(h) - len(m)
    if short > 0:
        h += list(hits[len(h): len(h) + short])
        short = n - len(h) - len(m)
        m += list(misses[len(m): len(m) + short])
    return h + m
