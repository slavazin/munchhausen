"""Arm isolation (SPEC § 5): nothing an arm learns or derives from its own episodes reaches another arm.

Five arms run in one process against one database and are read as paired differences, so a record of arm
`governed` that reaches arm `ungated` contaminates the comparison that isolates the gate. Shared by design:
`world`, the question stream and V set, the authority, the seeded vocabulary, the content-addressed caches.

Offline. The repositories under test are the real Atlas ones (`store/repositories.py`, `store/decisions.py`)
over an in-memory collection that evaluates the Mongo filters they send, so a read that drops `arm` or
`run_id` shows here as a leak, not as a fake's own filtering. Every read is logged; the scope check at the
end asserts that each of `ungated`'s learner reads carried its own `(run_id, arm)`.

Arm `governed` admits a floor decision with an escaped (learned) term, writes episodes, observations, fires
and a held draft. Arm `ungated` holds one decision of its own, so its semantic and neighbour paths run.
Every negative assertion has its positive control: `governed` sees its own record through the same call.
"""

from __future__ import annotations

import asyncio
import copy
import itertools
import re
from collections.abc import Sequence
from typing import Any

import numpy as np
import pytest
from pymongo.errors import DuplicateKeyError

from munchhausen.agent.consultation import HookConsulter, SemanticConsulter
from munchhausen.agent.execute import ExecutionError, execute
from munchhausen.domain.admission import plan_admission
from munchhausen.domain.common import (
    DecisionKind,
    Disposition,
    FireRole,
    LifecycleStatus,
    emb_key,
)
from munchhausen.domain.decision import Decision, LifecycleError, Representation
from munchhausen.domain.draft import DraftStatus, Route, Verdict
from munchhausen.domain.episode import Consultation, Episode, Proposal, Residual
from munchhausen.domain.ids import decision_id
from munchhausen.domain.latches import FloorLatch, HookLatch, KeySet
from munchhausen.domain.pipeline_guard import PipelineRefused, check_scope, is_floor_view
from munchhausen.domain.question import Question
from munchhausen.domain.registers import Term
from munchhausen.impl.parties.nominator import logical_collections
from munchhausen.impl.similarity import NumpySimilarity, store_loader
from munchhausen.learn.direct import DirectWriter
from munchhausen.learn.episodic import shape_of
from munchhausen.learn.layers import L0Shape, L2Neighbours
from munchhausen.learn.lifecycle import LifecycleService
from munchhausen.learn.nominate import Nominator
from munchhausen.ports.curation import CurationContext
from munchhausen.store.decisions import AtlasDecisions
from munchhausen.store.names import view_name
from munchhausen.store.repositories import (
    AtlasBacktests,
    AtlasDrafts,
    AtlasEpisodes,
    AtlasFires,
    AtlasObservations,
    AtlasTerms,
    AtlasToolAccess,
)
from tests.test_adjudication_fakes import RUN, TERM, draft, episode, fire, observation

GOV, UNG = "governed", "ungated"
LEARNED = "churned accounts"                  # the escaped term governed's draft brings: other(<term>): gloss
QUESTION = Question(id="q-iso", text=f"How many {TERM} were {LEARNED} last quarter?", template="t_iso",
                    persona="omar", collections=("customers",))
REP_ID = "iso-rep"
VEC = [1.0, 0.0, 0.0]                         # every text embeds here: governed's records are the nearest


def run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- an in-memory collection that evaluates the filters the Atlas repositories send ----------------------


def _values(doc: Any, path: str) -> tuple[list[Any], bool]:
    cur = [doc]
    for part in path.split("."):
        nxt: list[Any] = []
        for c in cur:
            if isinstance(c, dict) and part in c:
                nxt.append(c[part])
            elif isinstance(c, list):
                nxt += [el[part] for el in c if isinstance(el, dict) and part in el]
        cur = nxt
    out: list[Any] = []
    for v in cur:
        out.append(v)
        if isinstance(v, list):
            out += v
    return out, bool(cur)


def _eq(v: Any, a: Any) -> bool:
    return bool(isinstance(v, str) and a.search(v)) if isinstance(a, re.Pattern) else v == a


def _cmp(vals: list[Any], arg: Any, op: Any) -> bool:
    for v in vals:
        try:
            if v is not None and op(v, arg):
                return True
        except TypeError:
            continue
    return False


def _field(vals: list[Any], exists: bool, cond: Any) -> bool:  # noqa: C901 - one branch per operator
    if isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond):
        for op, arg in cond.items():
            if op == "$exists":
                ok = exists == bool(arg)
            elif op == "$in":
                ok = any(_eq(v, a) for v in vals for a in arg) or (None in arg and not exists)
            elif op == "$nin":
                ok = not any(_eq(v, a) for v in vals for a in arg)
            elif op == "$ne":
                ok = not any(_eq(v, arg) for v in vals)
            elif op == "$all":
                ok = all(any(_eq(v, a) for v in vals) for a in arg)
            elif op == "$gt":
                ok = _cmp(vals, arg, lambda x, y: x > y)
            elif op == "$gte":
                ok = _cmp(vals, arg, lambda x, y: x >= y)
            elif op == "$lt":
                ok = _cmp(vals, arg, lambda x, y: x < y)
            elif op == "$lte":
                ok = _cmp(vals, arg, lambda x, y: x <= y)
            else:
                raise NotImplementedError(f"filter operator {op}")
            if not ok:
                return False
        return True
    return any(_eq(v, cond) for v in vals) or (cond is None and not exists)


