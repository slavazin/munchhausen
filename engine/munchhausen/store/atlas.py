"""`AtlasStore`: the Store port over MongoDB Atlas."""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Sequence
from typing import Any, Self

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure

from munchhausen.config import Settings
from munchhausen.domain import pipeline_guard as guard
from munchhausen.domain.common import Pipeline, emb_key
from munchhausen.store import setup as _setup
from munchhausen.store.client import AtlasClients
from munchhausen.store.decisions import AtlasDecisions
from munchhausen.store.repositories import repositories

Doc = dict[str, Any]


class AtlasReader:
    """DocumentReader over one database."""

    def __init__(self, db: AsyncDatabase[Doc]) -> None:
        self._db = db

    async def find(self, collection: str, filter: Doc | None = None, projection: Doc | None = None,
                   limit: int = 0) -> list[Doc]:
        return await self._db[collection].find(filter or {}, projection, limit=limit).to_list()

    async def aggregate(self, collection: str, pipeline: Pipeline, *, max_time_ms: int) -> list[Doc]:
        return await (await self._db[collection].aggregate(pipeline, maxTimeMS=max_time_ms)).to_list()

    async def collection_names(self) -> list[str]:
        return sorted(await self._db.list_collection_names())


class AtlasWorldWriter(AtlasReader):
    async def replace_collection(self, collection: str, docs: Sequence[Doc]) -> int:
        await self._db.drop_collection(collection)
        if not docs:
            return 0
        res = await self._db[collection].insert_many(list(docs), ordered=False)
        return len(res.inserted_ids)

    async def create_view(self, name: str, source: str, pipeline: Pipeline) -> None:
        if name in await self._db.list_collection_names():
            return
        await self._db.create_collection(name, viewOn=source, pipeline=pipeline)

    async def drop_view(self, name: str) -> None:
        await self._db.drop_collection(name)


class GuardedReader(AtlasReader):
    """The `world` database as the executor role, behind the runtime sandbox (`domain/pipeline_guard.py`).

    Every `aggregate` and `find` against `world` passes here — the proposer's execute, the nominator's world
    tool, the authority's gold reads — so no caller can skip the guard. A refusal raises `PipelineRefused`.
    `$lookup`/`$graphLookup`/`$unionWith` targets are checked against the world's collection and view names,
    re-read once when a pipeline names one not yet seen (a floor view admitted since the last read)."""

    def __init__(self, db: AsyncDatabase[Doc], *, row_cap: int, max_time_ms: int) -> None:
        super().__init__(db)
        self._row_cap, self._max_time_ms = row_cap, max_time_ms
        self._names: frozenset[str] | None = None

    async def _targets(self, wanted: set[str]) -> frozenset[str]:
        if self._names is None or not wanted <= self._names:
            self._names = frozenset(n for n in await self._db.list_collection_names()
                                    if not n.startswith("system."))   # view definitions are not data
        return self._names

    async def aggregate(self, collection: str, pipeline: Pipeline, *, max_time_ms: int) -> list[Doc]:
        guard.check(pipeline, targets=await self._targets(guard.lookup_targets(pipeline)))
        rows = await super().aggregate(collection, guard.capped(pipeline, self._row_cap),
                                       max_time_ms=min(max_time_ms, self._max_time_ms))
        guard.check_rows(len(rows), self._row_cap)
        return rows

    async def find(self, collection: str, filter: Doc | None = None, projection: Doc | None = None,
                   limit: int = 0) -> list[Doc]:
        guard.check_filter(filter)
        guard.check_filter(projection)        # projections take expressions too ($function in $project)
        lim = self._row_cap + 1 if limit <= 0 else min(limit, self._row_cap + 1)
        rows = await self._db[collection].find(filter or {}, projection, limit=lim,
                                               max_time_ms=self._max_time_ms).to_list()
        guard.check_rows(len(rows), self._row_cap)
        return rows


