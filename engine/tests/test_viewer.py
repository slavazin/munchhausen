"""Viewer (S6): read-model projections, the app over an in-memory run, and the injection beat with fakes.
Offline: no Atlas, no model calls."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from munchhausen.config import Settings
from munchhausen.domain.backtest import Backtest, BacktestSample
from munchhausen.domain.common import DecisionKind, LayerRole, Signature
from munchhausen.domain.draft import Draft, LayerOutcome, Shape, Verdict
from munchhausen.domain.episode import Episode, Judgement
from munchhausen.domain.ids import backtest_id, episode_id
from munchhausen.domain.latches import HookLatch, KeySet
from munchhausen.domain.observation import Observation, ObservationDisposition, Via
from munchhausen.domain.question import Question, SchemaSummary
from munchhausen.domain.registers import Cursor
from munchhausen.learn.episodic import Bar
from munchhausen.loop.inject import (
    INJECTION_STREAM,
    InjectedWorld,
    InjectionRequest,
    Injector,
    InjectParams,
    pick_questions,
)
from munchhausen.ports.curation import CurationContext
from munchhausen.store.read_models import change_event, evidence_at, status_at
from munchhausen_viewer.app import EventBus, create_app, pump
from munchhausen_viewer.memory import MemoryReadModel
from munchhausen_viewer.services import ViewerServices
from munchhausen_viewer.synthetic import _draft, build

RUN = "wt-s6-test"


@pytest.fixture
def s(settings_offline: Settings) -> Settings:
    return settings_offline.model_copy(update={"viewer_run_id": RUN})


@pytest.fixture
def rm(s: Settings) -> MemoryReadModel:
    return MemoryReadModel(build(s, RUN), s.round_size)


@pytest.fixture
def client(s: Settings, rm: MemoryReadModel) -> Iterator[TestClient]:
    svc = ViewerServices(settings=s, read_model=rm, arms=s.arms(), mode="synthetic")
    with TestClient(create_app(svc)) as c:
        yield c


# --- the story on the read side -----------------------------------------------------------------------


def test_config_names_no_secret_and_derives_reference(client: TestClient) -> None:
    cfg = client.get("/api/config").json()
    assert cfg["reference_arm"] == "frozen"          # derived: the arm whose write_path is none
    assert cfg["default_arm"] == "governed"
    assert "mongodb" not in str(cfg).lower() and "key" not in " ".join(cfg)


def test_decision_store_tells_the_story(client: TestClient, s: Settings) -> None:
    now = client.get("/api/decisions", params={"arm": "governed"}).json()
    status = {d["title"]: d["status"] for d in now}
    assert "superseded" in status.values() and list(status.values()).count("admitted") == 2
    old = next(d for d in now if d["status"] == "superseded")
    assert old["lifecycle"]["superseded_by"] and old["fan"]["revisits"][0]["signature"] == "set_member"
    assert old["backtest"]["verdict"] == "admit" and len(old["backtest"]["samples"]) == old["backtest"]["n"]
    floor = next(d for d in now if d["kind"] == "floor")
    assert floor["fan"]["floor"]["view"].startswith("accounts__")

    before_d1 = client.get("/api/decisions", params={"arm": "governed", "at": s.d1_at - 1}).json()
    assert all(d["status"] == "admitted" for d in before_d1) and len(before_d1) == 2   # no successor yet
    after_fire = client.get("/api/decisions", params={"arm": "governed", "at": s.d1_at + 20}).json()
    q1 = next(d for d in after_fire if d["id"] == old["id"])
    assert q1["status"] == "admitted" and q1["evidence_state"] == "contested"
    assert client.get("/api/decisions", params={"arm": "governed", "at": 10}).json() == []


def test_fire_ticker_carries_residuals_and_rewires(client: TestClient) -> None:
    rows = client.get("/api/fires").json()
    disp = next(r for r in rows if r["type"] == "fire" and r["role"] == "dispositive")
    assert disp["disposition"] == "applied" and disp["disposer"] == "lifecycle"
    assert any(r["type"] == "rewire" and r["after"].startswith("accounts__") for r in rows)


def test_curves_and_paired_readings(client: TestClient, s: Settings) -> None:
    c = client.get("/api/curves").json()
    assert c["reference"] == "frozen" and c["rolling"] and c["v"]
    gov = [r for r in c["readings"] if r["arm"] == "governed"]
    assert gov and all(r["n"] > 0 and r["lo"] <= r["diff"] <= r["hi"] for r in gov)
    assert gov[0]["segment"] == [0, s.d1_at] and "unit" in gov[0]


def test_why_term_walks_the_tombstone_chain(client: TestClient) -> None:
    w = client.get("/api/why", params={"target": "active_customer", "arm": "governed"}).json()
    statuses = [d["lifecycle"]["status"] for d in w["chain"]]
    assert statuses == ["superseded", "admitted"]
    assert w["chain"][0]["lifecycle"]["superseded_by"] == w["chain"][1]["id"]
    assert w["trail"][w["chain"][0]["id"]]["fires"]


def test_hero_episode_and_scrubber(client: TestClient) -> None:
    e = client.get("/api/episode", params={"arm": "governed", "at": 200}).json()
    assert e["idx"] == 200 and "consulted" in e and "resolved_collection" in e


def test_owner_port_unwired_is_501(client: TestClient) -> None:
    r = client.post("/api/owner/draft", json={"id": "x", "verdict": "admit"})
    assert r.status_code == 501


# --- pure projections -----------------------------------------------------------------------------------


def test_status_and_evidence_at(s: Settings) -> None:
    sr = build(s, RUN)
    rm = MemoryReadModel(sr, s.round_size)
    old = next(d for d in rm.decisions_.values() if d.lifecycle.status.value == "superseded")
    adm = rm._admitted_at(old)
    assert status_at(old, adm, adm - 1) is None
    assert status_at(old, adm, adm) == "admitted"
    assert status_at(old, adm, old.lifecycle.at_idx) == "superseded"
    fires = [f.model_dump(mode="json") for f in rm.fires_ if f.decision_id == old.id]
    assert evidence_at(old, fires, old.lifecycle.at_idx - 1) == "contested"
    assert evidence_at(old, fires, old.lifecycle.at_idx) == "clear"


def test_change_event_keeps_images_drops_vectors() -> None:
    ev = change_event({"_id": {"_data": "x"}, "operationType": "update", "ns": {"coll": "decisions"},
                       "documentKey": {"_id": "D-1"},
                       "fullDocument": {"_id": "D-1", "run_id": RUN, "arm": "governed", "emb": {"v": [1.0]},
                                        "lifecycle": {"status": "superseded"}},
                       "fullDocumentBeforeChange": {"_id": "D-1", "lifecycle": {"status": "admitted"}}})
    assert ev["before"]["lifecycle"]["status"] == "admitted" and ev["after"]["lifecycle"]["status"] == "superseded"
    assert "emb" not in ev["after"] and ev["collection"] == "decisions" and ev["run_id"] == RUN


async def test_pump_falls_back_to_polling(s: Settings, rm: MemoryReadModel) -> None:
    class Broken(MemoryReadModel):
        async def changes(self, run_id: str, collections: Sequence[str]):  # type: ignore[override]
            raise RuntimeError("no change streams here")
            yield {}

    broken = Broken(rm.sr, s.round_size)
    svc = ViewerServices(settings=s.model_copy(update={"poll_interval_s": 0.01}), read_model=broken,
                         arms=s.arms())
    bus = EventBus()
    q = bus.subscribe()
    task = asyncio.create_task(pump(svc, bus))
    seen = [await asyncio.wait_for(q.get(), 1) for _ in range(3)]
    task.cancel()
    assert bus.mode == "poll" and any(k == "change" and d["collection"] == "_poll" for k, d in seen)


# --- injection --------------------------------------------------------------------------------------


TEMPLATES = ("active_customers_count", "active_customers_by_tier", "trades_by_symbol")


class FakeWorld:
    id = "fake"

    def schema_summary(self) -> SchemaSummary:
        return SchemaSummary(collections={})

    def questions(self, seed: int) -> Iterator[Question]:
        k = 0
        while True:
            t = TEMPLATES[k % len(TEMPLATES)]
            yield Question(id=f"{seed}-{k}", text=f"q {t} {k}", template=t, persona="ops", collections=("customers",))
            k += 1

    def v_set(self) -> Sequence[Question]:
        return ()

    def world_version(self, idx: int) -> str:
        return "v0"

    async def build(self, seed: int) -> dict[str, int]:
        return {}

    async def judge(self, question: Question, answer: Any, idx: int, *, with_authority: bool) -> Judgement:
        raise AssertionError("injection must never reach the real authority")


class FakeForward:
    def __init__(self, world: Any) -> None:
        self.world = world

    async def run(self, idx: int, question: Question, *, stream: str = "stream") -> Episode:
        j = await self.world.judge(question, 100, idx, with_authority=True)
        return Episode(_id=episode_id(RUN, "governed", idx, stream=stream, question_id=question.id), run_id=RUN,
                       arm="governed", idx=idx, question_id=question.id, text=question.text,
                       template=question.template, persona=question.persona, terms=("active customers",),
                       world_version="v0", consulted=(), collection="customers", pipeline=[], answer_path="n",
                       view_map={}, answer=100, confidence=0.8, correct=j.correct, figure=j.figure,
                       phrasing=j.phrasing, stream=stream)


class Repo:
    def __init__(self) -> None:
        self.rows: dict[str, Any] = {}

    async def put(self, rec: Any) -> None:
        self.rows[rec.id] = rec

    async def get(self, id_: str) -> Any:
        return self.rows.get(id_)

    async def dispose(self, ids: Sequence[str], disposition: ObservationDisposition, by: str) -> None:
        for i in ids:
            self.rows[i] = self.rows[i].model_copy(update={"disposition": disposition, "disposed_by": by})


class FakeCursors:
    async def get(self, run_id: str, arm: str) -> Cursor:
        return Cursor(run_id=run_id, arm=arm, next_idx=412, round=13)


@dataclass(frozen=True)
class FakeNomination:
    draft: Draft
    neighbours: tuple = ()


class FakeNominator:
    async def nominate(self, run_id: str, arm: str, round_: int, shape: Shape,
                       members: Sequence[Observation]) -> FakeNomination:
        hook = HookLatch(fires_when=KeySet(terms=tuple(sorted(shape.terms)) or ("active customers",)))
        return FakeNomination(_draft(run_id, arm, round_, shape.id, title="Active customers are every account holder",
                                     kind=DecisionKind.TAXONOMIC, hook=hook, sig=Signature.SET_MEMBER, obs=members,
                                     payload="Every customer with an account counts as active."))


class FakeAdjudicator:
    """Stands in for S4: L0–L4, with a paired backtest that refuses (0 fixed, 2 broken)."""

    def __init__(self, backtests: Repo) -> None:
        self.backtests = backtests
        self.seen: list[tuple[Draft, CurationContext]] = []

    async def adjudicate(self, draft: Draft, ctx: CurationContext) -> list[LayerOutcome]:
        self.seen.append((draft, ctx))
        rows = tuple(BacktestSample(episode_id=f"e{k}", template="trades_by_symbol", original_correct=True,
                                    replay_correct=k >= 2, baseline_correct=True) for k in range(4))
        bt = Backtest.read(id=backtest_id(draft.id), run_id=ctx.run_id, arm=ctx.arm, draft_id=draft.id,
                           sampled=rows, source_templates=frozenset(TEMPLATES[:2]),
                           thresholds=Settings(_env_file=None).backtest_thresholds)
        await self.backtests.put(bt)
        return [LayerOutcome(layer=k, role=None, verdict=Verdict.PASS) for k in ("L0", "L1")] + [
            LayerOutcome(layer="L4", role=LayerRole.DISPOSITIVE, verdict=Verdict.REFUSE)]


def make_injector(s: Settings) -> tuple[Injector, Repo, FakeAdjudicator]:
    obs, drafts, bts = Repo(), Repo(), Repo()
    adj = FakeAdjudicator(bts)
    inj = Injector(world=FakeWorld(), forward_for=FakeForward, nominator=FakeNominator(), adjudicator=adj,
                   observations=obs, drafts=drafts, backtests=bts, cursors=FakeCursors(),  # type: ignore[arg-type]
                   bar=Bar(min_obs=s.bar_min_obs, min_templates=s.bar_min_templates, min_gap=s.bar_min_gap,
                           min_matched=s.bar_min_matched),
                   params=InjectParams(seed=s.inject_seed, scan_max=s.inject_scan_max, rel_tol=s.score_rel_tol))
    return inj, obs, adj


async def test_injected_world_returns_the_operators_figure() -> None:
    w = InjectedWorld(FakeWorld(), 4242, "active customers", 1e-4)   # type: ignore[arg-type]
    q = next(FakeWorld().questions(1))
    miss = await w.judge(q, 100, 0, with_authority=True)
    assert (miss.correct, miss.figure, miss.phrasing) == (False, 4242, "active customers")
    assert (await w.judge(q, 4242, 0, with_authority=True)).correct


def test_pick_questions_refuses_unknown_template() -> None:
    with pytest.raises(ValueError, match="nope"):
        pick_questions(FakeWorld(), ["nope"], 1, seed=1, scan_max=50)   # type: ignore[arg-type]


async def test_injection_ends_with_the_backtest_record(s: Settings) -> None:
    inj, obs, adj = make_injector(s)
    steps: list[str] = []
    req = InjectionRequest(run_id=RUN, arm="governed", templates=TEMPLATES[:2], figure=4242,
                           phrasing="active customers", per_template=1)
    res = await inj.run(req, lambda name, payload: steps.append(name))
    assert all(e.stream == INJECTION_STREAM and e.figure == 4242 for e in res.episodes)
    assert len(res.observations) == 2 and all(o.via is Via.INJECTION for o in obs.rows.values())
    assert all(o.surfaces.phrasing == "active customers" for o in res.observations)
    assert all(o.disposition is ObservationDisposition.SPENT for o in obs.rows.values())   # refused → spent
    draft, ctx = adj.seen[0]
    assert draft.adjudication["bar"].detail["direction_read"] == "skipped"
    assert ctx.at_idx == 412 and {o.id for o in ctx.sources} == {o.id for o in res.observations}
    assert res.backtest is not None and res.backtest.verdict.value == "refuse" and res.backtest.broken == 2
    assert steps[0] == "questions" and steps[-1] == "done" and res.summary()["backtest"]["fixed"] == 0


async def test_injection_on_one_template_holds_at_the_bar(s: Settings) -> None:
    inj, _, adj = make_injector(s)
    req = InjectionRequest(run_id=RUN, arm="governed", templates=TEMPLATES[:1], figure=4242,
                           phrasing="active customers", per_template=2)
    res = await inj.run(req)
    assert not res.bar_cleared and res.draft is None and not adj.seen and "bar" in (res.stopped or "")


def test_injection_through_the_app(s: Settings, rm: MemoryReadModel) -> None:
    inj, _, _ = make_injector(s)
    svc = ViewerServices(settings=s, read_model=rm, arms=s.arms(), injector_for=lambda arm: inj)
    with TestClient(create_app(svc)) as c:
        assert c.post("/api/inject", json={"arm": "frozen", "templates": ["x"], "figure": 1,
                                           "phrasing": "p"}).status_code == 400   # no authority on frozen
        job = c.post("/api/inject", json={"templates": list(TEMPLATES[:2]), "figure": 4242,
                                          "phrasing": "active customers"}).json()
        deadline = time.monotonic() + 5
        while (st := c.get(f"/api/inject/{job['id']}").json())["status"] == "running":
            assert time.monotonic() < deadline
            time.sleep(0.02)
        assert st["status"] == "done", st
        assert st["result"]["backtest"]["verdict"] == "refuse" and st["steps"][-1]["step"] == "done"
