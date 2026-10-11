"""`AtlasStore`: the Store port over MongoDB Atlas."""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Sequence
from typing import Any, Self

from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure

from munchhausen.config import Settings
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

    def world(self) -> AtlasReader:
        return AtlasReader(self.clients.world_db(write=False))

    def world_writer(self) -> AtlasWorldWriter:
        return AtlasWorldWriter(self.clients.world_db(write=True))

    def source(self) -> AtlasReader:
        return AtlasReader(self.clients.source_db())

    async def setup(self) -> dict[str, Any]:
        return await _setup.setup(self._db, self._s)

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