async def role_reach(settings: Settings) -> dict[str, Any]:
    """Which databases each role's connection can list (presence only: names and booleans, never a URI).
    `isolation` is `roles` when the three roles have their own, distinct URIs; otherwise `convention`."""
    roles = ("learner", "evaluator", "executor")
    own = {r: getattr(settings, f"mongodb_uri_{r}") is not None for r in roles}
    distinct = len({settings.uri_for(r) for r in roles}) == len(roles)
    dbs = {"store": settings.store_db, "world": settings.world_db, "truth": settings.truth_db,
           "source": settings.source_db}
    reach: dict[str, dict[str, bool]] = {}
    for r in roles:
        client: AsyncMongoClient[Doc] = AsyncMongoClient(settings.uri_for(r), appname=f"munchhausen-probe-{r}")
        try:
            reach[r] = {}
            for label, name in dbs.items():
                try:
                    await client[name].list_collection_names()
                    reach[r][label] = True
                except OperationFailure:
                    reach[r][label] = False
        finally:
            await client.close()
    return {"isolation": "roles" if all(own.values()) and distinct else "convention",
            "own_uri": own, "reach": reach}


# What each role must and must not be able to do (SPEC § 20.2). `verify_roles` probes each cell live.
ROLE_EXPECTATIONS: dict[str, dict[str, bool]] = {
    "learner":   {"read_store": True,  "write_store": True,  "read_world": True,  "write_world": False,
                  "view_world": True,  "read_truth": False},
    "executor":  {"read_store": False, "write_store": False, "read_world": True,  "write_world": False,
                  "view_world": False, "read_truth": False},
    "evaluator": {"read_store": False, "write_store": False, "read_world": True,  "write_world": False,
                  "view_world": False, "read_truth": True},
}
PROBE = "_role_probe"   # probe collection/view name; a permitted write is undone at once


def _probe_calls(c: AsyncMongoClient[Doc], settings: Settings, role: str) -> dict[str, Any]:
    store, world, truth = c[settings.store_db], c[settings.world_db], c[settings.truth_db]
    return {
        "read_store": lambda: store[PROBE].find_one({}),
        "write_store": lambda: store[PROBE].insert_one({"_id": f"probe-{role}"}),
        "read_world": lambda: world[PROBE].find_one({}),
        "write_world": lambda: world[PROBE].insert_one({"_id": f"probe-{role}"}),
        "view_world": lambda: world.create_collection(f"{PROBE}_view_{role}", viewOn=PROBE, pipeline=[]),
        "read_truth": lambda: truth[PROBE].find_one({}),
    }


async def verify_roles(settings: Settings) -> dict[str, Any]:
    """Probe every (role, capability) cell against Atlas and compare with `ROLE_EXPECTATIONS`.
    Reads are `find_one`; writes insert one probe document (or create one probe view) and remove it at
    once, through the admin connection if the role itself cannot. Returns presence only, never a URI."""
    admin: AsyncMongoClient[Doc] = AsyncMongoClient(settings.uri_for("admin"), appname="munchhausen-probe-admin")
    out: dict[str, Any] = {}
    try:
        for role, expect in ROLE_EXPECTATIONS.items():
            c: AsyncMongoClient[Doc] = AsyncMongoClient(settings.uri_for(role), appname=f"munchhausen-probe-{role}")
            probes = _probe_calls(c, settings, role)
            cells: dict[str, Any] = {}
            try:
                for cap, call in probes.items():
                    try:
                        await call()
                        got = True
                    except OperationFailure:
                        got = False
                    cells[cap] = {"allowed": got, "expected": expect[cap], "ok": got == expect[cap]}
            finally:
                await c.close()
            for db in (settings.store_db, settings.world_db):        # undo any permitted probe write
                await admin[db][PROBE].delete_many({"_id": f"probe-{role}"})
            if f"{PROBE}_view_{role}" in await admin[settings.world_db].list_collection_names():
                await admin[settings.world_db].drop_collection(f"{PROBE}_view_{role}")
            out[role] = cells
        for db in (settings.store_db, settings.world_db):
            if await admin[db][PROBE].count_documents({}) == 0:
                await admin[db].drop_collection(PROBE)
    finally:
        await admin.close()
    distinct = len({settings.uri_for(r) for r in (*ROLE_EXPECTATIONS, "admin")}) == len(ROLE_EXPECTATIONS) + 1
    enforced = distinct and all(cell["ok"] for cells in out.values() for cell in cells.values())
    return {"isolation": "roles" if enforced else "convention", "distinct_uris": distinct, "cells": out}