def matches(doc: dict[str, Any], f: dict[str, Any]) -> bool:
    for k, cond in f.items():
        if k == "$or":
            if not any(matches(doc, c) for c in cond):
                return False
        elif k == "$and":
            if not all(matches(doc, c) for c in cond):
                return False
        elif k == "$nor":
            if any(matches(doc, c) for c in cond):
                return False
        elif k.startswith("$"):
            raise NotImplementedError(f"top-level operator {k}")
        elif not _field(*_values(doc, k), cond):
            return False
    return True


def _get(doc: Any, path: str) -> Any:
    vals, exists = _values(doc, path)
    return vals[0] if exists else None


def _expr(doc: dict[str, Any], e: Any) -> Any:
    if isinstance(e, str) and e.startswith("$"):
        return _get(doc, e[1:])
    if isinstance(e, dict) and "$cond" in e:
        c, a, b = e["$cond"]
        return _expr(doc, a) if _expr(doc, c) else _expr(doc, b)
    return e


def _project(doc: dict[str, Any], proj: dict[str, Any] | None) -> dict[str, Any]:
    if not proj:
        return doc
    if any(v for v in proj.values()):
        keep = {k.split(".")[0] for k, v in proj.items() if v} | {"_id"}
        return {k: v for k, v in doc.items() if k in keep}
    return {k: v for k, v in doc.items() if k not in proj}


class Cursor:
    def __init__(self, docs: Sequence[dict[str, Any]]) -> None:
        self._docs = [copy.deepcopy(d) for d in docs]

    def sort(self, key: Any, direction: int | None = None) -> Cursor:
        keys = key if isinstance(key, list) else [(key, 1 if direction is None else direction)]
        for k, d in reversed(keys):
            if k != "$natural":
                self._docs.sort(key=lambda doc, k=k: (_get(doc, k) is not None, _get(doc, k)), reverse=d == -1)
        return self

    def skip(self, n: int) -> Cursor:
        self._docs = self._docs[n:]
        return self

    def limit(self, n: int) -> Cursor:
        if n:
            self._docs = self._docs[:n]
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        return list(self._docs)

    def __aiter__(self) -> Cursor:
        self._it = iter(self._docs)
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration from None


class Result:
    def __init__(self, matched: int) -> None:
        self.matched_count = matched


