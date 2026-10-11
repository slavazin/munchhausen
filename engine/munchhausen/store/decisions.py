"""The decision store and its only write path (SPEC § 10.2 "Frozen at admission").

Exposes `admit`, `amend`, `supersede`, `converge`, `moot` and `retire` — plus the computed
`refresh_evidence_state`. No other module issues an update against `decisions`; an architecture test
asserts it. Lifecycle transitions are validated in the domain (`Lifecycle`), committed here.

View DDL (create/drop of floor views in `world`) is not transactional, so the application service
(`learn/lifecycle.py`) creates a successor's view before `admit` and drops predecessors' views after it.
"""

from __future__ import annotations

from typing import Any

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from munchhausen.domain.admission import Admission
from munchhausen.domain.common import Disposer, FireDisposition, FireRole, LifecycleStatus
from munchhausen.domain.decision import Amendment, Decision, LifecycleError, evidence_state
from munchhausen.domain.draft import DraftStatus
from munchhausen.domain.question import QuestionKeys
from munchhausen.store.codec import from_doc, to_doc
from munchhausen.store.names import C


class AtlasDecisions:
    def __init__(self, db: AsyncDatabase[dict[str, Any]]) -> None:
        self._db = db
        self._c = db[C.DECISIONS.value]

    # --- reads -------------------------------------------------------------------------------------

    async def get(self, decision_id: str) -> Decision | None:
        return from_doc(Decision, await self._c.find_one({"_id": decision_id}))

    async def admitted(self, run_id: str, arm: str) -> list[Decision]:
        cur = self._c.find({"run_id": run_id, "arm": arm, "lifecycle.status": LifecycleStatus.ADMITTED.value})
        return [Decision.model_validate(d) async for d in cur]

    async def match_hooks(self, run_id: str, arm: str, keys: QuestionKeys) -> list[Decision]:
        """Index-backed prefilter in Atlas (§ 20.3), then the domain's `HookLatch.matches` as the one
        definition of a match (persona scope and `not_this`)."""
        query = {
            "run_id": run_id, "arm": arm, "lifecycle.status": LifecycleStatus.ADMITTED.value,
            "$or": [{"latches.fires_when.terms": {"$in": sorted(keys.terms)}},
                    {"latches.fires_when.collections": {"$in": sorted(keys.collections)}}],
        }
        out = []
        async for d in self._c.find(query):
            dec = Decision.model_validate(d)
            if dec.hook.matches(keys):
                out.append(dec)
        return out

    async def lineage(self, decision_id: str) -> list[Decision]:
        """`$graphLookup` over `latches.edges` (SPEC § 17 pane 5)."""
        pipeline = [
            {"$match": {"_id": decision_id}},
            # `$latches.edges` over an array of latch subdocuments is an array of arrays; flatten it first
            {"$graphLookup": {"from": C.DECISIONS.value,
                              "startWith": {"$reduce": {"input": "$latches.edges", "initialValue": [],
                                                        "in": {"$concatArrays": ["$$value", "$$this"]}}},
                              "connectFromField": "latches.edges", "connectToField": "_id", "as": "chain"}},
        ]
        docs = await (await self._c.aggregate(pipeline)).to_list()
        if not docs:
            return []
        root = docs[0]
        chain = root.pop("chain", [])
        return [Decision.model_validate(d) for d in [root, *chain]]

    # --- the write path ----------------------------------------------------------------------------

    async def admit(self, plan: Admission) -> None:
        """Atomic (§ 20.2): insert successor, flip predecessors, dispose their open fires,
        rewire tool access, close the draft. Idempotent: re-admitting the same draft is a no-op."""
        async with self._db.client.start_session() as s:
            await s.with_transaction(lambda sess: self._admit_txn(sess, plan))

    async def supersede(self, plan: Admission) -> None:
        if not any(f.lifecycle.status is LifecycleStatus.SUPERSEDED for f in plan.flips):
            raise LifecycleError("a supersede plan must flip its predecessor to superseded")
        await self.admit(plan)

    async def converge(self, plan: Admission) -> None:
        if not any(f.lifecycle.status is LifecycleStatus.CONVERGED for f in plan.flips):
            raise LifecycleError("a converge plan must flip at least one decision to converged")
        await self.admit(plan)

    async def amend(self, decision_id: str, amendment: Amendment) -> None:
        await self._c.update_one({"_id": decision_id}, {"$push": {"amendments": to_doc(amendment)}})

    async def moot(self, decision_id: str, at_idx: int, reason: str) -> None:
        await self._terminal(decision_id, lambda lc: lc.moot(at_idx, reason))

    async def retire(self, decision_id: str, at_idx: int, reason: str) -> None:
        await self._terminal(decision_id, lambda lc: lc.retire(at_idx, reason))

    async def refresh_evidence_state(self, decision_id: str) -> None:
        cur = self._db[C.FIRES.value].find({"decision_id": decision_id, "disposition": FireDisposition.OPEN.value},
                                           {"role": 1, "disposition": 1})
        roles = [(FireRole(f["role"]), FireDisposition(f["disposition"])) async for f in cur]
        await self._c.update_one({"_id": decision_id}, {"$set": {"evidence_state": evidence_state(roles).value}})

    # --- `why` (read-only) -------------------------------------------------------------------------

    async def trail(self, decision_id: str) -> dict[str, Any] | None:
        """One aggregation: `$graphLookup` over `latches.edges` (predecessors), a reverse `$lookup` for
        successors, and `$lookup`s to the warrant's observations and episodes, the backtest and the fires."""
        no_emb = [{"$project": {"emb": 0}}]
        pipeline = [
            {"$match": {"_id": decision_id}},
            # `$latches.edges` over an array of latch subdocuments is an array of arrays; flatten it first
            {"$graphLookup": {"from": C.DECISIONS.value,
                              "startWith": {"$reduce": {"input": "$latches.edges", "initialValue": [],
                                                        "in": {"$concatArrays": ["$$value", "$$this"]}}},
                              "connectFromField": "latches.edges", "connectToField": "_id",
                              "as": "lineage", "depthField": "depth"}},
            {"$lookup": {"from": C.DECISIONS.value, "localField": "_id", "foreignField": "latches.edges",
                         "pipeline": no_emb, "as": "successors"}},
            {"$lookup": {"from": C.OBSERVATIONS.value, "localField": "warrant.source_observation_ids",
                         "foreignField": "_id", "pipeline": no_emb, "as": "observations"}},
            {"$lookup": {"from": C.EPISODES.value, "localField": "warrant.source_episode_ids",
                         "foreignField": "_id", "as": "episodes",
                         "pipeline": [{"$project": {"idx": 1, "text": 1, "template": 1, "persona": 1, "answer": 1,
                                                    "figure": 1, "phrasing": 1, "confirmed_figure": 1}}]}},
            {"$lookup": {"from": C.BACKTESTS.value, "localField": "warrant.backtest_id", "foreignField": "_id",
                         "as": "backtest"}},
            {"$lookup": {"from": C.FIRES.value, "localField": "_id", "foreignField": "decision_id", "as": "fires"}},
            {"$lookup": {"from": C.TOOL_ACCESS.value, "localField": "_id", "foreignField": "decision_id",
                         "as": "tool_access"}},
            {"$project": {"emb": 0, "lineage.emb": 0}},
        ]
        docs = await (await self._c.aggregate(pipeline)).to_list()
        return docs[0] if docs else None

    async def ids_with_term(self, run_id: str, term: str, arm: str | None = None) -> list[str]:
        query: dict[str, Any] = {"run_id": run_id, "latches.fires_when.terms": term}
        if arm is not None:
            query["arm"] = arm
        cur = self._c.find(query, {"_id": 1, "lifecycle.at_idx": 1}).sort("lifecycle.at_idx", 1)
        return [d["_id"] async for d in cur]

    # --- internals ---------------------------------------------------------------------------------

    async def _admit_txn(self, s: AsyncClientSession, plan: Admission) -> None:
        d = plan.decision
        if await self._c.find_one({"_id": d.id}, {"_id": 1}, session=s):
            return
        await self._c.insert_one(to_doc(d), session=s)
        flipped = []
        for f in plan.flips:
            res = await self._c.update_one(
                {"_id": f.decision_id, "lifecycle.status": LifecycleStatus.ADMITTED.value},
                {"$set": {"lifecycle": to_doc(f.lifecycle)}}, session=s)
            if res.matched_count != 1:
                raise LifecycleError(f"predecessor {f.decision_id} is not admitted")
            flipped.append(f.decision_id)
        if flipped:
            await self._db[C.FIRES.value].update_many(
                {"decision_id": {"$in": flipped}, "disposition": FireDisposition.OPEN.value},
                {"$set": {"disposition": FireDisposition.APPLIED.value, "disposer": Disposer.LIFECYCLE.value}},
                session=s)
        ta = self._db[C.TOOL_ACCESS.value]
        if plan.restore_views_of:
            await ta.delete_many({"decision_id": {"$in": list(plan.restore_views_of)}}, session=s)
        if plan.rewire:
            r = plan.rewire
            await ta.replace_one({"run_id": r.run_id, "arm": r.arm, "logical": r.logical}, to_doc(r),
                                 upsert=True, session=s)
        await self._db[C.DRAFTS.value].update_one(
            {"_id": plan.draft_id}, {"$set": {"status": DraftStatus.ADMITTED.value}}, session=s)

    async def _terminal(self, decision_id: str, transition: Any) -> None:
        async with self._db.client.start_session() as s:
            async def txn(sess: AsyncClientSession) -> None:
                dec = from_doc(Decision, await self._c.find_one({"_id": decision_id}, session=sess))
                if dec is None:
                    raise LifecycleError(f"unknown decision {decision_id}")
                lc = transition(dec.lifecycle)
                await self._c.update_one({"_id": decision_id, "lifecycle.status": LifecycleStatus.ADMITTED.value},
                                         {"$set": {"lifecycle": to_doc(lc)}}, session=sess)
                await self._db[C.TOOL_ACCESS.value].delete_many({"decision_id": decision_id}, session=sess)
            await s.with_transaction(txn)