def open_truth(settings: Settings, clients: AtlasClients) -> AtlasReader:
    """The `truth` database as the evaluator role. Called by the composition root only."""
    return AtlasReader(clients.truth_db())


class AtlasStore:
    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(settings)

    def __init__(self, settings: Settings, clients: AtlasClients | None = None) -> None:
        self._s = settings
        self.clients = clients or AtlasClients(settings)
        db = self.clients.store_db()
        self._db = db
        self.decisions = AtlasDecisions(db)
        for name, repo in repositories(db, settings.lease_ttl_s, settings.seed_lens_weights()).items():
            setattr(self, name, repo)
        self.terms.configure_search(limit=settings.terms_search_limit)

    def world_evaluation(self) -> AtlasReader:
        """S2: `world` for the evaluation side (gold, the authority): their reads are pack code, not
        model-written input, so they skip the sandbox and its row cap. Composition root only."""
        return AtlasReader(self.clients.evaluation_world_db())

    def world(self) -> AtlasReader:
        """`world` as the executor role, behind the runtime sandbox (S2: `GuardedReader`)."""
        return GuardedReader(self.clients.world_db(write=False), row_cap=self._s.pipeline_row_cap,
                             max_time_ms=self._s.pipeline_max_time_ms)

    def world_writer(self) -> AtlasWorldWriter:
        """The learner's handle on `world`: floor views only (its role cannot write data)."""
        return AtlasWorldWriter(self.clients.world_db(write=True))

    def world_builder(self) -> AtlasWorldWriter:
        """The offline build's handle on `world` (admin role): `build-world` only."""
        return AtlasWorldWriter(self.clients.world_build_db())

    def source(self) -> AtlasReader:
        return AtlasReader(self.clients.source_db())

    async def setup(self) -> dict[str, Any]:
        return await _setup.setup(self.clients.admin_store_db(), self._s)

    async def ping(self) -> Doc:
        return await self.clients.client("learner").admin.command("ping")

    async def capabilities(self) -> dict[str, Any]:
        admin = self.clients.client("learner").admin
        build = await admin.command("buildInfo")
        hello = await admin.command("hello")
        major, minor = (int(x) for x in build["version"].split(".")[:2])
        present: list[str] = []
        for coll in ("decisions", "observations", "terms", "episodes"):
            with contextlib.suppress(OperationFailure):
                present += [ix["name"] async for ix in await self._db[coll].list_search_indexes()]
        return {
            "server_version": build["version"],
            "rank_fusion": (major, minor) >= (8, 0),
            "score_fusion": (major, minor) >= (8, 2),
            "transactions": "setName" in hello or hello.get("msg") == "isdbgrid",
            "change_streams": "setName" in hello or hello.get("msg") == "isdbgrid",
            "vector_search": None,                 # verified by creating decisions_vec (M0)
            "search_indexes": sorted(present),
            "search_indexes_left": max(0, self._s.search_index_cap - len(present)),
            "auto_embed": None,                    # verify at kickoff (SPEC § 20.2)
            "agent_engine": None,                  # verify at kickoff (SPEC § 20.2)
        }

    async def watch(self, collection: str, *, resume_token: Doc | None = None) -> AsyncIterator[Doc]:
        async with await self._db[collection].watch(resume_after=resume_token,
                                                    full_document="updateLookup") as stream:
            async for change in stream:
                yield change

    async def vector_search(self, collection: str, embedder_id: str, vector: Sequence[float], k: int,
                            filter: Doc, *, exact: bool = False) -> list[tuple[str, float]]:
        stage: Doc = {"index": f"{collection}_vec", "path": f"emb.{emb_key(embedder_id)}",
                      "queryVector": list(vector), "limit": k, "filter": filter}
        if exact:
            stage["exact"] = True
        else:
            stage["numCandidates"] = max(10 * k, 100)
        pipeline = [{"$vectorSearch": stage}, {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}}]
        rows = await (await self._db[collection].aggregate(pipeline)).to_list()
        return [(r["_id"], float(r["score"])) for r in rows]

    async def close(self) -> None:
        await self.clients.close()