class Coll:
    _ids = itertools.count()

    def __init__(self, db: DB, name: str) -> None:
        self.db, self.name, self.docs = db, name, {}

    @property
    def database(self) -> DB:
        return self.db

    def _log(self, op: str, f: Any) -> None:
        self.db.log.append((self.name, op, copy.deepcopy(f)))

    def _find(self, f: dict[str, Any] | None) -> list[dict[str, Any]]:
        return [d for d in self.docs.values() if matches(d, f or {})]

    def find(self, filter: dict[str, Any] | None = None, projection: dict[str, Any] | None = None,
             **_: Any) -> Cursor:
        self._log("find", filter or {})
        return Cursor([_project(d, projection) for d in self._find(filter)])

    async def find_one(self, filter: dict[str, Any] | None = None, projection: dict[str, Any] | None = None,
                       **_: Any) -> dict[str, Any] | None:
        self._log("find_one", filter or {})
        rows = self._find(filter)
        return copy.deepcopy(_project(rows[0], projection)) if rows else None

    async def count_documents(self, filter: dict[str, Any], limit: int = 0, **_: Any) -> int:
        self._log("count", filter)
        n = len(self._find(filter))
        return min(n, limit) if limit else n

    async def distinct(self, key: str, filter: dict[str, Any] | None = None) -> list[Any]:
        self._log("distinct", filter or {})
        return sorted({_get(d, key) for d in self._find(filter)})

    async def aggregate(self, pipeline: list[dict[str, Any]], **_: Any) -> Cursor:
        self._log("aggregate", pipeline)
        return Cursor(self._run(list(self.docs.values()), pipeline))

    def _run(self, docs: list[dict[str, Any]], pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for stage in pipeline:
            (op, spec), = stage.items()
            if op == "$match":
                docs = [d for d in docs if matches(d, spec)]
            elif op == "$search":          # candidate retrieval: every row is a candidate; callers post-filter
                docs = list(docs)
            elif op == "$facet":
                docs = [{k: self._run(docs, sub) for k, sub in spec.items()}]
            elif op == "$group":
                if spec["_id"] is not None:
                    raise NotImplementedError("$group by key")
                docs = [{"_id": None, **{k: sum(1 if acc["$sum"] == 1 else _expr(d, acc["$sum"]) for d in docs)
                                         for k, acc in spec.items() if k != "_id"}}] if docs else []
            elif op in ("$sample", "$limit"):
                docs = docs[: spec["size"] if op == "$sample" else spec]
            elif op == "$sort":
                c = Cursor(docs).sort(list(spec.items()))
                docs = c._docs
            elif op == "$project":
                docs = [_project(d, spec) for d in docs]
            else:
                raise NotImplementedError(f"stage {op}")
        return docs

    async def insert_one(self, doc: dict[str, Any], **_: Any) -> None:
        doc = copy.deepcopy(doc)
        doc.setdefault("_id", f"{self.name}-{next(self._ids)}")
        if doc["_id"] in self.docs:
            raise DuplicateKeyError(f"dup {doc['_id']}")
        self.docs[doc["_id"]] = doc

    async def replace_one(self, filter: dict[str, Any], doc: dict[str, Any], upsert: bool = False,
                          **_: Any) -> Result:
        rows = self._find(filter)
        if rows:
            new = {**copy.deepcopy(doc), "_id": rows[0]["_id"]}
            self.docs[new["_id"]] = new
            return Result(1)
        if upsert:
            await self.insert_one(doc)
        return Result(0)

    async def update_one(self, filter: dict[str, Any], update: dict[str, Any], upsert: bool = False,
                         **_: Any) -> Result:
        rows = self._find(filter)
        if not rows:
            if upsert:
                new = {k: v for k, v in filter.items() if not k.startswith("$") and not isinstance(v, dict)}
                new.update(copy.deepcopy(update.get("$setOnInsert", {})))
                _apply(new, update)
                await self.insert_one(new)
            return Result(0)
        _apply(rows[0], update)
        return Result(1)

    async def update_many(self, filter: dict[str, Any], update: dict[str, Any], **_: Any) -> Result:
        rows = self._find(filter)
        for d in rows:
            _apply(d, update)
        return Result(len(rows))

    async def delete_many(self, filter: dict[str, Any], **_: Any) -> None:
        for d in self._find(filter):
            del self.docs[d["_id"]]

    async def delete_one(self, filter: dict[str, Any], **_: Any) -> None:
        for d in self._find(filter)[:1]:
            del self.docs[d["_id"]]


def _apply(doc: dict[str, Any], update: dict[str, Any]) -> None:
    for op, fields in update.items():
        if op == "$setOnInsert":
            continue
        for path, value in fields.items():
            *head, last = path.split(".")
            node = doc
            for p in head:
                node = node.setdefault(p, {})
            if op == "$set":
                node[last] = copy.deepcopy(value)
            elif op == "$min":
                node[last] = value if last not in node else min(node[last], value)
            elif op == "$push":
                node.setdefault(last, []).append(copy.deepcopy(value))
            else:
                raise NotImplementedError(f"update operator {op}")


class Session:
    async def __aenter__(self) -> Session:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    async def with_transaction(self, cb: Any) -> Any:
        return await cb(self)


class Client:
    def start_session(self) -> Session:
        return Session()


class DB:
    def __init__(self) -> None:
        self.colls: dict[str, Coll] = {}
        self.log: list[tuple[str, str, Any]] = []
        self.client = Client()

    def __getitem__(self, name: str) -> Coll:
        return self.colls.setdefault(name, Coll(self, name))


# --- the world: base collections plus every arm's floor views, in one database ----------------------------


class World:
    """`world` as a reader that lists every name and answers any read: the arm scope is the caller's to hold."""

    def __init__(self) -> None:
        self.base = {"customers", "accounts", "transactions"}
        self.views: dict[str, tuple[str, list[dict[str, Any]]]] = {}
        self.reads: list[tuple[str, list[dict[str, Any]]]] = []

    async def collection_names(self) -> list[str]:
        return sorted(self.base | set(self.views))

    async def aggregate(self, collection: str, pipeline: list[dict[str, Any]], *, max_time_ms: int) -> list[dict]:
        self.reads.append((collection, pipeline))
        return [{"v": 1.0}]

    async def find(self, *a: Any, **k: Any) -> list[dict]:
        return []

    async def create_view(self, name: str, source: str, pipeline: list[dict[str, Any]]) -> None:
        self.views[name] = (source, pipeline)

    async def drop_view(self, name: str) -> None:
        self.views.pop(name, None)

    async def replace_collection(self, collection: str, docs: Sequence[dict]) -> int:
        return 0


class Rep:
    id, dim = REP_ID, 3

    async def embed(self, texts: Sequence[str], role: str) -> np.ndarray:
        return np.asarray([VEC] * len(texts), dtype=np.float32)


class NoRep:
    id, dim = "none", 0

    async def embed(self, texts: Sequence[str], role: str) -> None:
        return None


class Rerank:
    async def rerank(self, query: str, documents: Sequence[str], top_k: int | None = None) -> list[tuple[int, float]]:
        return [(i, 1.0) for i in range(len(documents))]


class Sink:
    async def publish(self, decision: Decision) -> None: ...

    async def withdraw(self, decision_id: str, reason: str) -> None: ...


class Recording:
    """Similarity wrapper: records each pre-filter it is asked for."""

    def __init__(self, inner: Any) -> None:
        self.inner, self.filters = inner, []

    async def knn(self, store: str, query: Any, k: int, filter: dict[str, Any]) -> list[tuple[str, float]]:
        self.filters.append((store, dict(filter)))
        return await self.inner.knn(store, query, k, filter)


class Leaky:
    """A backend that ignores the pre-filter and returns every id it is handed: the caller's re-check holds."""

    def __init__(self, ids: Sequence[str]) -> None:
        self.ids = list(ids)

    async def knn(self, store: str, query: Any, k: int, filter: dict[str, Any]) -> list[tuple[str, float]]:
        return [(i, 1.0) for i in self.ids]


class Store:
    def __init__(self) -> None:
        self.db = DB()
        self.episodes = AtlasEpisodes(self.db["episodes"])
        self.observations = AtlasObservations(self.db["observations"])
        self.fires = AtlasFires(self.db["fires"])
        self.drafts = AtlasDrafts(self.db["drafts"])
        self.backtests = AtlasBacktests(self.db["backtests"])
        self.tool_access = AtlasToolAccess(self.db["tool_access"])
        self.terms = AtlasTerms(self.db["terms"])
        self.terms._search_ok = False            # the in-process path; the `$search` path is checked separately
        self.decisions = AtlasDecisions(self.db)  # type: ignore[arg-type]
        self.world_ = World()

    def world(self) -> World:
        return self.world_

    def world_writer(self) -> World:
        return self.world_


# --- the scenario --------------------------------------------------------------------------------------


def _decision_draft(did: str, arm: str, sources: Sequence[Episode], *, terms: tuple[str, ...],
                    floor: FloorLatch | None = None, new_terms: tuple[str, ...] = ()) -> Any:
    d = draft(did, "Count customers by RULE status.", sources, arm=arm, floor=floor, new_terms=new_terms,
              kind=DecisionKind.FLOOR if floor is not None else DecisionKind.TAXONOMIC)
    latches = tuple(HookLatch(fires_when=KeySet(terms=terms)) if isinstance(lt, HookLatch) else lt
                    for lt in d.latches)
    return d.model_copy(update={"latches": latches})


class Scenario:
    def __init__(self) -> None:
        self.s = Store()
        self.lifecycle = LifecycleService(decisions=self.s.decisions, world=self.s.world_, sink=Sink(),
                                          tool_access=self.s.tool_access, fires=self.s.fires,
                                          episodes=self.s.episodes, retire_idle=1, retire_fires=99)

    async def build(self) -> Scenario:
        s = self.s
        await s.terms.add(Term(term=TERM, source="schema", admitted_at_idx=0, run_id=RUN))
        # governed: episodes, a floor decision with an escaped term (admitted through the real lifecycle)
        g_eps = [episode(i, f"t{i % 3}", correct=i % 2 == 0, figure=100.0 + i, arm=GOV,
                         terms=(TERM, LEARNED)) for i in range(8)]
        floor = FloorLatch(collection="customers", match={"st": {"$in": [2, 7]}})
        g_draft = _decision_draft(f"{RUN}:{GOV}:r0:a", GOV, g_eps[1::2], terms=(TERM, LEARNED), floor=floor,
                                  new_terms=(f"other({LEARNED}): accounts their holder closed",))
        self.g_id = await self._admit(g_draft)
        await s.terms.add(Term(term=LEARNED, source="nominator", admitted_at_idx=8, run_id=RUN, arm=GOV,
                               decision_id=self.g_id))
        consulted = (Consultation(decision_id=self.g_id, disposition=Disposition.APPLIED),)
        for e in g_eps:
            res = () if e.correct else (Residual(id=f"{e.id}:r", decision_id=self.g_id, answer=e.answer,
                                                 figure=e.figure, signature_match=True, attributable=True),)
            await s.episodes.put(e.model_copy(update={"consulted": consulted, "residuals": res}))
        self.g_obs = [observation(e).model_copy(update={"rep": {"embedder_id": REP_ID},
                                                         "emb": {emb_key(REP_ID): VEC}})
                      for e in g_eps if not e.correct]
        for o in self.g_obs:
            await s.observations.put(o)
        await s.fires.put(fire(self.g_id, 7))
        held = _decision_draft(f"{RUN}:{GOV}:r1:held", GOV, g_eps[1:2], terms=(TERM,))
        await s.drafts.put(held.model_copy(update={"status": DraftStatus.HELD}))
        # ungated: two hits and one decision of its own, keyed elsewhere, its vector orthogonal
        for i in range(2):
            await s.episodes.put(episode(i, "t9", correct=True, figure=5.0, arm=UNG, terms=("revenue",)))
        u_draft = _decision_draft(f"{RUN}:{UNG}:r0:u", UNG, [], terms=("revenue",))
        self.u_id = await self._admit(u_draft, vec=[0.0, 1.0, 0.0])
        s.db.log.clear()
        return self

    async def _admit(self, d: Any, vec: Sequence[float] = VEC) -> str:
        """The real admission path: plan → lifecycle (view DDL, the store transaction, tool-access rewire)."""
        did = decision_id(d.id)
        plan = plan_admission(d, at_idx=8, backtest_id="B-iso", lens_score=None,
                              view_name=view_name(d.floor.collection, did) if d.floor else None,
                              rep=Representation(embedder_id=REP_ID, text_hash="h"), emb={emb_key(REP_ID): list(vec)})
        await self.s.drafts.put(d)
        await self.lifecycle.admit(plan)
        return did


@pytest.fixture(scope="module")
def sc() -> Scenario:
    return run(Scenario().build())


def _scope(entry: Any) -> dict[str, Any]:
    """(run_id, arm) a logged read carries: the filter's top level, its `$and` members, or a first `$match`."""
    f = entry[0]["$match"] if isinstance(entry, list) and entry and "$match" in entry[0] else entry
    out = {k: f[k] for k in ("run_id", "arm") if k in f}
    for part in f.get("$and", []) if isinstance(f, dict) else []:
        out |= {k: part[k] for k in ("run_id", "arm") if k in part}
    return out


# --- the arm's own records reach it; the other arm's never do ---------------------------------------------


def test_governed_admission_wrote_a_floor_view_and_its_learned_term(sc: Scenario) -> None:
    s = sc.s
    assert run(s.tool_access.view_map(RUN, GOV)) == {"customers": view_name("customers", sc.g_id)}
    assert view_name("customers", sc.g_id) in s.world_.views
    assert is_floor_view(view_name("customers", sc.g_id))
    rows = {t.term: t for t in run(s.terms.all())}
    assert rows[LEARNED].arm == GOV and not rows[LEARNED].runs, "a learned term never joins the run-wide map"


def test_consult_returns_nothing_of_governed(sc: Scenario) -> None:
    s = sc.s
    hooks = HookConsulter(s.decisions, s.terms, Rerank(), budget_tokens=10_000)
    _, u = run(hooks.consult(RUN, UNG, QUESTION))
    _, g = run(hooks.consult(RUN, GOV, QUESTION))
    assert [d.id for d in g] == [sc.g_id]
    assert all(d.arm == UNG for d in u) and sc.g_id not in {d.id for d in u}

    sim = Recording(NumpySimilarity(store_loader(s, emb_key(REP_ID))))   # type: ignore[arg-type]
    semantic = SemanticConsulter(s.decisions, s.terms, Rep(), sim, Rerank(), top_k=5, budget_tokens=10_000)
    _, u = run(semantic.consult(RUN, UNG, QUESTION))
    _, g = run(semantic.consult(RUN, GOV, QUESTION))
    assert [d.id for d in g] == [sc.g_id]
    assert [d.id for d in u] == [sc.u_id], "top-k over the arm's own store, even when governed's is nearer"
    assert all(f["arm"] in (UNG, GOV) and f["run_id"] == RUN for _, f in sim.filters), sim.filters
    assert {f["arm"] for _, f in sim.filters} == {UNG, GOV}


def test_extract_never_holds_another_arms_learned_term(sc: Scenario) -> None:
    s = sc.s
    assert run(s.terms.extract(QUESTION.text, run_id=RUN, arm=GOV)) == {TERM, LEARNED}
    assert run(s.terms.extract(QUESTION.text, run_id=RUN, arm=UNG)) == {TERM}
    assert run(s.terms.extract(QUESTION.text, run_id=RUN)) == {TERM}, "no arm: the seeded vocabulary only"
    assert LEARNED not in {t.term for t in run(s.terms.all(run_id=RUN, arm=UNG))}
    # the `$search` candidate path reads every row; the same membership rule post-filters it
    search = AtlasTerms(s.db["terms"])
    search._search_ok, search._synonyms_ok = True, False
    assert run(search.extract(QUESTION.text, run_id=RUN, arm=UNG)) == {TERM}
    assert run(search.extract(QUESTION.text, run_id=RUN, arm=GOV)) == {TERM, LEARNED}


def test_learned_terms_must_name_their_arm() -> None:
    with pytest.raises(ValueError, match="must name its run and arm"):
        Term(term="x", source="nominator", admitted_at_idx=0, run_id=RUN)


def test_l0_vocabulary_is_the_arms_own(sc: Scenario) -> None:
    """ungated's draft keyed on governed's learned term (without the escape) is refused at L0."""
    s = sc.s
    d = _decision_draft(f"{RUN}:{UNG}:r2:x", UNG, [], terms=(LEARNED,))
    ctx = CurationContext(run_id=RUN, arm=UNG, at_idx=20, sources=())
    out = run(L0Shape(s.terms).check(d, ctx))
    assert out.verdict is Verdict.REFUSE and LEARNED in str(out.detail["problems"])
    ok = run(L0Shape(s.terms).check(d.model_copy(update={"arm": GOV, "run_id": RUN}),
                                    CurationContext(run_id=RUN, arm=GOV, at_idx=20, sources=())))
    assert not any("vocabulary" in p for p in ok.detail["problems"])


def test_nominator_neighbours_residuals_and_vocabulary_are_the_arms_own(sc: Scenario) -> None:
    s = sc.s
    shape = shape_of(sc.g_obs)

    def nominator(rep: Any, sim: Any) -> Nominator:
        return Nominator(models=None, world=s.world_, episodes=s.episodes, terms=s.terms,  # type: ignore[arg-type]
                         decisions=s.decisions, representation=rep, similarity=sim, neighbour_k=5,
                         residual_window=4)

    numpy = Recording(NumpySimilarity(store_loader(s, emb_key(REP_ID))))   # type: ignore[arg-type]
    n = nominator(Rep(), numpy)
    assert [d.id for d, _ in run(n.neighbours(RUN, GOV, shape, sc.g_obs))] == [sc.g_id]
    assert sc.g_id not in {d.id for d, _ in run(n.neighbours(RUN, UNG, shape, sc.g_obs))}
    assert all({"run_id", "arm"} <= set(f) for _, f in numpy.filters)
    # a backend that ignores the pre-filter is caught by the re-check
    leaky = nominator(Rep(), Leaky([sc.g_id, sc.u_id]))
    assert [d.id for d, _ in run(leaky.neighbours(RUN, UNG, shape, sc.g_obs))] == [sc.u_id]
    # no representation: shared hook keys over the arm's admitted decisions
    keyed = nominator(NoRep(), None)
    assert run(keyed.neighbours(RUN, UNG, shape, sc.g_obs)) == []
    assert [d.id for d, _ in run(keyed.neighbours(RUN, GOV, shape, sc.g_obs))] == [sc.g_id]
    # a neighbour's residuals come from the arm's own consultations
    g_decision = run(s.decisions.get(sc.g_id))
    assert run(n.residuals(RUN, UNG, g_decision)) == ([], [])
    assert run(n.residuals(RUN, GOV, g_decision))[0]


def test_direction_read_and_backtest_population_are_the_arms_own(sc: Scenario) -> None:
    s = sc.s
    inside = {"terms": {"$in": [TERM]}}
    g = run(s.episodes.direction_read(RUN, GOV, inside, before_idx=100))
    u = run(s.episodes.direction_read(RUN, UNG, inside, before_idx=100))
    assert (g.n_in, g.misses_in) == (8, 4)
    assert (u.n_in, u.misses_in, u.n_out) == (0, 0, 2)
    uw = run(s.episodes.direction_read_window(RUN, UNG, inside, before_idx=100, last_n=40))
    assert (uw.n_in, uw.misses_in) == (0, 0)
    uw = run(s.episodes.direction_read_window(RUN, UNG, inside, before_idx=100, after_idx=0))
    assert (uw.n_in, uw.misses_in) == (0, 0)

    for override in ({}, {"arm": GOV}, {"run_id": "other", "arm": GOV}):   # a caller's filter never moves scope
        pop = run(s.episodes.backtest_sample(RUN, UNG, override, n=10, seed=None))
        assert pop and {e.arm for e in pop} == {UNG}
        pop = run(s.episodes.backtest_population(RUN, UNG, override, exclude_ids=[], after_idx=None, n=10))
        assert {e.arm for e in pop} == {UNG}
        rows = run(s.episodes.for_learner(RUN, UNG, with_authority=False, filter=override))
        assert rows and {r["arm"] for r in rows} == {UNG}
    assert {e.arm for e in run(s.episodes.backtest_sample(RUN, GOV, {}, n=10, seed=None))} == {GOV}
    assert run(s.episodes.consultations_of(RUN, UNG, sc.g_id, 10)) == []
    assert len(run(s.episodes.consultations_of(RUN, GOV, sc.g_id, 10))) == 8


def test_open_observations_held_drafts_and_tool_access_are_the_arms_own(sc: Scenario) -> None:
    s = sc.s
    assert run(s.observations.open_for_pass(RUN, UNG, since_round=0)) == []
    assert len(run(s.observations.open_for_pass(RUN, GOV, since_round=0))) == 4
    assert run(s.drafts.held(RUN, UNG)) == []
    assert [d.arm for d in run(s.drafts.held(RUN, GOV))] == [GOV]
    assert run(s.tool_access.view_map(RUN, UNG)) == {}
    assert run(s.tool_access.rewires(RUN, UNG)) == []
    assert run(s.backtests.for_arm(RUN, UNG)) == []
    assert run(s.decisions.match_hooks(RUN, UNG, run(HookConsulter(s.decisions, s.terms, Rerank(), 1)
                                                         .consult(RUN, GOV, QUESTION))[0])) == []


def test_lessons_merge_only_considers_the_arms_own_decisions(sc: Scenario) -> None:
    s = sc.s
    writer = DirectWriter(models=None, adjudicator=None, decisions=s.decisions,  # type: ignore[arg-type]
                          representation=Rep(), merge=True, merge_cosine=0.5)
    u_lesson = _decision_draft(f"{RUN}:{UNG}:r3:l", UNG, [], terms=(TERM,))
    target, score = run(writer._merge_target(u_lesson))
    assert target is None and score is not None and score < 0.5, "governed's identical vector is not a candidate"
    g_lesson = _decision_draft(f"{RUN}:{GOV}:r3:l", GOV, [], terms=(TERM,))
    target, _ = run(writer._merge_target(g_lesson))
    assert target is not None and target.id == sc.g_id


def test_lifecycle_sweep_reads_only_the_arms_decisions(sc: Scenario) -> None:
    s = sc.s
    out = run(sc.lifecycle.sweep(RUN, UNG, 10_000))
    assert sc.g_id not in out["moot"] + out["retired"] + out["contested"]
    assert run(s.decisions.get(sc.g_id)).lifecycle.status is LifecycleStatus.ADMITTED
    assert view_name("customers", sc.g_id) in s.world_.views


def test_execute_never_reaches_another_arms_floor_view(sc: Scenario) -> None:
    s = sc.s
    g_view = view_name("customers", sc.g_id)
    u_map = run(s.tool_access.view_map(RUN, UNG))
    lookup = Proposal(collection="accounts", answer_path="0.v", confidence=0.5, rationale="r", pipeline=[
        {"$lookup": {"from": g_view, "localField": "a", "foreignField": "a", "as": "c"}}])
    union = lookup.model_copy(update={"pipeline": [{"$facet": {"x": [{"$unionWith": g_view}]}}]})
    direct = lookup.model_copy(update={"collection": g_view, "pipeline": [{"$count": "v"}]})
    n_reads = len(s.world_.reads)
    for p in (lookup, union, direct):
        with pytest.raises(ExecutionError) as err:
            run(execute(p, u_map, s.world_, max_time_ms=1000))
        assert isinstance(err.value.__cause__, PipelineRefused)
    assert len(s.world_.reads) == n_reads, "a refused pipeline never reaches the world"
    # governed reaches its own view, through its register and by name
    g_map = run(s.tool_access.view_map(RUN, GOV))
    via_logical = lookup.model_copy(update={"pipeline": [
        {"$lookup": {"from": "customers", "localField": "a", "foreignField": "a", "as": "c"}}]})
    run(execute(via_logical, g_map, s.world_, max_time_ms=1000))
    assert s.world_.reads[-1][1][0]["$lookup"]["from"] == g_view
    run(execute(direct, g_map, s.world_, max_time_ms=1000))
    # ungated's own reads of the logical collection stay on the base collection
    run(execute(via_logical, u_map, s.world_, max_time_ms=1000))
    assert s.world_.reads[-1][1][0]["$lookup"]["from"] == "customers"


def test_the_nominators_world_tool_reads_base_collections_only(sc: Scenario) -> None:
    g_view = view_name("customers", sc.g_id)
    assert g_view not in logical_collections(run(sc.s.world_.collection_names()))
    with pytest.raises(PipelineRefused):
        check_scope(g_view, [], own_views=())
    with pytest.raises(PipelineRefused):
        check_scope("accounts", [{"$lookup": {"from": g_view, "as": "c", "pipeline": []}}], own_views=())
    check_scope("customers", [{"$lookup": {"from": "accounts", "as": "c", "pipeline": []}}], own_views=())


def test_another_arms_decision_is_never_a_predecessor(sc: Scenario) -> None:
    s = sc.s
    g_decision = run(s.decisions.get(sc.g_id))
    successor = _decision_draft(f"{RUN}:{UNG}:r4:s", UNG, [], terms=(TERM,)).model_copy(
        update={"route": Route.SUPERSEDE, "supersedes": sc.g_id})
    l2 = L2Neighbours(threshold=0.5, decisions=s.decisions, fires=s.fires)
    out = run(l2.check(successor, CurationContext(run_id=RUN, arm=UNG, at_idx=20, sources=())))
    assert out.verdict is Verdict.REFUSE and "another run or arm" in out.detail["reason"]
    with pytest.raises(LifecycleError, match="another run or arm"):
        plan_admission(successor, at_idx=20, backtest_id="B-x", lens_score=None, predecessors=(g_decision,))
    # a floor draft cannot shadow another arm's floor view either
    shadow = _decision_draft(f"{RUN}:{UNG}:r4:f", UNG, [], terms=(TERM,),
                             floor=FloorLatch(collection=view_name("customers", sc.g_id), match={"st": 1}))
    l0 = run(L0Shape(s.terms, world=s.world_).check(shadow, CurationContext(run_id=RUN, arm=UNG, at_idx=20,
                                                                             sources=())))
    assert l0.verdict is Verdict.REFUSE and any("floor view" in p for p in l0.detail["problems"])


def test_every_ungated_learner_read_carried_its_own_run_and_arm(sc: Scenario) -> None:
    """Replays ungated's reads against a cleared log: each read of a learner store names (run, ungated),
    or a key derived from one of ungated's own records (a decision id, an episode id)."""
    s = sc.s
    s.db.log.clear()
    shape = shape_of(sc.g_obs)
    numpy = NumpySimilarity(store_loader(s, emb_key(REP_ID)))   # type: ignore[arg-type]
    n = Nominator(models=None, world=s.world_, episodes=s.episodes, terms=s.terms,  # type: ignore[arg-type]
                  decisions=s.decisions, representation=Rep(), similarity=numpy, neighbour_k=5, residual_window=4)
    run(HookConsulter(s.decisions, s.terms, Rerank(), 10_000).consult(RUN, UNG, QUESTION))
    run(SemanticConsulter(s.decisions, s.terms, Rep(), numpy, Rerank(), 5, 10_000).consult(RUN, UNG, QUESTION))
    for d, _ in run(n.neighbours(RUN, UNG, shape, sc.g_obs)):
        run(n.residuals(RUN, UNG, d))
    run(s.episodes.direction_read_window(RUN, UNG, {"terms": {"$in": [TERM]}}, before_idx=100, last_n=40))
    run(s.episodes.backtest_sample(RUN, UNG, {}, n=10, seed=None))
    run(s.observations.open_for_pass(RUN, UNG, since_round=0))
    run(s.drafts.held(RUN, UNG))
    run(s.tool_access.view_map(RUN, UNG))
    run(sc.lifecycle.sweep(RUN, UNG, 10_000))
    own = {sc.u_id}
    scoped = {"episodes", "observations", "drafts", "tool_access", "backtests", "decisions"}
    assert s.db.log
    for coll, op, f in s.db.log:
        if coll == "terms":
            continue                       # shared seeded vocabulary; membership is post-filtered (above)
        if coll == "fires" or (coll == "decisions" and isinstance(f, dict) and set(f) == {"_id"}):
            key = f.get("decision_id") if coll == "fires" else f["_id"]
            assert key in own, (coll, op, f)
            continue
        assert coll in scoped, (coll, op, f)
        assert _scope(f) == {"run_id": RUN, "arm": UNG}, (coll, op, f)


def test_fires_are_keyed_by_decision_ids_that_name_their_arm(sc: Scenario) -> None:
    """`fires.open_for(decision_id)` filters by decision id only: decision ids hash (run, arm, round, shape),
    and every caller takes the id from an arm-scoped read (consultation, admitted set, neighbours, its own
    draft's L2-checked `supersedes`)."""
    s = sc.s
    assert [f.decision_id for f in run(s.fires.open_for(sc.g_id))] == [sc.g_id]
    assert run(s.fires.open_for(sc.u_id)) == []
    assert all(f.arm == GOV and f.role is FireRole.DISPOSITIVE for f in run(s.fires.for_decision(sc.g_id)))
    assert sc.g_id != sc.u_id


# --- process-level sharing: per-arm caches, nothing learned under `_run` -----------------------------------


def test_harness_caches_learning_collaborators_per_arm(settings_offline: Any) -> None:
    from munchhausen import bootstrap_learn
    from munchhausen.bootstrap import Harness

    store = Store()
    store.lenses = None   # type: ignore[attr-defined]
    h = Harness(settings=settings_offline.model_copy(update={"run_id": RUN}), store=store,  # type: ignore[arg-type]
                arms=settings_offline.arms())
    h.ports["_run"] = {"models": object(), "trace": None}
    built = {}
    for arm in (GOV, UNG):
        built[arm] = {"consulter": h.consulter(arm), "similarity": h.port(arm, "similarity"),
                      "representation": h.port(arm, "representation"), "reranker": h.port(arm, "reranker"),
                      "backtester": bootstrap_learn.backtester_for(h, arm),
                      "lifecycle": bootstrap_learn.lifecycle_for(h, arm),
                      "adjudicator": bootstrap_learn.adjudicator_for(h, arm),
                      "nominator": bootstrap_learn.nominator_for(h, arm)}
    for key in built[GOV]:
        assert built[GOV][key] is not built[UNG][key], key
        assert h.ports[GOV][key] is built[GOV][key] and h.ports[UNG][key] is built[UNG][key], key
    # run-wide: only stateless or by-design-shared ports (models: response cache keyed by arm; trace: write-only)
    assert set(h.ports["_run"]) <= {"models", "trace", "signal_source", "world"}, sorted(h.ports["_run"])
    assert built[GOV]["nominator"].similarity is built[GOV]["similarity"]
    assert built[UNG]["nominator"].similarity is built[UNG]["similarity"]
