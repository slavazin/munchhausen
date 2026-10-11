"""Forward pass (S2, M2): consultation, the proposer party, residuals and fires, terms, and the composition
root's null fallbacks. Offline: fakes for Models, Store and World."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pytest

from munchhausen.agent.consultation import (
    HookConsulter,
    NoConsulter,
    SemanticConsulter,
    consulter_for,
    lexical_top_k,
)
from munchhausen.agent.proposer import Proposer
from munchhausen.agent.terms import noun_phrases, present_terms, seed_terms
from munchhausen.config import Settings
from munchhausen.domain.arm import ArmSpec, ConsultationMode, WritePath
from munchhausen.domain.common import (
    DecisionKind,
    Disposition,
    FireDisposition,
    FireRole,
    LifecycleStatus,
    Signature,
)
from munchhausen.domain.decision import Decision, Lifecycle, Option, Warrant
from munchhausen.domain.episode import Consultation, Episode, Judgement, Proposal
from munchhausen.domain.fire import Fire
from munchhausen.domain.latches import Guard, HookLatch, KeySet, RevisitLatch
from munchhausen.domain.question import Question, QuestionKeys, SchemaSummary
from munchhausen.domain.registers import Cursor, Term, term_arm_key, term_run_key, term_visible
from munchhausen.impl.parties import proposer as proposer_party
from munchhausen.impl.representation import NoRepresentation
from munchhausen.impl.reranker import IdentityReranker
from munchhausen.impl.similarity import NumpySimilarity, store_loader
from munchhausen.loop.episode import ForwardParams, ForwardPass
from munchhausen.loop.residuals import compute_residuals, rounding_unit
from munchhausen.ports.models import ProposerInput
from munchhausen.store.atlas import GuardedReader
from munchhausen.world.pack import Pack, Quirk, TransformRef


def run(coro):  # noqa: ANN001, ANN201
    return asyncio.run(coro)


SCHEMA = SchemaSummary(collections={
    "customers": {"_id": "objectId", "username": "string", "st": "int", "tier_and_details": "object",
                  "tier_and_details.$key.tier": "string", "accounts": "array<int>"},
    "accounts": {"account_id": "int", "limit": "int"},
    "transactions": {"transactions": "array<object>", "transactions.total": "string"}})
ACTIVE = "active customers"
PHRASING = "That is not how active customers are counted."


def question(i: int, template: str = "active_count") -> Question:
    texts = {"active_count": f"How many active customers opened accounts in {2000 + i % 5}?",
             "control": f"How many accounts have a limit above {1000 * (i % 3 + 1)}?"}
    return Question(id=f"q{i}", text=texts[template], template=template, persona="omar",
                    collections=("customers",) if template == "active_count" else ("accounts",))


def decision(did: str = "D-1", *, terms: tuple[str, ...] = (ACTIVE,), signature: Signature = Signature.SET_MEMBER,
             arm: str = "hooks", run_id: str = "r") -> Decision:
    return Decision(
        _id=did, run_id=run_id, arm=arm, title="Active customers carry status codes in the active set",
        kind=DecisionKind.TAXONOMIC, payload="A customer is active when field st holds a code in the active set.",
        options=(Option(definition="not closed", verdict="rejected", prior=True),
                 Option(definition="st in active set", verdict="chosen")),
        forecloses="counting every non-closed customer",
        latches=(HookLatch(fires_when=KeySet(terms=terms, collections=("customers",))),
                 RevisitLatch(id=f"T-{did}-1", signature=signature, guard=Guard(min_residuals=2, window=30))),
        residue="does not check joins from accounts",
        warrant=Warrant(source_observation_ids=("o1",), source_episode_ids=("e1",), templates=2,
                        falsifier="two attributable residuals within 30 consultations"),
        lifecycle=Lifecycle(status=LifecycleStatus.ADMITTED, at_idx=0))


# --- fakes ---------------------------------------------------------------------------------------------


class FakeTrace:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def begin(self, episode: dict[str, Any]) -> None: ...

    def signal(self, name: str, value: Any, comment: str | None = None) -> None: ...

    def event(self, name: str, payload: dict[str, Any]) -> None:
        self.events.append((name, payload))

    def finish(self, output: Any) -> None: ...

    def names(self) -> list[str]:
        return [n for n, _ in self.events]


class _Cursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    async def to_list(self) -> list[dict[str, Any]]:
        return list(self._docs)


class FakeColl:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows, self.pipelines = rows, []

    async def aggregate(self, pipeline: list[dict[str, Any]], maxTimeMS: int) -> _Cursor:  # noqa: N803
        self.pipelines.append(pipeline)
        limit = next((s["$limit"] for s in reversed(pipeline) if "$limit" in s), None)
        return _Cursor(self.rows[:limit] if limit else self.rows)

    def find(self, filter: Any, projection: Any, limit: int = 0, **kw: Any) -> _Cursor:  # noqa: A002
        return _Cursor(self.rows[:limit] if limit else self.rows)


class FakeDB:
    """The `world` database as pymongo's AsyncDatabase presents it to the store's readers."""

    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.colls = {k: FakeColl(v) for k, v in collections.items()}

    def __getitem__(self, name: str) -> FakeColl:
        return self.colls.setdefault(name, FakeColl([]))

    async def list_collection_names(self) -> list[str]:
        return sorted(self.colls)


class FakeEpisodes:
    def __init__(self) -> None:
        self.docs: dict[str, Episode] = {}
        self.puts = 0

    async def put(self, e: Episode) -> None:
        self.docs[e.id] = e
        self.puts += 1

    async def get(self, eid: str) -> Episode | None:
        return self.docs.get(eid)

    async def exists(self, run_id: str, arm: str, idx: int) -> bool:
        return any(e.run_id == run_id and e.arm == arm and e.idx == idx for e in self.docs.values())

    async def consultations_of(self, run_id: str, arm: str, decision_id: str, last_n: int) -> list[Episode]:
        hits = [e for e in self.docs.values() if e.run_id == run_id and e.arm == arm
                and any(c.decision_id == decision_id for c in e.consulted)]
        return sorted(hits, key=lambda e: e.idx, reverse=True)[:last_n]


class FakeDecisions:
    def __init__(self, decisions: Sequence[Decision] = ()) -> None:
        self.rows = list(decisions)
        self.refreshed: list[str] = []

    async def admitted(self, run_id: str, arm: str) -> list[Decision]:
        return [d for d in self.rows if d.run_id == run_id and d.arm == arm and d.is_admitted]

    async def match_hooks(self, run_id: str, arm: str, keys: QuestionKeys) -> list[Decision]:
        return [d for d in await self.admitted(run_id, arm) if d.hook.matches(keys)]

    async def refresh_evidence_state(self, decision_id: str) -> None:
        self.refreshed.append(decision_id)


class FakeFires:
    def __init__(self) -> None:
        self.rows: dict[str, Fire] = {}

    async def put(self, f: Fire) -> None:
        self.rows[f.id] = f

    async def open_for(self, decision_id: str) -> list[Fire]:
        return [f for f in self.rows.values() if f.decision_id == decision_id
                and f.disposition is FireDisposition.OPEN]

    async def put_new(self, f: Fire) -> bool:
        if f.id in self.rows:
            return False
        self.rows[f.id] = f
        return True

    async def disposed_count(self, decision_id: str, latch: str) -> int:
        return sum(1 for f in self.rows.values() if f.decision_id == decision_id and f.latch == latch
                   and f.disposition is not FireDisposition.OPEN)


class FakeCursors:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict[str, int]] = {}

    async def get(self, run_id: str, arm: str) -> Cursor:
        row = self.rows.setdefault((run_id, arm), {"next_idx": 0, "round": 0})
        return Cursor(run_id=run_id, arm=arm, **row)

    async def claim_next(self, run_id: str, arm: str, *, limit: int) -> int | None:
        row = self.rows.setdefault((run_id, arm), {"next_idx": 0, "round": 0})
        if row["next_idx"] >= limit:
            return None
        row["next_idx"] += 1
        return row["next_idx"] - 1

    async def set_round(self, run_id: str, arm: str, round_: int) -> None:
        self.rows[(run_id, arm)]["round"] = round_


class FakeLeases:
    def __init__(self, ttl_s: float = 120.0) -> None:
        self.rows: dict[tuple[str, str, int], tuple[str, datetime]] = {}
        self.ttl = ttl_s

    async def acquire(self, run_id: str, arm: str, idx: int, worker: str) -> bool:
        if (run_id, arm, idx) in self.rows:
            return False
        self.rows[(run_id, arm, idx)] = (worker, datetime.now(UTC) + timedelta(seconds=self.ttl))
        return True

    async def take_over(self, run_id: str, arm: str, idx: int, worker: str) -> bool:
        held = self.rows.get((run_id, arm, idx))
        if held is not None and held[1] < datetime.now(UTC):
            self.rows[(run_id, arm, idx)] = (worker, datetime.now(UTC) + timedelta(seconds=self.ttl))
            return True
        return await self.acquire(run_id, arm, idx, worker)

    async def release(self, run_id: str, arm: str, idx: int, *, worker: str | None = None) -> None:
        held = self.rows.get((run_id, arm, idx))
        if held is not None and (worker is None or held[0] == worker):
            self.rows.pop((run_id, arm, idx), None)


class FakeToolAccess:
    async def view_map(self, run_id: str, arm: str) -> dict[str, str]:
        return {}


class FakeTerms:
    def __init__(self, rows: Sequence[Term]) -> None:
        self.rows = list(rows)

    async def all(self, *, run_id: str | None = None, arm: str | None = None) -> list[Term]:
        return [r for r in self.rows if term_visible(r, run_id=run_id, arm=arm)]

    async def add(self, term: Term) -> None:
        """As `AtlasTerms.add`: one row per term, runs (seeded) and arm_runs (learned) as membership maps
        (earliest idx wins)."""
        old = next((r for r in self.rows if r.term == term.term), None)
        runs = dict(old.runs) if old else {}
        arm_runs = dict(old.arm_runs) if old else {}
        if term.learned and term.run_id is not None and term.arm is not None:
            k = term_arm_key(term.run_id, term.arm)
            arm_runs[k] = min(arm_runs.get(k, term.admitted_at_idx), term.admitted_at_idx)
        elif term.run_id is not None:
            k = term_run_key(term.run_id)
            runs[k] = min(runs.get(k, term.admitted_at_idx), term.admitted_at_idx)
        new = (old or term).model_copy(update={"runs": runs, "arm_runs": arm_runs})
        self.rows = [r for r in self.rows if r.term != term.term] + [new]

    async def extract(self, text: str, *, run_id: str | None = None, arm: str | None = None) -> frozenset[str]:
        return present_terms(text, await self.all(run_id=run_id, arm=arm))

    async def compile_synonyms(self) -> int:
        return 0


class FakeStore:
    def __init__(self, decisions: Sequence[Decision] = (), rows: list[dict[str, Any]] | None = None,
                 lease_ttl_s: float = 120.0) -> None:
        self.episodes, self.decisions, self.fires = FakeEpisodes(), FakeDecisions(decisions), FakeFires()
        self.cursors, self.leases, self.tool_access = FakeCursors(), FakeLeases(lease_ttl_s), FakeToolAccess()
        self.terms = FakeTerms([Term(term=t, source="question", admitted_at_idx=0, runs={"r": 0})
                                for t in (ACTIVE, "customers", "limit")])
        self.db = FakeDB({"customers": rows if rows is not None else [{"n": 10}], "accounts": [{"n": 4}]})

    def world(self) -> GuardedReader:
        return GuardedReader(self.db, row_cap=100, max_time_ms=5000)  # type: ignore[arg-type]


class FakeWorld:
    """Q-template questions miss (the agent answers 10, the authority expects 12); controls hit."""

    id = "fake+pack"

    def __init__(self, figure: float = 12.0) -> None:
        self.figure, self.judged = figure, []

    def schema_summary(self) -> SchemaSummary:
        return SCHEMA

    def questions(self, seed: int) -> Iterator[Question]:
        i = 0
        while True:
            yield question(i, "active_count" if i % 2 == 0 else "control")
            i += 1

    def v_set(self) -> Sequence[Question]:
        return [question(100 + j, "control") for j in range(3)]

    def world_version(self, idx: int) -> str:
        return "v0" if idx < 300 else "v0+D1"

    async def judge(self, q: Question, answer: Any, idx: int, *, with_authority: bool) -> Judgement:
        self.judged.append((q.id, idx, with_authority))
        if q.template == "control":
            return Judgement(correct=answer == 4)
        if answer == self.figure:
            return Judgement(correct=True)
        return Judgement(correct=False, figure=self.figure if with_authority else None,
                         phrasing=PHRASING if with_authority else None)


class FakeModels:
    """Counts with `$count`; applies every consulted decision; optionally emits a refused pipeline."""

    def __init__(self, pipeline: list[dict[str, Any]] | None = None, fail: bool = False) -> None:
        self.pipeline, self.fail, self.calls = pipeline, fail, []

    async def propose(self, inp: ProposerInput) -> Proposal:
        self.calls.append(inp)
        if self.fail:
            raise RuntimeError("model unavailable")
        return Proposal(collection=inp.question.collections[0], pipeline=self.pipeline or [{"$count": "n"}],
                        answer_path="0.n", consulted=tuple(Consultation(decision_id=d.id,
                                                                        disposition=Disposition.APPLIED)
                                                           for d in inp.consulted),
                        confidence=0.8, rationale="Counts the matching documents.")


def arm(name: str = "hooks", *, authority: bool = True, mode: ConsultationMode = ConsultationMode.HOOKS) -> ArmSpec:
    return ArmSpec(name=name, authority=authority, write_path=WritePath.EPISODIC if authority else WritePath.NONE,
                   consultation=mode)


def forward(store: FakeStore, spec: ArmSpec, models: FakeModels | None = None,
            world: FakeWorld | None = None) -> tuple[ForwardPass, FakeTrace]:
    trace = FakeTrace()
    consulter = (HookConsulter(store.decisions, store.terms, IdentityReranker(), 900)  # type: ignore[arg-type]
                 if spec.consultation is ConsultationMode.HOOKS else NoConsulter())
    fp = ForwardPass(run_id="r", arm=spec, world=world or FakeWorld(), store=store,  # type: ignore[arg-type]
                     consulter=consulter, proposer=Proposer(models or FakeModels()), trace=trace,  # type: ignore[arg-type]
                     params=ForwardParams(max_time_ms=3000, rel_tol=1e-4, propose_attempts=2, rounding_base=10,
                                          fire_fetch_factor=2))
    return fp, trace


# --- the forward pass ---------------------------------------------------------------------------------------


def test_frozen_episode_consults_nothing_and_never_reads_the_authority() -> None:
    store, world = FakeStore(), FakeWorld()
    fp, trace = forward(store, arm("frozen", authority=False, mode=ConsultationMode.NONE), world=world)
    ep = run(fp.run(0, question(0)))
    assert ep.consulted == () and not ep.correct and ep.figure is None and ep.confirmed_figure is None
    assert ep.retry_pipeline is None and ep.residuals == ()
    assert world.judged == [("q0", 0, False)]
    assert {"consultation_set", "view_resolved", "episode_written"} <= set(trace.names())


def test_hook_arm_applies_a_matched_decision_and_fires_on_agreeing_attributable_residuals() -> None:
    store = FakeStore([decision()])
    fp, trace = forward(store, arm())
    e0 = run(fp.run(0, question(0)))
    assert [c.decision_id for c in e0.consulted] == ["D-1"] and ACTIVE in e0.terms
    assert e0.confirmed_figure == 12.0 and e0.retry_pipeline is not None and e0.retry_correct is False
    (r,) = e0.residuals
    assert r.attributable and r.signature_match and r.delta == -2.0
    assert not [f for f in store.fires.rows.values() if f.role is FireRole.DISPOSITIVE]
    run(fp.run(2, question(2)))
    dispositive = [f for f in store.fires.rows.values() if f.role is FireRole.DISPOSITIVE]
    assert len(dispositive) == 1 and dispositive[0].at_idx == 2 and store.decisions.refreshed == ["D-1"]
    assert "fire_raised" in trace.names()
    consults = [p for n, p in trace.events if n == "consultation_set"]
    assert consults[0]["decision_ids"] == ["D-1"]


def test_a_residual_is_unattributable_when_another_applied_hook_names_the_concept() -> None:
    a, b = decision("D-a"), decision("D-b")
    out = compute_residuals("e", [Consultation(decision_id=d.id, disposition=Disposition.APPLIED) for d in (a, b)],
                            {a.id: a, b.id: b}, 10.0, 12.0, frozenset({ACTIVE}), rounding_base=10)
    assert not any(r.attributable for r in out)
    c = decision("D-c", terms=(ACTIVE, "status code"))
    out = compute_residuals("e", [Consultation(decision_id=d.id, disposition=Disposition.APPLIED) for d in (a, c)],
                            {a.id: a, c.id: c}, 10.0, 12.0, frozenset({ACTIVE, "status code"}), rounding_base=10)
    assert {r.decision_id: r.attributable for r in out} == {"D-a": False, "D-c": True}


def test_rounding_signature_is_derived_from_the_figure_not_a_pack_literal() -> None:
    assert rounding_unit(1_204_000, 10) == 1000 and rounding_unit(1204, 10) == 1 and rounding_unit(0, 10) == 1
    d = decision(signature=Signature.ROUNDING)
    applied = [Consultation(decision_id=d.id, disposition=Disposition.APPLIED)]
    near = compute_residuals("e", applied, {d.id: d}, 1_203_817.0, 1_204_000.0, frozenset(), rounding_base=10)
    far = compute_residuals("e", applied, {d.id: d}, 1_190_000.0, 1_204_000.0, frozenset(), rounding_base=10)
    assert near[0].signature_match and not far[0].signature_match


def test_a_guard_refusal_is_an_irreducible_miss_and_a_trace_event() -> None:
    store = FakeStore()
    fp, trace = forward(store, arm(), FakeModels(pipeline=[{"$out": "customers"}]))
    ep = run(fp.run(0, question(0)))
    assert ep.answer is None and ep.error and "$out" in ep.error
    refusals = [p for n, p in trace.events if n == "guard_refusal"]
    assert refusals and refusals[0]["episode_id"] == ep.id
    assert all("$out" not in str(p) for p in store.db.colls["customers"].pipelines)


def test_a_failing_proposer_leaves_a_judged_error_episode_not_a_hole() -> None:
    store, models = FakeStore(), FakeModels(fail=True)
    fp, trace = forward(store, arm(), models)
    ep = run(fp.run(0, question(0)))
    assert ep.error == "proposer: no proposal" and not ep.correct and ep.confirmed_figure == 12.0
    assert len(models.calls) == 2 and trace.names().count("proposal_failed") == 2


def test_v_episodes_skip_the_authority_and_never_fire() -> None:
    store, world = FakeStore([decision()]), FakeWorld()
    fp, _ = forward(store, arm(), world=world)
    ep = run(fp.run(-1, question(0), stream="v", at_idx=375))
    assert ep.idx == -1 and ep.stream == "v" and ep.world_version == "v0+D1" and ":v:q0:375" in ep.id
    assert ep.residuals == () and ep.figure is None and ep.retry_pipeline is None and not store.fires.rows
    assert world.judged == [("q0", 375, False)]


# --- consultation ----------------------------------------------------------------------------------------


def test_consulter_for_dispatches_on_the_mode() -> None:
    store = FakeStore()
    deps = dict(decisions=store.decisions, terms=store.terms, representation=NoRepresentation(),
                similarity=NumpySimilarity(store_loader(store, "voyage_4")), reranker=IdentityReranker(),
                top_k=8, budget_tokens=900)
    assert isinstance(consulter_for(arm(mode=ConsultationMode.HOOKS), **deps), HookConsulter)  # type: ignore[arg-type]
    assert isinstance(consulter_for(arm(mode=ConsultationMode.SEMANTIC), **deps), SemanticConsulter)  # type: ignore[arg-type]
    assert isinstance(consulter_for(arm(mode=ConsultationMode.NONE), **deps), NoConsulter)  # type: ignore[arg-type]


def test_semantic_consultation_runs_offline_on_the_null_representation() -> None:
    off_topic = decision("D-2", terms=("revenue",)).model_copy(update={"title": "Revenue nets the fee",
                                                                       "payload": "Subtract the fee field."})
    store = FakeStore([decision(arm="sem"), off_topic.model_copy(update={"arm": "sem"})])
    c = SemanticConsulter(store.decisions, store.terms, NoRepresentation(),  # type: ignore[arg-type]
                          NumpySimilarity(store_loader(store, "voyage_4")), IdentityReranker(), 1, 900)  # type: ignore[arg-type]
    _, got = run(c.consult("r", "sem", question(0)))
    assert [d.id for d in got] == ["D-1"]
    assert lexical_top_k("an unrelated sentence", store.decisions.rows, 3) == []


def test_numpy_similarity_reads_vectors_through_the_store_port() -> None:
    d1 = decision("D-1", arm="sem").model_copy(update={"emb": {"voyage_4": [1.0, 0.0]}})
    d2 = decision("D-2", arm="sem").model_copy(update={"emb": {"voyage_4": [0.0, 1.0]}})
    store = FakeStore([d1, d2])
    sim = NumpySimilarity(store_loader(store, "voyage_4"))
    hits = run(sim.knn("decisions", [0.9, 0.1], 1, {"run_id": "r", "arm": "sem", "lifecycle.status": "admitted"}))
    assert hits[0][0] == "D-1"
    assert run(sim.knn("decisions", [0.9, 0.1], 2, {"run_id": "r", "arm": "sem", "lifecycle.status": "moot"})) == []


# --- the proposer party ------------------------------------------------------------------------------------


class _LLM:
    def __init__(self, wire: Any) -> None:
        self.wire, self.kwargs = wire, {}

    async def parse(self, *, stage: str, arm: str, model: str, system: str, user: str, wire: type,
                    effort: str | None = None, max_tokens: int = 16000, temperature: float | None = None) -> Any:
        self.kwargs = dict(stage=stage, system=system, user=user, temperature=temperature, max_tokens=max_tokens)
        return self.wire


def test_proposer_prompt_keeps_learned_content_out_of_the_always_loaded_set(settings_offline: Settings) -> None:
    d = decision()
    wire = proposer_party.ProposalWire(collection="customers", pipeline_json='[{"$count": "n"}]', answer_path="0.n",
                                       terms_used=[ACTIVE], consulted=[Consultation(decision_id="D-zz",
                                                                                    disposition=Disposition.APPLIED)],
                                       anomalies=[], confidence=1.4, rationale="Counts.")
    llm = _LLM(wire)
    inp = ProposerInput(question=question(0), schema=SCHEMA, consulted=[d], arm="hooks")
    p = run(proposer_party.run(llm, settings_offline, inp))
    assert d.payload not in llm.kwargs["system"] and d.id not in llm.kwargs["system"]
    assert "st: int" in llm.kwargs["system"] and d.payload in llm.kwargs["user"]
    assert "Apply each one whose hook matched" in llm.kwargs["user"]
    assert llm.kwargs["temperature"] == settings_offline.proposer_temperature is None   # haiku-5-5 refuses it
    p0 = run(proposer_party.run(llm, settings_offline.model_copy(update={"proposer_temperature": 0.0}), inp))
    assert llm.kwargs["temperature"] == 0.0 and p0.pipeline == [{"$count": "n"}]
    assert p.consulted == (Consultation(decision_id="D-1", disposition=Disposition.CONSIDERED_NOT_APPLICABLE),)
    assert p.confidence == 1.0 and p.pipeline == [{"$count": "n"}]
    assert proposer_party.system_prompt(SCHEMA) == llm.kwargs["system"]   # stable: hashable per run


def test_retry_prompt_carries_the_authority_figure_and_phrasing(settings_offline: Settings) -> None:
    inp = ProposerInput(question=question(0), schema=SCHEMA, consulted=[], retry_figure=12.0,
                        retry_phrasing=PHRASING, stage="retry")
    text = proposer_party.user_prompt(inp)
    assert "expected 12.0" in text and PHRASING in text


def test_an_unparseable_pipeline_becomes_a_refused_stage() -> None:
    assert proposer_party._pipeline("not json") == ([{"$unparsed": "not json"}], ())
    assert proposer_party._pipeline('{"$count": "n"}') == ([{"$count": "n"}], ())


# --- the term vocabulary ---------------------------------------------------------------------------------


def test_present_terms_bias_broad_and_fold_plurals_and_aliases() -> None:
    rows = [Term(term=ACTIVE, aliases=("live clients",), source="question", admitted_at_idx=0),
            Term(term="customers", source="schema", admitted_at_idx=0)]
    assert present_terms("How many active customers?", rows) == {ACTIVE, "customers"}
    assert present_terms("Count the live client base", rows) == {ACTIVE}
    assert present_terms("How many accounts?", rows) == frozenset()


def test_seeding_never_reads_the_pack() -> None:
    pack = Pack(id="analytics-v1", adapter="sample_analytics", quirks=(
        Quirk(id="Q1_active_customer", kind="taxonomic", prior_trap="active means not closed",
              gold=TransformRef(transform="status_in", params={"active": [2, 7]}),
              materialize=TransformRef(transform="assign_status_codes", params={"codes": [1, 2, 4, 7]}),
              authority_phrasings=(PHRASING,)),))
    questions = [question(i) for i in range(10)] + [question(i, "control") for i in range(10)]
    terms = {t.term for t in seed_terms(SCHEMA, questions, min_questions=2, max_tokens=3)}
    assert ACTIVE in terms and "customers" in terms and "tier and details" in terms
    assert "tier" not in terms   # a path through a `$key` map placeholder is dropped whole (S1)
    assert "total" in terms and not any("$" in t or t == "key" or t == "id" for t in terms)
    assert not any(t in {"string", "int", "object", "objectid"} for t in terms)   # names only, never types
    banned = {pack.id, *(q.id.lower() for q in pack.quirks)}
    for q in pack.quirks:
        for ref in (q.gold, q.materialize):
            assert ref is not None
            banned |= {ref.transform, *(str(v) for v in ref.params.values())}
        banned.add(q.prior_trap)
    assert not terms & banned
    assert not any(q.id.lower() in t for q in pack.quirks for t in terms)
    assert not any(ch.isdigit() for t in terms for ch in t)


def test_noun_phrases_break_on_stopwords_numbers_and_codes() -> None:
    got = noun_phrases("How many active customers traded AAPL in 2017?", 3)
    assert "active customers" in got and "aapl" not in got and not any("2017" in p for p in got)


# --- the composition root ---------------------------------------------------------------------------------


def test_missing_voyage_key_selects_the_null_ports(settings_offline: Settings) -> None:
    from munchhausen.bootstrap import Harness, effective_name

    assert effective_name("representation", "voyage-4", settings_offline) == "none"
    assert effective_name("reranker", "rerank-3", settings_offline) == "identity"
    assert effective_name("similarity", "atlas-vector", settings_offline) == "atlas-vector"
    h = Harness(settings=settings_offline, store=FakeStore(), arms=settings_offline.arms())  # type: ignore[arg-type]
    sel = h.selection()
    assert sel["naive"]["representation"] == "none" and sel["governed"]["reranker"] == "identity"
    assert isinstance(h.port("naive", "representation"), NoRepresentation)
    keyed = settings_offline.model_copy(update={"voyage_api_key": "x"})
    assert effective_name("representation", "voyage-4", keyed) == "voyage-4"


def test_round_hook_tolerates_unbuilt_seams(settings_offline: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    from munchhausen import evidence
    from munchhausen.bootstrap import Harness

    async def unbuilt(*a: object, **k: object) -> None:
        raise NotImplementedError("seam not built")

    monkeypatch.setattr(evidence, "close_round", unbuilt)
    from munchhausen import bootstrap_learn

    monkeypatch.setattr(bootstrap_learn, "backward_for", lambda h, arm: unbuilt)
    h = Harness(settings=settings_offline, store=FakeStore(), arms=settings_offline.arms())  # type: ignore[arg-type]
    for name in ("frozen", "governed"):
        run(h.round_hook(name)(0, (0, 30)))     # NotImplementedError from S4/S5 seams is logged, not raised


def test_numpy_array_shapes_for_empty_store() -> None:
    store = FakeStore()
    ids, mat = run(store_loader(store, "voyage_4")("decisions", {"run_id": "r", "arm": "x"}))
    assert ids == [] and isinstance(mat, np.ndarray)


@pytest.mark.parametrize("bad", ["$where", "$function"])
def test_find_filters_are_guarded_too(bad: str) -> None:
    from munchhausen.domain.pipeline_guard import PipelineRefused

    with pytest.raises(PipelineRefused):
        run(FakeStore().world().find("customers", {bad: "1"}))
    with pytest.raises(PipelineRefused):     # projections carry expressions too
        run(FakeStore().world().find("customers", {}, {"x": {bad: {"body": "f"}}}))


# --- review fixes (S2 round 2) ------------------------------------------------------------------------------


def test_backtester_via_bootstrap_learn_consults_through_the_arms_consulter(settings_offline: Settings) -> None:
    from munchhausen import bootstrap_learn
    from munchhausen.bootstrap import Harness

    store = FakeStore([decision(arm="governed")])
    store.backtests = None  # type: ignore[attr-defined]
    h = Harness(settings=settings_offline.model_copy(update={"run_id": "r"}), store=store,  # type: ignore[arg-type]
                arms=settings_offline.arms())
    h.ports["_run"] = {"models": FakeModels(), "trace": FakeTrace()}
    bt = bootstrap_learn.backtester_for(h, "governed")
    keys, consulted = run(bt.consulter.consult("r", "governed", question(0)))
    assert [d.id for d in consulted] == ["D-1"] and ACTIVE in keys.terms
    assert h.ports["governed"]["consulter"] is h.consulter("governed") is bootstrap_learn.consulter(h, "governed")


def test_floor_definitions_pass_the_sandbox() -> None:
    from munchhausen.domain.common import DecisionKind as K
    from munchhausen.domain.latches import FloorLatch
    from munchhausen.domain.pipeline_guard import PipelineRefused, check_floor

    check_floor("customers", {"st": {"$in": [2, 7]}}, collections=["customers", "accounts"])
    for coll, match, names in (("decisions", {}, ["customers"]), ("system.views", {}, ["system.views"]),
                               ("customers", {"$where": "1"}, ["customers"]),
                               ("customers", {"$expr": {"$function": {"body": "f"}}}, ["customers"])):
        with pytest.raises(PipelineRefused):
            check_floor(coll, match, collections=names)
    d = decision()
    bad = d.model_copy(update={"kind": K.FLOOR, "latches": (*d.latches,
                                                            FloorLatch(collection="customers", match={"$where": "1"}))})
    assert any("sandbox" in v for v in bad.l0_violations([]))


def test_cross_collection_reads_resolve_through_the_floor_view() -> None:
    from munchhausen.agent.execute import execute
    from munchhausen.domain.pipeline_guard import rewrite_targets

    vm = {"customers": "customers__D-1"}
    p = [{"$lookup": {"from": "customers", "as": "c", "pipeline": [{"$unionWith": "customers"}]}},
         {"$facet": {"a": [{"$unionWith": {"coll": "customers", "pipeline": []}}]}},
         {"$graphLookup": {"from": "customers", "startWith": "$a", "connectFromField": "a",
                           "connectToField": "b", "as": "g"}}]
    out = rewrite_targets(p, vm)
    assert out[0]["$lookup"]["from"] == "customers__D-1"
    assert out[0]["$lookup"]["pipeline"] == [{"$unionWith": "customers__D-1"}]
    assert out[1]["$facet"]["a"][0]["$unionWith"]["coll"] == "customers__D-1"
    assert out[2]["$graphLookup"]["from"] == "customers__D-1" and p[0]["$lookup"]["from"] == "customers"
    store = FakeStore()
    store.db.colls["customers__D-1"] = store.db.colls["customers"]
    prop = Proposal(collection="accounts", pipeline=[{"$unionWith": "customers"}, {"$count": "n"}],
                    answer_path="0.n", confidence=0.5, rationale="")
    run(execute(prop, vm, store.world(), max_time_ms=100))
    assert store.db.colls["accounts"].pipelines[-1][0] == {"$unionWith": "customers__D-1"}


def test_concurrent_episodes_raise_one_dispositive_fire_per_latch() -> None:
    store = FakeStore([decision()])
    fp, trace = forward(store, arm())
    run(fp.run(0, question(0)))

    async def both() -> None:
        await asyncio.gather(fp.run(2, question(2)), fp.run(4, question(4)), fp.run(6, question(6)))

    run(both())
    dispositive = [f for f in store.fires.rows.values() if f.role is FireRole.DISPOSITIVE]
    assert len(dispositive) == 1 and dispositive[0].id.endswith("-g0")
    assert trace.names().count("fire_raised") == 1


def test_episode_tokens_sum_the_calls_made_inside_it() -> None:
    from munchhausen.agent.usage import CURRENT_EPISODE

    class Counting(FakeModels):
        async def propose(self, inp: ProposerInput) -> Proposal:
            usage = CURRENT_EPISODE.get()
            assert usage is not None
            from munchhausen.impl.models_anthropic import current_episode_id
            assert current_episode_id() == usage.episode_id == "r:hooks:e0"   # spend meta.episode_id
            usage.add(100, 20)          # what the shared call path does per call
            return await super().propose(inp)

    store = FakeStore([decision()])
    fp, _ = forward(store, arm(), Counting())
    ep = run(fp.run(0, question(0)))      # propose + retry: two calls
    assert ep.tokens == {"in": 200, "out": 40, "calls": 2} and CURRENT_EPISODE.get() is None


def test_terms_are_scoped_to_their_run() -> None:
    terms = FakeTerms([])
    run(terms.add(Term(term=ACTIVE, source="question", admitted_at_idx=7, run_id="a.1")))
    run(terms.add(Term(term=ACTIVE, source="question", admitted_at_idx=3, run_id="a.1")))
    run(terms.add(Term(term="revenue", source="question", admitted_at_idx=0, run_id="b")))
    assert run(terms.extract("active customers and revenue", run_id="a.1")) == {ACTIVE}
    assert run(terms.extract("active customers and revenue", run_id="b")) == {"revenue"}
    assert terms.rows[0].runs == {"a_1": 3}
    seeded = seed_terms(SCHEMA, [question(i) for i in range(4)], min_questions=2, max_tokens=3, run_id="r9")
    assert {t.run_id for t in seeded} == {"r9"}


def test_hook_terms_match_regardless_of_case_and_spacing() -> None:
    d = decision(terms=("Active  Customers",))
    assert d.hook.matches(QuestionKeys(terms=frozenset({ACTIVE}), collections=frozenset(), persona=None))


def test_an_unparsed_pipeline_is_its_own_event_not_a_guard_refusal() -> None:
    store = FakeStore()
    fp, trace = forward(store, arm(), FakeModels(pipeline=[{"$unparsed": "not json"}]))
    ep = run(fp.run(0, question(0)))
    assert "proposal_unparsed" in trace.names() and "guard_refusal" not in trace.names()
    assert ep.error and "did not parse" in ep.error


def test_gold_reads_the_world_through_the_evaluation_side(settings_offline: Settings) -> None:
    from munchhausen.bootstrap import _EvaluationStore

    class S(FakeStore):
        def world_evaluation(self) -> str:
            return "unguarded"

    assert _EvaluationStore(S()).world() == "unguarded"  # type: ignore[arg-type]
    assert isinstance(_EvaluationStore(FakeStore()).world(), GuardedReader)  # type: ignore[arg-type]
    assert _EvaluationStore(FakeStore()).episodes is not None  # type: ignore[arg-type]
