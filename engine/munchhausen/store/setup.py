"""`store.setup()` (SPEC § 13 M0): collections, validators, B-tree indexes and search indexes.

Idempotent. Search indexes are created in the order of § 20.1 and stop at the tier's cap; every skipped
index is returned so the caller writes it to `runs.capabilities`.
"""

from __future__ import annotations

import logging
from typing import Any

from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

from munchhausen.config import Settings
from munchhausen.domain.common import emb_key
from munchhausen.store.names import C
from munchhausen.store.schemas import MODELS, validator

log = logging.getLogger(__name__)

BTREE: dict[C, list[IndexModel]] = {
    C.EPISODES: [IndexModel([("run_id", ASCENDING), ("arm", ASCENDING), ("idx", ASCENDING)], unique=True),
                 IndexModel([("run_id", ASCENDING), ("arm", ASCENDING), ("consulted.decision_id", ASCENDING)])],
    C.OBSERVATIONS: [IndexModel([("run_id", ASCENDING), ("arm", ASCENDING), ("disposition", ASCENDING)])],
    C.DECISIONS: [
        IndexModel([("run_id", ASCENDING), ("arm", ASCENDING), ("lifecycle.status", ASCENDING), ("kind", ASCENDING)]),
        # hook matching runs in Atlas over multikey indexes (SPEC § 20.3)
        IndexModel([("latches.fires_when.terms", ASCENDING)]),
        IndexModel([("latches.fires_when.collections", ASCENDING)]),
        IndexModel([("latches.edges", ASCENDING)]),
    ],
    C.FIRES: [IndexModel([("decision_id", ASCENDING), ("disposition", ASCENDING)])],
    C.DRAFTS: [IndexModel([("shape_id", ASCENDING)]),
               IndexModel([("run_id", ASCENDING), ("arm", ASCENDING), ("status", ASCENDING)])],
    C.CURSORS: [IndexModel([("run_id", ASCENDING), ("arm", ASCENDING)], unique=True)],
    C.LEASES: [IndexModel([("run_id", ASCENDING), ("arm", ASCENDING), ("idx", ASCENDING)], unique=True),
               IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0)],
    C.TOOL_ACCESS: [IndexModel([("run_id", ASCENDING), ("arm", ASCENDING), ("logical", ASCENDING)], unique=True)],
    C.ROUNDS: [IndexModel([("run_id", ASCENDING), ("arm", ASCENDING), ("round", ASCENDING)], unique=True)],
    C.TERMS: [IndexModel([("term", ASCENDING)], unique=True)],
    C.LENS_WEIGHTS: [IndexModel([("version", ASCENDING)], unique=True)],
}

PRE_POST_IMAGES = (C.DECISIONS, C.TOOL_ACCESS)


def search_indexes(settings: Settings) -> list[tuple[C, SearchIndexModel]]:
    """In budget order (SPEC § 20.1)."""
    emb = f"emb.{emb_key(settings.embed_model)}"
    vec = {"type": "vector", "path": emb, "numDimensions": settings.embed_dim, "similarity": "cosine"}
    return [
        (C.DECISIONS, SearchIndexModel(name="decisions_vec", type="vectorSearch", definition={"fields": [
            vec, *({"type": "filter", "path": p} for p in ("run_id", "arm", "lifecycle.status", "kind"))]})),
        (C.OBSERVATIONS, SearchIndexModel(name="observations_vec", type="vectorSearch", definition={"fields": [
            vec, *({"type": "filter", "path": p} for p in ("run_id", "arm", "disposition"))]})),
        (C.TERMS, SearchIndexModel(name="terms_search", type="search", definition={
            "analyzer": "lucene.english",
            "mappings": {"dynamic": False, "fields": {"term": {"type": "string"}, "aliases": {"type": "string"}}},
            "synonyms": [{"name": "term_synonyms", "analyzer": "lucene.english",
                          "source": {"collection": C.TERM_SYNONYMS.value}}]})),
        (C.DECISIONS, SearchIndexModel(name="decisions_search", type="search", definition={
            "mappings": {"dynamic": False, "fields": {"title": {"type": "string"}, "payload": {"type": "string"},
                                                      "latches": {"type": "document", "dynamic": True}}}})),
        (C.EPISODES, SearchIndexModel(name="episodes_search", type="search", definition={
            "mappings": {"dynamic": False, "fields": {
                "text": {"type": "string"}, "rationale": {"type": "string"}, "phrasing": {"type": "string"},
                "arm": {"type": "token"}, "template": {"type": "token"}, "correct": {"type": "boolean"}}}})),
    ]


async def setup(db: AsyncDatabase[dict[str, Any]], settings: Settings) -> dict[str, Any]:
    existing = set(await db.list_collection_names())
    for c in C:
        if c.value in existing:
            continue
        if c is C.SPEND:
            await db.create_collection(c.value, timeseries={"timeField": "at", "metaField": "meta"})
        else:
            await db.create_collection(c.value)

    for c, model in MODELS.items():
        await db.command({"collMod": c.value, "validator": validator(model),
                          "validationLevel": "moderate", "validationAction": "warn"})
    for c in PRE_POST_IMAGES:
        await db.command({"collMod": c.value, "changeStreamPreAndPostImages": {"enabled": True}})
    for c, models in BTREE.items():
        await db[c.value].create_indexes(models)

    created, skipped = await _search_indexes(db, settings)
    return {"collections": [c.value for c in C], "search_indexes": created, "skipped_indexes": skipped}


async def _search_indexes(db: AsyncDatabase[dict[str, Any]], settings: Settings) -> tuple[list[str], list[str]]:
    present: set[str] = set()
    for c in {c for c, _ in search_indexes(settings)}:
        async for ix in await db[c.value].list_search_indexes():
            present.add(ix["name"])
    created, skipped = sorted(present), []
    for c, model in search_indexes(settings):
        name = model.document["name"]
        if name in present:
            continue
        if len(created) >= settings.search_index_cap:
            skipped.append(name)
            continue
        try:
            await db[c.value].create_search_index(model)
            created.append(name)
        except OperationFailure as e:   # the tier refused it: fall back per § 20.1
            log.warning("search index %s skipped: %s", name, e)
            skipped.append(name)
    return created, skipped
