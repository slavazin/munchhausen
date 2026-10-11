"""Shaping (M3a): observer contract, groupers + coherence guard, bar + direction read, the episodic pass's
disposition rules, nominator input bounds and supersede rule, and the nominator party's tool loop against a
fake world (prior row run and rejected; figures_reproduced computed from runs). All offline."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from munchhausen.config import Settings
from munchhausen.domain.common import DecisionKind, EvidenceState, FireRole, LifecycleStatus, Signature, emb_key
from munchhausen.domain.decision import Decision, EntryContract, Lifecycle, Option, Warrant
from munchhausen.domain.draft import DirectionRead, Draft, DraftStatus, LayerOutcome, Route, Verdict
from munchhausen.domain.episode import Episode, Residual
from munchhausen.domain.fire import Fire, FireCause
from munchhausen.domain.latches import Guard, HookLatch, KeySet, NotThisRow, RevisitLatch, WiringLatch
from munchhausen.domain.observation import (
    Observation,
    ObservationClass,
    ObservationDisposition,
    ObservationNote,
    Surfaces,
    Via,
)
from munchhausen.domain.registers import Term
from munchhausen.impl.grouper import AgglomerativeGrouper, SignatureBucketGrouper
from munchhausen.impl.parties import nominator as nominator_party
from munchhausen.impl.parties import observer as observer_party
from munchhausen.impl.representation import NoRepresentation
from munchhausen.learn.episodic import Bar, EpisodicPass, coherence_guard, presentation_filter, shape_of
from munchhausen.learn.nominate import Nominator
from munchhausen.learn.observe import Observer, masked
from munchhausen.lint_language import lint_draft_language, lint_noticed, parse_escape, tells
from munchhausen.ports import registry
from munchhausen.ports.grouper import Grouper
from munchhausen.ports.models import NominatorInput


def run(coro):  # noqa: ANN001, ANN201
    return asyncio.run(coro)


S = Settings(_env_file=None)


# --- fixtures --------------------------------------------------------------------------------------


def episode(eid: str, idx: int = 1, *, template: str = "t1", answer: Any = 100.0, figure: Any = 90.0,
            error: str | None = None, terms: tuple[str, ...] = ("active customers",), phrasing: str | None =
            "Finance counts active customers its own way.") -> Episode:
    return Episode(_id=eid, run_id="r", arm="a", idx=idx, question_id="q", text="How many active customers?",
                   template=template, persona="omar", terms=terms, world_version="v0", consulted=(),
                   collection="customers", pipeline=[{"$count": "n"}], answer_path="0.n", view_map={},
                   answer=answer, confidence=0.5, correct=False, figure=figure, phrasing=phrasing,
                   confirmed_figure=figure, error=error)


def obs(oid: str, eid: str, *, template: str = "t1", terms: tuple[str, ...] = ("active customers",),
        phrasing: str | None = "p", sig: Signature | None = Signature.EXCLUSION, delta: float = 10.0,
        emb: list[float] | None = None, persona: str = "omar") -> Observation:
    return Observation(_id=oid, run_id="r", arm="a", episode_id=eid, via=Via.OBSERVER, cls="reducible",
                       noticed="The count exceeds the figure by 11%.",
                       surfaces=Surfaces(terms=terms, collection="customers", phrasing=phrasing),
                       template=template, persona=persona, answer=100.0, figure=90.0, delta=delta,
                       signature_guess=sig, round=0, emb={emb_key("voyage-4"): emb} if emb else {})


def entry(*, supersedes: str | None = None, terms: tuple[str, ...] = ("active customers",)) -> EntryContract:
    return EntryContract(
        title="Active customers carry an open account", kind=DecisionKind.TAXONOMIC,
        payload="An active customer holds at least one account with status open.",
        options=(Option(definition="every customer document", verdict="rejected", prior=True),
                 Option(definition="customers with an open account", verdict="chosen",
                        figures_reproduced=("r:a:e1",))),
        forecloses="counts of every customer document",
        latches=(HookLatch(fires_when=KeySet(terms=terms, collections=("customers",)),
                           not_this=(NotThisRow(terms=("signup year",),
                                                contrast="a count of customers by signup year, every holder"),)),
                 RevisitLatch(id="T-pending-1", signature=Signature.EXCLUSION,
                              guard=Guard(min_residuals=2, window=30)),
                 WiringLatch.build(supersedes=supersedes)),
        residue="does not check how the status field is populated",
        warrant=Warrant(source_observation_ids=("o1",), source_episode_ids=("r:a:e1",), templates=2,
                        figures_reproduced=("r:a:e1",), falsifier="a dispositive fire on the revisit latch"))


def decision(did: str, state: EvidenceState) -> Decision:
    return Decision(_id=did, run_id="r", arm="a", **{f: getattr(entry(), f) for f in EntryContract.model_fields},
                    lifecycle=Lifecycle(status=LifecycleStatus.ADMITTED, at_idx=10), evidence_state=state)


# --- fakes -----------------------------------------------------------------------------------------


class Trace:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def begin(self, episode: dict[str, Any]) -> None: ...
    def signal(self, name: str, value: Any, comment: str | None = None) -> None: ...
    def finish(self, output: Any) -> None: ...

    def event(self, name: str, payload: dict[str, Any]) -> None:
        self.events.append((name, payload))

    def names(self) -> list[str]:
        return [n for n, _ in self.events]


class Observations:
    def __init__(self, rows: Sequence[Observation] = ()) -> None:
        self.rows = {o.id: o for o in rows}

    async def put(self, o: Observation) -> None:
        self.rows[o.id] = o

    async def get(self, oid: str) -> Observation | None:
        return self.rows.get(oid)

    async def open_for_pass(self, run_id: str, arm: str, *, since_round: int) -> list[Observation]:
        return [o for o in self.rows.values() if o.disposition is ObservationDisposition.OPEN
                and o.round >= since_round]

    async def dispose(self, ids: Sequence[str], disposition: ObservationDisposition, by: str) -> None:
        for i in ids:
            self.rows[i] = self.rows[i].model_copy(update={"disposition": disposition, "disposed_by": by})


class Episodes:
    def __init__(self, read: DirectionRead, consultations: Sequence[Episode] = ()) -> None:
        self.read, self.filters, self.got, self.windows = read, [], [], []
        self.consultations = list(consultations)

    async def get(self, eid: str) -> Episode | None:
        self.got.append(eid)
        return episode(eid, int(eid.rsplit(":e", 1)[-1]) if ":e" in eid else 1)

    async def direction_read(self, run_id: str, arm: str, inside: dict[str, Any], *, before_idx: int):  # noqa: ANN201
        self.filters.append((inside, before_idx))
        return self.read

    async def direction_read_window(self, run_id: str, arm: str, inside: dict[str, Any], *, before_idx: int,  # noqa: ANN201
                                    after_idx: int | None = None, last_n: int | None = None):
        self.filters.append((inside, before_idx))
        self.windows.append({"after_idx": after_idx, "last_n": last_n})
        return self.read

    async def consultations_of(self, run_id: str, arm: str, decision_id: str, last_n: int) -> list[Episode]:
        return self.consultations


class Fires:
    def __init__(self, rows: Sequence[Fire] = ()) -> None:
        self.rows = list(rows)

    async def open_for(self, decision_id: str) -> list[Fire]:
        return [f for f in self.rows if f.decision_id == decision_id]


class Drafts:
    def __init__(self) -> None:
        self.rows: dict[str, Draft] = {}

    async def put(self, d: Draft) -> None:
        self.rows[d.id] = d

    async def get(self, did: str) -> Draft | None:
        return self.rows.get(did)

    async def record(self, did: str, outcome: LayerOutcome) -> None:
        d = self.rows[did]
        self.rows[did] = d.model_copy(update={"adjudication": {**d.adjudication, outcome.layer: outcome}})

    async def set_status(self, did: str, status: DraftStatus) -> None:
        self.rows[did] = self.rows[did].model_copy(update={"status": status})

    async def held(self, run_id: str, arm: str) -> list[Draft]:
        return [d for d in self.rows.values() if d.status is DraftStatus.HELD]


class Terms:
    async def all(self, *, run_id: str | None = None) -> list[Term]:
        return [Term(term="active customers", source="schema", admitted_at_idx=0)]


class Decisions:
    def __init__(self, admitted: Sequence[Decision] = ()) -> None:
        self.rows = list(admitted)

    async def admitted(self, run_id: str, arm: str) -> list[Decision]:
        return self.rows

    async def get(self, did: str) -> Decision | None:
        return next((d for d in self.rows if d.id == did), None)


class Models:
    def __init__(self, notes: Sequence[ObservationNote] = (), nominated: EntryContract | None = None) -> None:
        self.notes, self.nominated = list(notes), nominated
        self.observe_calls, self.inputs = 0, []

    async def observe(self, ep: Episode) -> list[ObservationNote]:
        self.observe_calls += 1
        return self.notes

    async def nominate(self, inp: NominatorInput) -> tuple[EntryContract, tuple[str, ...]]:
        self.inputs.append(inp)
        return self.nominated or entry(), ()


class Adjudicator:
    def __init__(self, verdict: Verdict) -> None:
        self.verdict, self.seen = verdict, []

    async def adjudicate(self, draft: Draft, ctx) -> list[LayerOutcome]:  # noqa: ANN001
        self.seen.append((draft, ctx))
        return [LayerOutcome(layer="L4", role=None, verdict=self.verdict)]


class Rep:
    id, dim = "voyage-4", 2

    async def embed(self, texts: Sequence[str], role: str) -> np.ndarray:
        return np.ones((len(texts), 2), dtype=np.float32)


def note(text: str, cls: ObservationClass = ObservationClass.REDUCIBLE) -> ObservationNote:
    return ObservationNote(cls=cls, noticed=text, surfaces=Surfaces(terms=("active customers",),
                                                                    collection="customers", phrasing="paraphrase"))


# --- lint ------------------------------------------------------------------------------------------


def test_tells_are_case_aware() -> None:
    assert not tells("Revenue in US dollars per quarter.")
    assert tells("we count every customer")
    assert tells("I count every customer")
    assert not tells("Count in fiscal quarter II.")
    assert tells("The governed store holds it.")
    assert tells("Seen at episode #120.")


def test_noticed_refuses_fixes_and_long_text() -> None:
    assert not lint_noticed("The count of customers exceeds the figure by 3.1%. The pipeline counts every document.")
    assert any("fix" in p for p in lint_noticed("The pipeline should exclude closed accounts."))
    assert any("sentences" in p for p in lint_noticed("A. B. C. D."))


def test_escape_and_hook_vocabulary() -> None:
    assert parse_escape("other(fiscal quarter): how a question names a reporting period") == (
        "fiscal quarter", "how a question names a reporting period")
    assert parse_escape("fiscal quarter") is None
    e = entry(terms=("active customers", "fiscal quarter"))
    assert any("vocabulary" in p for p in lint_draft_language(e, ["active customers"], []))
    assert not lint_draft_language(e, ["active customers"], ["other(fiscal quarter): a reporting period"])


def test_bare_negation_contrast_is_refused() -> None:
    e = entry()
    hook = e.hook.model_copy(update={"not_this": (NotThisRow(terms=("x",), contrast="anything else"),)})
    bad = e.model_copy(update={"latches": (hook, *e.latches[1:])})
    assert any("contrast" in p for p in lint_draft_language(bad, ["active customers"], []))


# --- observer --------------------------------------------------------------------------------------


def test_observer_one_record_per_noticing_phrasing_verbatim_and_idempotent() -> None:
    store, models = Observations(), Models([note("The count exceeds the figure by 11%."),
                                            note("The window spans the calendar year.")])
    o = Observer(models, NoRepresentation(), store)
    out = run(o.observe(episode("r:a:e1"), 0))
    assert [x.id for x in out] == ["r:a:e1:o0", "r:a:e1:o1"]
    assert all(x.surfaces.phrasing == "Finance counts active customers its own way." for x in out)
    assert all(x.disposition is ObservationDisposition.OPEN and x.emb == {} for x in out)
    assert out[0].ratio == pytest.approx(100 / 90) and out[0].delta == pytest.approx(10.0)
    assert run(o.observe(episode("r:a:e1"), 0)) == [] and models.observe_calls == 1


def test_noise_filter_is_mechanical_for_execution_errors_and_empty_results() -> None:
    store, models = Observations(), Models([note("x.")])
    o = Observer(models, NoRepresentation(), store)
    out = run(o.observe(episode("r:a:e2", error="OperationFailure: bad stage"), 0))
    out += run(o.observe(episode("r:a:e3", answer=None), 0))
    assert models.observe_calls == 0
    assert all(x.cls is ObservationClass.IRREDUCIBLE and x.disposition is ObservationDisposition.NOISE for x in out)
    assert not any(lint_noticed(x.noticed) for x in out)


def test_model_irreducible_class_becomes_noise() -> None:
    o = Observer(Models([note("The answer path reads a missing key.", ObservationClass.IRREDUCIBLE)]),
                 NoRepresentation(), Observations())
    assert run(o.observe(episode("r:a:e4"), 0))[0].disposition is ObservationDisposition.NOISE


def test_lint_refusals_are_not_stored_and_are_traced() -> None:
    store, trace = Observations(), Trace()
    o = Observer(Models([note("We should exclude closed accounts."), note("The count exceeds the figure.")]),
                 NoRepresentation(), store, trace=trace)
    out = run(o.observe(episode("r:a:e5"), 0))
    assert len(out) == 1 and "observation.refused" in trace.names() and len(store.rows) == 1


def test_embedding_and_mask() -> None:
    o = Observer(Models([note("The customers count exceeds the figure.")]), Rep(), Observations(),
                 embed_mask="surfaces")
    out = run(o.observe(episode("r:a:e6"), 0))
    assert out[0].emb[emb_key("voyage-4")] == [1.0, 1.0] and out[0].rep == {"embedder_id": "voyage-4"}
    n = note("The customers count in t1 exceeds the figure.")
    assert masked(n.noticed, n, "t1") == "The _ count in _ exceeds the figure."


def test_observer_prompt_never_shows_the_retry_pipeline() -> None:
    ep = episode("r:a:e7").model_copy(update={"retry_pipeline": [{"$match": {"secret": 1}}]})
    assert "secret" not in observer_party.render(ep, S)
    wire = observer_party.NoteWire.model_validate(
        {"class": "reducible", "noticed": "n.", "terms": ["invented"], "collection": None, "fields": [],
         "signature_guess": None, "re_check_terms": []})
    assert observer_party.to_note(wire, ep).surfaces.terms == ("active customers",)


# --- groupers and the coherence guard ---------------------------------------------------------------


def test_signature_buckets_group_by_signature_direction_collection() -> None:
    rows = [obs("o1", "e1"), obs("o2", "e2", template="t2"), obs("o3", "e3", delta=-5.0),
            obs("o4", "e4", sig=Signature.DATE_OFFSET)]
    shapes = run(SignatureBucketGrouper().group(rows))
    assert sorted(s.observation_ids for s in shapes) == [("o1", "o2"), ("o3",), ("o4",)]
    assert isinstance(SignatureBucketGrouper(), Grouper)
    assert registry.resolve("grouper", "signature-buckets") is SignatureBucketGrouper


def test_agglomerative_clusters_vectors_and_buckets_the_rest() -> None:
    rows = [obs("o1", "e1", emb=[1.0, 0.0]), obs("o2", "e2", emb=[0.99, 0.05]),
            obs("o3", "e3", emb=[0.0, 1.0]), obs("o4", "e4"), obs("o5", "e5")]
    shapes = run(AgglomerativeGrouper("voyage-4", 0.35).group(rows))
    assert sorted(s.observation_ids for s in shapes) == [("o1", "o2"), ("o3",), ("o4", "o5")]


def test_guard_keeps_shared_terms_and_partitions_otherwise() -> None:
    a = [obs("o1", "e1", terms=("active customers", "accounts")), obs("o2", "e2", terms=("active customers",))]
    assert coherence_guard(shape_of(a), a)[0].terms == frozenset({"active customers"})
    b = [obs("o1", "e1", terms=("revenue",), phrasing="x"), obs("o2", "e2", terms=("revenue",), phrasing="y"),
         obs("o3", "e3", terms=("fiscal quarter",), phrasing="z", delta=-3.0, persona="dana"),
         obs("o4", "e4", terms=(), phrasing="w")]
    split = coherence_guard(shape_of(b), b)
    assert sorted(s.observation_ids for s in split) == [("o1", "o2"), ("o3",)]
    same_phrase = [obs("o1", "e1", terms=("a",), phrasing="p"), obs("o2", "e2", terms=("b",), phrasing="p")]
    assert len(coherence_guard(shape_of(same_phrase), same_phrase)) == 1


# --- the episodic pass -----------------------------------------------------------------------------


GAP = DirectionRead(misses_in=16, n_in=20, misses_out=20, n_out=100)
NO_GAP = DirectionRead(misses_in=4, n_in=20, misses_out=20, n_out=100)


def build(read: DirectionRead, verdict: Verdict, rows: Sequence[Observation], *, models: Models | None = None,
          admitted: Sequence[Decision] = (), fires: Fires | None = None, consultations: Sequence[Episode] = (),
          window: int | None = None, adjudicator: Any = None, holdout: int = 0, bar: Bar | None = None,
          ) -> tuple[EpisodicPass, Observations, Drafts, Trace, Models]:
    store, drafts, trace, models = Observations(rows), Drafts(), Trace(), models or Models()
    episodes = Episodes(read, consultations)
    nominator = Nominator(models=models, world=None, episodes=episodes, terms=Terms(),  # type: ignore[arg-type]
                          decisions=Decisions(admitted), representation=NoRepresentation(), similarity=None,  # type: ignore[arg-type]
                          neighbour_k=5, residual_window=10, trace=trace)
    p = EpisodicPass(observations=store, episodes=episodes, drafts=drafts, grouper=SignatureBucketGrouper(),
                     bar=bar or Bar.from_settings(S), nominator=nominator,
                     adjudicator=adjudicator or Adjudicator(verdict),
                     round_size=30, trace=trace, fires=fires, direction_window=window,
                     holdout_templates=holdout, min_templates_floor=S.bar_min_templates_floor, holdout_seed=7)
    return p, store, drafts, trace, models


ROWS = [obs("o1", "r:a:e1"), obs("o2", "r:a:e2", template="t2"), obs("o9", "r:a:e9", template="t3",
                                                                       sig=Signature.RATIO)]


def test_pass_nominates_cleared_shape_and_spends_on_admit() -> None:
    p, store, drafts, trace, models = build(GAP, Verdict.ADMIT, ROWS)
    rep = run(p.run("r", "a", 0))
    assert len(rep.drafts) == 1 and ("S-" in rep.refused[0][0] and rep.refused[0][1] == "bar")
    assert store.rows["o1"].disposition is ObservationDisposition.SPENT
    assert store.rows["o9"].disposition is ObservationDisposition.OPEN
    assert {"shape.formed", "bar.verdict", "bar.direction_read", "draft.written", "draft.adjudicated"} <= set(
        trace.names())
    written = dict(trace.events)["draft.written"]
    assert written["options"][0]["prior"] and written["figures_reproduced"] == ["r:a:e1"]
    assert p.episodes.filters[0] == ({"terms": {"$in": ["active customers"]}}, 30)
    # nominator input bounded to the shape
    assert {e.id for e in models.inputs[0].episodes} == {"r:a:e1", "r:a:e2"}
    # idempotent per (arm, round)
    store.rows["o1"] = store.rows["o1"].model_copy(update={"disposition": ObservationDisposition.OPEN})
    store.rows["o2"] = store.rows["o2"].model_copy(update={"disposition": ObservationDisposition.OPEN})
    assert run(p.run("r", "a", 0)).drafts == [] and len(models.inputs) == 1


def test_direction_read_refusal_leaves_observations_open() -> None:
    p, store, drafts, trace, _ = build(NO_GAP, Verdict.ADMIT, ROWS)
    rep = run(p.run("r", "a", 0))
    assert not rep.drafts and ("direction" in [r for _, r in rep.refused])
    assert store.rows["o1"].disposition is ObservationDisposition.OPEN
    read = dict(trace.events)["bar.direction_read"]
    assert read["n_in"] == 20 and read["gap"] == pytest.approx(0.0)


def test_hold_reopens_and_identical_evidence_is_not_renominated() -> None:
    p, store, drafts, _, models = build(GAP, Verdict.HOLD, ROWS)
    rep = run(p.run("r", "a", 0))
    (did,) = rep.drafts
    assert store.rows["o1"].disposition is ObservationDisposition.OPEN
    drafts.rows[did] = drafts.rows[did].model_copy(update={"status": DraftStatus.HELD})   # the adjudicator's act
    rep = run(p.run("r", "a", 1))
    assert not rep.drafts and ("held" in [r for _, r in rep.refused])
    store.rows["o3"] = obs("o3", "r:a:e3", template="t3")      # new evidence joins the held shape
    rep = run(p.run("r", "a", 2))
    assert len(rep.drafts) == 1 and drafts.rows[did].status is DraftStatus.REFUSED
    assert drafts.rows[did].adjudication["renominated"].detail["renominated_as"] == rep.drafts[0]
    assert len(models.inputs) == 2


def test_failed_nomination_is_traced_and_does_not_sink_the_round() -> None:
    class Boom(Models):
        async def nominate(self, inp):  # noqa: ANN001, ANN201
            raise RuntimeError("no draft")
    p, store, _, trace, _ = build(GAP, Verdict.ADMIT, ROWS, models=Boom())
    rep = run(p.run("r", "a", 0))
    assert rep.failed and "nomination.failed" in trace.names()
    assert store.rows["o1"].disposition is ObservationDisposition.OPEN


def test_supersede_only_against_a_contested_neighbour() -> None:
    clear, contested = decision("D-clear", EvidenceState.CLEAR), decision("D-hot", EvidenceState.CONTESTED)
    p, _, drafts, trace, _ = build(GAP, Verdict.ADMIT, ROWS, models=Models(nominated=entry(supersedes="D-clear")),
                                   admitted=[clear, contested])
    (did,) = run(p.run("r", "a", 0)).drafts
    assert drafts.rows[did].route is Route.NEW and drafts.rows[did].supersedes is None
    assert "draft.supersede_stripped" in trace.names()
    p, _, drafts, _, _ = build(GAP, Verdict.ADMIT, ROWS, models=Models(nominated=entry(supersedes="D-hot")),
                               admitted=[clear, contested])
    (did,) = run(p.run("r", "a", 0)).drafts
    d = drafts.rows[did]
    assert d.route is Route.SUPERSEDE and d.supersedes == "D-hot" and d.wiring.supersedes == "D-hot"
    assert all(lt.id.startswith("T-D-") for lt in d.revisits)


# --- the nominator party against a fake world ------------------------------------------------------


class World:
    """customers: 100 documents, 90 of them with an open account."""

    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []

    async def aggregate(self, collection: str, pipeline: list[dict[str, Any]], *, max_time_ms: int):  # noqa: ANN201
        self.calls.append(pipeline)
        assert pipeline[-1] == {"$limit": S.nominator_tool_max_rows}
        opened = any("$match" in st and st["$match"].get("status") == "open" for st in pipeline)
        return [{"n": 90 if opened else 100}]

    async def collection_names(self) -> list[str]:
        return ["customers"]

    async def find(self, *a: Any, **k: Any) -> list[dict[str, Any]]:
        return []


def tool(tid: str, name: str, payload: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tid, name=name, input=payload)


def agg(tid: str, option: str, eid: str, opened: bool) -> SimpleNamespace:
    pipe = ([{"$match": {"status": "open"}}] if opened else []) + [{"$count": "n"}]
    return tool(tid, "aggregate", {"collection": "customers", "pipeline_json": json.dumps(pipe),
                                   "answer_path": "0.n", "option": option, "episode_id": eid})


SUBMIT = {
    "title": "Active customers hold an open account", "kind": "taxonomic",
    "payload": "An active customer holds at least one account whose status is open.",
    "options": [{"label": "prior", "definition": "every customer document", "verdict": "rejected", "prior": True},
                {"label": "open", "definition": "customers with an open account", "verdict": "chosen",
                 "prior": False}],
    "forecloses": "counts of every customer document",
    "fires_when": {"terms": ["active customers"], "collections": ["customers"], "persona": None},
    "not_this": [{"terms": ["signup year"], "collections": [], "persona": None,
                  "contrast": "a count of customers by signup year, which counts every holder"}],
    "revisit_signature": "exclusion", "floor": None,
    "residue": "does not check how the status field is populated",
    "falsifier": "a dispositive fire on the revisit latch", "new_terms": [], "supersedes": None,
}


class Client:
    def __init__(self, turns: list[list[SimpleNamespace]]) -> None:
        self.turns, self.requests = turns, []
        self.messages = self

    async def create(self, **kw: Any) -> SimpleNamespace:
        self.requests.append(kw)
        content = self.turns[len(self.requests) - 1]
        return SimpleNamespace(content=content, stop_reason="tool_use",
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5))


class LLM:
    def __init__(self, client: Client) -> None:
        self.client, self.calls = client, []

    async def record_call(self, **kw: Any) -> None:
        self.calls.append(kw)


def party_input(world: World) -> NominatorInput:
    members = [obs("o1", "r:a:e1"), obs("o2", "r:a:e2", template="t2")]
    shape = shape_of(members)
    return NominatorInput(shape=shape, sources=members, episodes=[episode("r:a:e1"), episode("r:a:e2")],
                          vocabulary=["active customers"], world=world)  # type: ignore[arg-type]


def test_party_records_rejected_prior_and_computes_figures_reproduced() -> None:
    world = World()
    client = Client([
        [tool("s0", "submit_draft", SUBMIT)],                       # submitted before running anything
        [agg("a1", "prior", "r:a:e1", False)],                     # the prior convention, first
        [agg("a2", "open", "r:a:e1", True), agg("a3", "open", "r:a:e2", True)],
        [tool("s1", "submit_draft", SUBMIT)],
    ])
    llm = LLM(client)
    e, new_terms = run(nominator_party.run(llm, S, party_input(world)))  # type: ignore[arg-type]
    prior = next(o for o in e.options if o.prior)
    chosen = next(o for o in e.options if o.verdict == "chosen")
    assert prior.verdict == "rejected" and prior.figures_reproduced == ()
    assert chosen.figures_reproduced == ("r:a:e1", "r:a:e2") == e.warrant.figures_reproduced
    assert e.warrant.source_episode_ids == ("r:a:e1", "r:a:e2") and e.warrant.templates == 2
    assert e.revisits[0].guard == Guard(min_residuals=S.fire_min_residuals, window=S.fire_window)
    assert e.retire_latch is not None and new_terms == ()
    assert len(llm.calls) == 4 and all(c["stage"] == "nominate" for c in llm.calls)
    first_reply = client.requests[1]["messages"][2]["content"][0]
    assert first_reply["is_error"] and "run option 'prior' against episode" in first_reply["content"]
    assert client.requests[0]["output_config"] == {"effort": S.nominator_effort}
    assert client.requests[0]["model"] == S.nominator_model


def test_party_gives_up_after_the_turn_cap() -> None:
    s = Settings(_env_file=None, nominator_max_tool_turns=2)
    client = Client([[agg("a1", "explore", "", False)], [agg("a2", "explore", "", False)]])
    with pytest.raises(RuntimeError, match="no accepted draft"):
        run(nominator_party.run(LLM(client), s, party_input(World())))  # type: ignore[arg-type]


def test_party_refuses_a_supersede_of_a_clear_neighbour_and_a_leaked_figure() -> None:
    world = World()
    inp = party_input(world)
    session = nominator_party.Session.open(S, inp)
    run(session.aggregate({"collection": "customers", "pipeline_json": "[]", "answer_path": "0.n",
                           "option": "prior", "episode_id": "r:a:e1"}))
    run(session.aggregate({"collection": "customers", "pipeline_json": '[{"$match": {"status": "open"}}]',
                           "answer_path": "0.n", "option": "open", "episode_id": "r:a:e1"}))
    leaky = nominator_party.DraftWire.model_validate({**SUBMIT, "supersedes": "D-x",
                                                      "payload": "The count is 90 open customers."})
    problems = nominator_party.submission_problems(leaky, session)
    assert any("contested" in p for p in problems)
    ok = nominator_party.DraftWire.model_validate({**SUBMIT, "payload": "The count is 90 open customers."})
    assert any("source figure" in p for p in nominator_party.submission_problems(ok, session))


# --- review fixes ----------------------------------------------------------------------------------


def test_neighbour_residuals_show_no_figures_and_seen_episodes_are_recorded() -> None:
    res = Residual(id="x", decision_id="D-hot", answer=123.0, figure=456.0, ratio=0.27, delta=-333.0,
                   signature_match=True, attributable=True)
    assert nominator_party.residual_view(res) == {"signature_match": True, "attributable": True, "direction": "-"}
    consulted = [episode("r:a:e40").model_copy(update={"residuals": (res,)})]
    hot = decision("D-hot", EvidenceState.CONTESTED)
    p, _, drafts, _, models = build(GAP, Verdict.ADMIT, ROWS, admitted=[hot], consultations=consulted)
    (did,) = run(p.run("r", "a", 0)).drafts
    assert drafts.rows[did].nominator_seen_episode_ids == ("r:a:e1", "r:a:e2", "r:a:e40")
    rendered = nominator_party.render(models.inputs[0], [])
    assert "456" not in rendered and "123" not in rendered


def test_direction_read_windows_from_the_contested_neighbours_fire_and_drops_pre_drift_members() -> None:
    hot = decision("D-hot", EvidenceState.CONTESTED)
    fire = Fire(_id="F", run_id="r", arm="a", decision_id="D-hot", latch="T-D-hot-1", role=FireRole.DISPOSITIVE,
                cause=FireCause.RESIDUALS, episode_ids=("r:a:e305",), at_idx=320)
    rows = [obs("o1", "r:a:e100"), obs("o2", "r:a:e310", template="t2"), obs("o3", "r:a:e330", template="t3")]
    p, store, drafts, trace, models = build(GAP, Verdict.ADMIT, rows, admitted=[hot], fires=Fires([fire]),
                                            window=S.direction_window)
    rep = run(p.run("r", "a", 11))
    assert p.episodes.windows == [{"after_idx": 305, "last_n": None}]
    assert {o.id for o in models.inputs[0].sources} == {"o2", "o3"}
    assert store.rows["o1"].disposition is ObservationDisposition.OPEN and "shape.windowed" in trace.names()
    assert len(rep.drafts) == 1
    p, *_ = build(GAP, Verdict.ADMIT, ROWS, window=S.direction_window)
    run(p.run("r", "a", 0))
    assert p.episodes.windows == [{"after_idx": None, "last_n": S.direction_window}]


def test_adjudicator_exception_reopens_evidence_and_rerun_resumes_the_pending_draft() -> None:
    class Flaky:
        def __init__(self) -> None:
            self.calls = 0

        async def adjudicate(self, draft, ctx):  # noqa: ANN001, ANN201
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("backtest down")
            return [LayerOutcome(layer="L4", role=None, verdict=Verdict.ADMIT)]

    p, store, drafts, trace, models = build(GAP, Verdict.ADMIT, ROWS, adjudicator=Flaky())
    rep = run(p.run("r", "a", 0))
    assert rep.failed and "adjudication.failed" in trace.names()
    assert store.rows["o1"].disposition is ObservationDisposition.OPEN
    rep = run(p.run("r", "a", 0))
    assert rep.resumed and not rep.drafts and len(models.inputs) == 1
    assert store.rows["o1"].disposition is ObservationDisposition.SPENT


def test_guard_keeps_a_persona_shape_and_a_floor_shape_without_shared_terms() -> None:
    dana = [obs("o1", "e1", template="c1", terms=("revenue",), phrasing="x", persona="dana", delta=-0.4,
                sig=Signature.ROUNDING),
            obs("o2", "e2", template="c2", terms=("trades",), phrasing="y", persona="dana", delta=0.3,
                sig=Signature.ROUNDING)]
    assert len(coherence_guard(shape_of(dana), dana)) == 1
    assert presentation_filter(shape_of(dana)) == {"template": {"$in": ["c1", "c2"]}, "persona": "dana"}
    q3 = [obs(f"o{i}", f"e{i}", template=f"t{i}", terms=(t,), phrasing=f"p{i}", persona=p)
          for i, (t, p) in enumerate([("accounts", "omar"), ("account limit", "lee"), ("products", "kim")])]
    (shape,) = coherence_guard(shape_of(q3), q3)
    assert len(shape.templates) == 3


def test_held_partial_overlap_waits_and_l1_hold_needs_a_new_template() -> None:
    p, store, drafts, _, models = build(GAP, Verdict.HOLD, ROWS)
    (did,) = run(p.run("r", "a", 0)).drafts
    hold = LayerOutcome(layer="L1", role=None, verdict=Verdict.HOLD)
    drafts.rows[did] = drafts.rows[did].model_copy(update={"status": DraftStatus.HELD,
                                                           "adjudication": {"L1": hold}})
    store.rows["o3"] = obs("o3", "r:a:e3", template="t2")      # more evidence, no new template
    rep = run(p.run("r", "a", 1))
    assert not rep.drafts and "held" in [r for _, r in rep.refused]
    store.rows["o4"] = obs("o4", "r:a:e4", template="t3")      # a new template
    rep = run(p.run("r", "a", 2))
    assert len(rep.drafts) == 1 and drafts.rows[did].status is DraftStatus.REFUSED
    assert drafts.rows[did].adjudication["renominated"].detail["renominated_as"] == rep.drafts[0]
    assert len(models.inputs) == 2


def test_party_refuses_literal_figures_and_counts_only_runs_against_source_episodes() -> None:
    inp = party_input(World())
    session = nominator_party.Session.open(S, inp)
    text, err = run(session.aggregate({"collection": "customers", "pipeline_json": '[{"$project": {"n": 90}}]',
                                       "answer_path": "0.n", "option": "open", "episode_id": "r:a:e1"}))
    assert err and "literal" in text
    run(session.aggregate({"collection": "customers", "pipeline_json": "[]", "answer_path": "0.n",
                           "option": "prior", "episode_id": ""}))
    assert not session.ran("prior")
    assert [r["option"] for r in inp.run_log] == ["open", "prior"] and inp.run_log[1]["pipeline"] == []
    assert nominator_party.logical_collections(["customers", "customers__D-1", "system.views"]) == ["customers"]


def test_nominator_traces_every_world_tool_run() -> None:
    class Logging(Models):
        async def nominate(self, inp):  # noqa: ANN001, ANN201
            inp.run_log.append({"option": "prior", "episode_id": "r:a:e1", "pipeline": [], "answer": 100,
                                "reproduced": False, "error": None, "collection": "customers"})
            return entry(), ()

    p, _, _, trace, _ = build(GAP, Verdict.ADMIT, ROWS, models=Logging())
    run(p.run("r", "a", 0))
    assert dict(trace.events)["nominator.run"]["option"] == "prior"


def test_noise_provenance_and_empty_observer() -> None:
    trace = Trace()
    o = Observer(Models([note("The answer path reads a missing key.", ObservationClass.IRREDUCIBLE)]),
                 NoRepresentation(), Observations(), trace=trace)
    assert run(o.observe(episode("r:a:e8"), 0))[0].disposed_by == "observer"
    assert run(o.observe(episode("r:a:e9", error="X: y"), 0))[0].disposed_by == "noise_filter"
    o = Observer(Models([]), NoRepresentation(), Observations(), trace=trace)
    assert run(o.observe(episode("r:a:e10"), 0)) == [] and "observation.none" in trace.names()
    long = "OperationFailure: bad, full error: {'ok': 0, 'errmsg': 'bad'}"
    assert observer_party.short_error(long, S.error_prompt_chars) == "OperationFailure: bad"


# --- smoke-1 fixes ---------------------------------------------------------------------------------


def test_literal_figure_guard_matches_number_literals_by_value_only() -> None:
    lf = nominator_party.literal_figures
    figs = [1.0, 1204.0, 2.0]
    assert lf([{"$group": {"_id": None, "n": {"$sum": 1}}}, {"$limit": 2}], figs, S.leak_min_abs) == []
    assert lf([{"$match": {"birthdate": {"$gte": "1970-01-01T00:00:00Z"}, "code": "a1204b"}}], figs,
              S.leak_min_abs) == []
    assert lf([{"$project": {"n": {"$literal": 1204}}}], figs, S.leak_min_abs) == [1204.0]
    assert lf([{"$project": {"n": "1204"}}], figs, S.leak_min_abs) == [1204.0]
    assert lf([{"$match": {"flag": True}}], [1.0, 10.0], S.leak_min_abs) == []


def test_a_rejected_option_whose_run_failed_counts_and_a_missing_one_gets_a_short_instruction() -> None:
    class Failing(World):
        async def aggregate(self, collection, pipeline, *, max_time_ms):  # noqa: ANN001, ANN201
            if any("$bad" in st for st in pipeline):
                raise RuntimeError("OperationFailure: unknown stage, full error: {...}")
            return await super().aggregate(collection, pipeline, max_time_ms=max_time_ms)

    inp = party_input(Failing())
    session = nominator_party.Session.open(S, inp)
    text, err = run(session.aggregate({"collection": "customers", "pipeline_json": '[{"$bad": 1}]',
                                       "answer_path": "0.n", "option": "prior", "episode_id": "r:a:e1"}))
    assert err and "full error" not in text
    run(session.aggregate({"collection": "customers", "pipeline_json": '[{"$match": {"status": "open"}}]',
                           "answer_path": "0.n", "option": "open", "episode_id": "r:a:e1"}))
    wire = nominator_party.DraftWire.model_validate(SUBMIT)
    assert nominator_party.submission_problems(wire, session) == []
    extra = nominator_party.DraftWire.model_validate(
        {**SUBMIT, "options": [*SUBMIT["options"], {"label": "flag", "definition": "the active flag",
                                                    "verdict": "rejected", "prior": False}]})
    assert nominator_party.submission_problems(extra, session) == [
        "run option 'flag' against episode 'r:a:e1' or drop it"]


def test_hook_must_key_on_the_shapes_shared_terms() -> None:
    inp = party_input(World())
    assert inp.shape.terms == frozenset({"active customers"})
    session = nominator_party.Session.open(S, inp)
    for opt, flt in (("prior", "[]"), ("open", '[{"$match": {"status": "open"}}]')):
        run(session.aggregate({"collection": "customers", "pipeline_json": flt, "answer_path": "0.n",
                               "option": opt, "episode_id": "r:a:e1"}))
    off = nominator_party.DraftWire.model_validate(
        {**SUBMIT, "fires_when": {"terms": [], "collections": ["customers"], "persona": None}})
    assert any("shared terms" in p for p in nominator_party.submission_problems(off, session))


class CodedWorld:
    """A collection whose definition lives in a coded field (`k`) the question never names."""

    DOCS = [{"_id": i, "active": True, "k": 2 if i % 10 < 7 else 9, "name": f"c{i}"} for i in range(100)]

    async def aggregate(self, collection: str, pipeline: list[dict[str, Any]], *, max_time_ms: int):  # noqa: ANN201
        if pipeline and "$sample" in pipeline[0]:
            return self.DOCS[: pipeline[0]["$sample"]["size"]]
        match = next((st["$match"] for st in pipeline if "$match" in st), {})
        n = sum(all(d.get(k) == v for k, v in match.items()) for d in self.DOCS)
        return [{"n": n}]

    async def collection_names(self) -> list[str]:
        return ["customers", "customers__D-1"]

    async def find(self, *a: Any, **k: Any) -> list[dict[str, Any]]:
        return []


def test_replayed_q1_nomination_converges_with_profile_and_a_coded_field() -> None:
    """Offline replay of the smoke-1 failure: prior run, profile reveals the coded field, the candidate on it
    reproduces both figures, an errored rejected option still counts, submission accepted within the cap."""
    members = [obs("o1", "r:a:e1"), obs("o2", "r:a:e2", template="t2")]
    members = [m.model_copy(update={"answer": 100.0, "figure": 70.0}) for m in members]
    inp = NominatorInput(shape=shape_of(members), sources=members,
                         episodes=[episode("r:a:e1", figure=70.0), episode("r:a:e2", figure=70.0)],
                         vocabulary=["active customers"], world=CodedWorld())  # type: ignore[arg-type]

    def agg_(tid: str, option: str, eid: str, match: dict[str, Any]) -> SimpleNamespace:
        return tool(tid, "aggregate", {"collection": "customers", "answer_path": "0.n", "option": option,
                                       "episode_id": eid, "pipeline_json": json.dumps(
                                           [{"$match": match}, {"$count": "n"}])})

    submit = {**SUBMIT, "options": [
        {"label": "prior", "definition": "every customer with the active flag", "verdict": "rejected", "prior": True},
        {"label": "date-string", "definition": "active customers born after a date written as a string",
         "verdict": "rejected", "prior": False},
        {"label": "coded", "definition": "customers whose code field k equals 2", "verdict": "chosen",
         "prior": False}],
        "payload": "An active customer is a customer document whose code field k equals 2."}
    turns = [
        [agg_("a1", "prior", "r:a:e1", {"active": True})],
        [tool("p1", "profile", {"collection": "customers"})],
        [tool("a2", "aggregate", {"collection": "customers", "answer_path": "0.n", "option": "date-string",
                                  "episode_id": "r:a:e1", "pipeline_json": "[{\"$match\": {\"x\": 1}}]"})],
        [agg_("a3", "coded", "r:a:e1", {"k": 2}), agg_("a4", "coded", "r:a:e2", {"k": 2})],
        [tool("s1", "submit_draft", submit)],
    ]
    client = Client(turns)
    e, _ = run(nominator_party.run(LLM(client), S, inp))  # type: ignore[arg-type]
    assert len(client.requests) == 5 <= S.nominator_max_tool_turns == 20
    profile_reply = client.requests[2]["messages"][4]["content"][0]["content"]
    assert '"k"' in profile_reply and '"2": 70' in profile_reply
    chosen = next(o for o in e.options if o.verdict == "chosen")
    assert chosen.figures_reproduced == ("r:a:e1", "r:a:e2")
    assert "customers__D-1" not in client.requests[0]["messages"][0]["content"]


# --- held-out template fold (smoke-2) --------------------------------------------------------------


class Warranting(Models):
    """Fills the warrant from the input shape, as the party does."""

    def __init__(self, kind: DecisionKind = DecisionKind.TAXONOMIC) -> None:
        super().__init__()
        self.kind = kind

    async def nominate(self, inp: NominatorInput) -> tuple[EntryContract, tuple[str, ...]]:
        self.inputs.append(inp)
        e = entry()
        w = e.warrant.model_copy(update={"source_observation_ids": inp.shape.observation_ids,
                                         "source_episode_ids": inp.shape.episode_ids,
                                         "templates": len(inp.shape.templates)})
        return e.model_copy(update={"warrant": w, "kind": self.kind}), ()


FOUR = [obs("o1", "r:a:e1", template="t1"), obs("o2", "r:a:e2", template="t1"),
        obs("o3", "r:a:e3", template="t2"), obs("o4", "r:a:e4", template="t2"),
        obs("o5", "r:a:e5", template="t3"), obs("o6", "r:a:e6", template="t3"),
        obs("o7", "r:a:e7", template="t4")]


def test_four_template_shape_withholds_the_thinnest_template_from_the_nominator() -> None:
    from munchhausen.learn.backtest import population_filter

    models = Warranting()
    p, store, drafts, trace, _ = build(GAP, Verdict.REFUSE, FOUR, models=models, holdout=1)
    (did,) = run(p.run("r", "a", 0)).drafts
    d = drafts.rows[did]
    inp = models.inputs[0]
    assert {o.template for o in inp.sources} == {"t1", "t2", "t3"} and "r:a:e7" not in {e.id for e in inp.episodes}
    assert d.holdout_templates == ("t4",) and d.holdout_observation_ids == ("o7",)
    assert d.warrant.templates == 3 and "o7" not in d.warrant.source_observation_ids
    assert "r:a:e7" not in d.warrant.source_episode_ids and "r:a:e7" not in d.nominator_seen_episode_ids
    ctx = p.adjudicator.seen[0][1]
    assert {o.template for o in ctx.sources} == {"t1", "t2", "t3"}
    # S4's population: everything the warrant, the context and the nominator saw is excluded; t4 is not
    seen_ids = set(d.warrant.source_episode_ids) | {o.episode_id for o in ctx.sources} | set(
        d.nominator_seen_episode_ids)
    flt = population_filter(d.hook, exclude_ids=sorted(seen_ids), exclude_questions=[], after_idx=None)
    assert "r:a:e7" not in flt["_id"]["$nin"] and "r:a:e1" in flt["_id"]["$nin"]
    # the withheld observation follows the shape's disposition
    assert store.rows["o7"].disposition is ObservationDisposition.SPENT
    formed = dict(trace.events)["shape.formed"]
    assert formed["holdout_templates"] == ["t4"] and dict(trace.events)["draft.written"]["holdout_templates"] == ["t4"]


def test_two_template_shape_holds_nothing_out() -> None:
    p, _, drafts, _, models = build(GAP, Verdict.ADMIT, ROWS, holdout=1)
    (did,) = run(p.run("r", "a", 0)).drafts
    assert drafts.rows[did].holdout_templates == () and len(models.inputs[0].sources) == 2


def test_a_fold_that_would_break_the_bar_is_not_taken() -> None:
    rows = [obs("o1", "r:a:e1", template="t1"), obs("o2", "r:a:e2", template="t1"),
            obs("o3", "r:a:e3", template="t2"), obs("o4", "r:a:e4", template="t3")]
    bar = Bar(min_obs=4, min_templates=2, min_gap=S.bar_min_gap, min_matched=S.bar_min_matched)
    p, _, drafts, _, models = build(GAP, Verdict.ADMIT, rows, holdout=1, bar=bar, models=Warranting())
    (did,) = run(p.run("r", "a", 0)).drafts
    assert drafts.rows[did].holdout_templates == () and len(models.inputs[0].sources) == 4


def test_floor_draft_undoes_a_fold_that_leaves_fewer_than_the_floor_templates() -> None:
    rows = FOUR[:6] + [obs("o7", "r:a:e7", template="t4")]
    rows = [r for r in rows if r.template != "t3"]       # t1, t2, t4: the fold would leave 2 < 3
    p, _, drafts, trace, models = build(GAP, Verdict.ADMIT, rows, holdout=1,
                                        models=Warranting(DecisionKind.FLOOR))
    (did,) = run(p.run("r", "a", 0)).drafts
    d = drafts.rows[did]
    assert d.holdout_templates == () and d.warrant.templates == 3 and "o7" in d.source_observation_ids
    assert "r:a:e7" in d.nominator_seen_episode_ids and "holdout.undone" in trace.names()
    assert {o.template for o in p.adjudicator.seen[0][1].sources} == {"t1", "t2", "t4"}


def test_settings_fill_unset_knobs() -> None:
    p = EpisodicPass(observations=None, episodes=None, drafts=None, grouper=None, bar=Bar.from_settings(S),  # type: ignore[arg-type]
                     nominator=None, adjudicator=None, round_size=30, settings=S)  # type: ignore[arg-type]
    assert (p.holdout_templates, p.direction_window, p.min_templates_floor) == (
        S.holdout_templates, S.direction_window, S.bar_min_templates_floor)
