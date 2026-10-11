"""Runtime sandbox (S2): the pipeline guard, pure and at the store boundary (`GuardedReader`)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from munchhausen.domain import pipeline_guard as guard
from munchhausen.domain.pipeline_guard import PipelineRefused
from tests.test_forward import FakeDB

WORLD = {"customers", "accounts", "transactions", "customers__D-1"}

ADVERSARIAL: list[tuple[str, list[dict[str, Any]]]] = [
    ("out", [{"$match": {}}, {"$out": "customers"}]),
    ("merge", [{"$merge": {"into": "decisions"}}]),
    ("merge into another db", [{"$merge": {"into": {"db": "munchhausen", "coll": "decisions"}}}]),
    ("where", [{"$match": {"$where": "this.st == 2"}}]),
    ("function", [{"$addFields": {"x": {"$function": {"body": "function(){}", "args": [], "lang": "js"}}}}]),
    ("accumulator", [{"$group": {"_id": None, "x": {"$accumulator": {"init": "function(){}"}}}}]),
    ("currentOp", [{"$currentOp": {}}]),
    ("listSessions", [{"$listSessions": {}}]),
    ("collStats", [{"$collStats": {"count": {}}}]),
    ("indexStats", [{"$indexStats": {}}]),
    ("planCacheStats", [{"$planCacheStats": {}}]),
    ("documents", [{"$documents": [{"a": 1}]}]),
    ("unknown stage", [{"$search": {"text": {"query": "x", "path": "y"}}}]),
    ("lookup into truth", [{"$lookup": {"from": "world_truth", "localField": "a", "foreignField": "b", "as": "g"}}]),
    ("lookup into the store", [{"$lookup": {"from": "decisions", "pipeline": [], "as": "d"}}]),
    ("lookup cross-db", [{"$lookup": {"from": {"db": "truth", "coll": "world_truth"}, "pipeline": [], "as": "g"}}]),
    ("graphLookup out", [{"$graphLookup": {"from": "episodes", "startWith": "$a", "connectFromField": "a",
                                           "connectToField": "b", "as": "g"}}]),
    ("unionWith string", [{"$unionWith": "observations"}]),
    ("unionWith coll", [{"$unionWith": {"coll": "fires", "pipeline": []}}]),
    ("nested lookup", [{"$lookup": {"from": "accounts", "as": "a", "pipeline": [
        {"$lookup": {"from": "world_truth", "pipeline": [], "as": "g"}}]}}]),
    ("facet hides out", [{"$facet": {"a": [{"$count": "n"}], "b": [{"$out": "x"}]}}]),
    ("facet hides where", [{"$facet": {"a": [{"$match": {"$where": "1"}}]}}]),
    ("lookup sub-pipeline where", [{"$lookup": {"from": "accounts", "as": "a",
                                                "pipeline": [{"$match": {"$where": "1"}}]}}]),
    ("not a list", {"$match": {}}),  # type: ignore[list-item]
    ("two operators in one stage", [{"$match": {}, "$limit": 1}]),
]

LEGIT: list[list[dict[str, Any]]] = [
    [{"$match": {"st": {"$in": [2, 7]}}}, {"$count": "n"}],
    [{"$unwind": "$transactions"}, {"$group": {"_id": "$transactions.symbol", "n": {"$sum": 1}}},
     {"$sort": {"n": -1}}, {"$limit": 5}],
    [{"$lookup": {"from": "accounts", "localField": "accounts", "foreignField": "account_id", "as": "acc"}},
     {"$project": {"n": {"$size": "$acc"}}}],
    [{"$unionWith": {"coll": "customers__D-1", "pipeline": [{"$match": {}}]}}, {"$count": "n"}],
    [{"$facet": {"a": [{"$count": "n"}], "b": [{"$group": {"_id": None, "s": {"$sum": {"$toDouble": "$total"}}}}]}}],
    [{"$setWindowFields": {"sortBy": {"date": 1}, "output": {"c": {"$sum": 1, "window": {"documents": [-1, 0]}}}}}],
]


@pytest.mark.parametrize(("name", "pipeline"), ADVERSARIAL, ids=[n for n, _ in ADVERSARIAL])
def test_adversarial_pipelines_are_refused(name: str, pipeline: list[dict[str, Any]]) -> None:
    with pytest.raises(PipelineRefused):
        guard.check(pipeline, targets=WORLD)


@pytest.mark.parametrize("pipeline", LEGIT)
def test_legitimate_pipelines_pass(pipeline: list[dict[str, Any]]) -> None:
    guard.check(pipeline, targets=WORLD)


def test_lookup_targets_reach_every_depth() -> None:
    p = [{"$lookup": {"from": "accounts", "as": "a", "pipeline": [{"$unionWith": "transactions"}]}},
         {"$facet": {"x": [{"$graphLookup": {"from": "customers", "startWith": "$a", "connectFromField": "a",
                                             "connectToField": "b", "as": "g"}}]}}]
    assert guard.lookup_targets(p) == {"accounts", "transactions", "customers"}


def _reader(rows: int = 3, cap: int = 10):  # noqa: ANN202
    from munchhausen.store.atlas import GuardedReader

    db = FakeDB({"customers": [{"i": i} for i in range(rows)], "accounts": []})
    return db, GuardedReader(db, row_cap=cap, max_time_ms=1000)  # type: ignore[arg-type]


def test_the_store_boundary_refuses_before_the_driver_sees_the_pipeline() -> None:
    db, reader = _reader()
    with pytest.raises(PipelineRefused):
        asyncio.run(reader.aggregate("customers", [{"$merge": {"into": "x"}}], max_time_ms=100))
    assert db.colls["customers"].pipelines == []


def test_the_store_boundary_caps_rows_and_rereads_names_for_new_views() -> None:
    db, reader = _reader(rows=50, cap=10)
    with pytest.raises(PipelineRefused, match="row cap"):
        asyncio.run(reader.aggregate("customers", [{"$match": {}}], max_time_ms=100))
    assert db.colls["customers"].pipelines[-1][-1] == {"$limit": 11}
    db2, reader2 = _reader(rows=3)
    asyncio.run(reader2.aggregate("customers", [{"$match": {}}], max_time_ms=100))   # caches the names
    db2.colls["customers__D-9"] = db2.colls["customers"]                                # a floor view admitted
    rows = asyncio.run(reader2.aggregate("customers", [{"$unionWith": "customers__D-9"}], max_time_ms=100))
    assert len(rows) == 3


def test_execute_maps_a_refusal_to_an_irreducible_error() -> None:
    from munchhausen.agent.execute import ExecutionError, execute
    from munchhausen.domain.episode import Proposal

    _, reader = _reader()
    p = Proposal(collection="customers", pipeline=[{"$out": "customers"}], answer_path="0.n", confidence=0.5,
                 rationale="")
    with pytest.raises(ExecutionError) as e:
        asyncio.run(execute(p, {}, reader, max_time_ms=100))
    assert isinstance(e.value.__cause__, PipelineRefused)


def test_system_collections_are_never_lookup_targets() -> None:
    db, reader = _reader()
    db.colls["system.views"] = db.colls["customers"]
    with pytest.raises(PipelineRefused, match="system.views"):
        asyncio.run(reader.aggregate("customers", [{"$unionWith": "system.views"}], max_time_ms=100))
