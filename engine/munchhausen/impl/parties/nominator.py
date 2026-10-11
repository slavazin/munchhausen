"""Nominator party (SPEC § 7.2 step 4, § 10.2). Owner: backward-pass shaping surface (M3).

A manual tool loop over `llm.client` (Anthropic tool use; no forced `tool_choice` on 5.5 models), with two
tools:
- `aggregate`: the read-only world tool (§ 20.2 fallback row: a Python aggregate over the world reader). Each
  run names the option it tests and the source episode whose figure it should reproduce; the harness reads
  the answer, compares it with that episode's figure and keeps the run log. `figures_reproduced` is computed
  from that log, never taken from the model's say-so: a definition reproduces a figure only if a run of it did.
- `submit_draft`: the entry contract as structured input. The harness validates it (prior option run and
  rejected, chosen option run, vocabulary/escape, contrasts, tells, L0's pure checks, supersede only against a
  contested neighbour) and returns the problems as a tool error until it passes or the turn cap is spent.

Every model call is recorded through `llm.record_call` (stage `nominate`). Turn and row caps are knobs.
Latch ids are placeholders (`T-pending-<k>`); `learn/nominate.py` rewrites them once the draft id exists.
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from munchhausen.agent.execute import ExecutionError, read_path
from munchhausen.config import Settings
from munchhausen.domain.common import Answer, DecisionKind, EvidenceState, Signature
from munchhausen.domain.decision import EntryContract, Option, Warrant
from munchhausen.domain.episode import Residual
from munchhausen.domain.latches import (
    FloorLatch,
    Guard,
    HookLatch,
    KeySet,
    MootWhen,
    NotThisRow,
    RetireLatch,
    RevisitLatch,
    WiringLatch,
    hook_reaches,
    why_unreached,
)
from munchhausen.domain.pipeline_json import decode_dates, parse_pipeline
from munchhausen.domain.question import QuestionKeys
from munchhausen.domain.scoring import matches
from munchhausen.impl.parties import LLM
from munchhausen.lint_language import lint_draft_language
from munchhausen.ports.models import NominatorInput

PENDING = "T-pending"
VIEW_SEP = "__"          # floor views are named <logical collection>__<decision id> (store/names.py)
REVISIT_K, RETIRE_K = 1, 2
STAGE = "nominate"

SYSTEM = """\
You nominate one decision for an analytics harness over a MongoDB world. You are given one shape: a group
of observations of missed answers that share a presentation, the episodes they came from (question,
pipeline, answer, and the stakeholder's confirmed figure), the term vocabulary, and the admitted decisions
nearest the shape with their recent residuals (where the current store loses).

Your job: generalize the shape into the decision that answers the question whose answer would settle every
observation in it, i.e. a definition or procedure that reproduces the confirmed figures, written so it
applies to future questions that present the same way.

Method (follow it in order):
1. Run the prior convention first. Use the aggregate tool to run the reading the pipelines already take
   (label the run with the prior option's label) against at least one source episode, and see which
   figures it fails to reproduce. This becomes a rejected option with prior: true.
2. Before proposing definitions, list the fields of the collection with their distinct small-cardinality
   values (the profile tool, or $group by field / $sortByCount). The definition may live in a field whose
   name does not name it: a coded field with a handful of values is as much a candidate as a field whose
   name matches the question's words.
3. Search for a definition that reproduces the source figures (label exploratory runs "explore"). Run each
   candidate against as many source episodes as you can; a definition counts as reproducing a figure only
   when a labelled run of it returned that figure. Never submit a definition you have not run. A rejected
   option whose run errored or read nothing still counts as run: it reproduced nothing.
4. Submit the entry with submit_draft.

Literal values must have the stored BSON type. A `date` field compares only with a date literal, written
in Extended JSON: {"$date": "2012-01-01T00:00:00Z"}. Never write new Date(...) or ISODate(...), and never
compare a date field with a string such as "2012-01-01" or "1995": it matches nothing. Date operators
($year, $month, $dateToString) also apply to date fields.

The entry contract:
- title: the decided constraint, at most 12 words, present tense. Never the deliberation, never a figure.
- payload: at most 60 words, a definition or procedure, present tense, naming fields and values. Never a
  question's answer value; no number equal to any source answer or figure.
- options: at least 2 rows: the prior convention (verdict rejected, prior true), the chosen definition
  (verdict chosen), and any other definitions you ran and rejected. Each label must match the labels
  you used on aggregate runs.
- forecloses: the answers this decision moves away from.
- hook: fires_when keyed on how a question PRESENTS: the shape's shared_terms when it has any (the words its
  questions arrive in), other vocabulary terms, the collections, a persona
  only if the shape is one persona's preference). Bias broad: a false match costs one
  considered-not-applicable; a miss is silent. Never key the hook on the decision's own conclusion.
  Recover precision with not_this rows; each row carries keys plus a contrast: one instantiated case the
  hook matches and must not bind (e.g. "a count of customers by signup year, which counts every account
  holder"), never a bare negation. A not_this row's keys must be ones the hook's own questions do NOT
  present (the source questions above must all still match the hook); its contrast names a question that
  lacks the decision's key concept.
- A hook term outside the vocabulary enters only through new_terms as "other(<term>): <presentation gloss>".
- revisit_signature: the residual signature a shift in the world would leave on this decision: set_member,
  ratio, date_offset, exclusion, threshold or rounding.
- kind: taxonomic (what a term means), procedural (how to compute), floor (a $match every pipeline on one
  collection must carry; give floor.collection and floor.match_json), preference (one persona's
  presentation), context_policy.
- residue: what enforcement does not check, named.
- falsifier: an observable event in the stores that would show this decision wrong.
- supersedes: only the id of a neighbour marked contested whose payload this decision reverses;
  otherwise null.

Language: present tense, impersonal. Never "the agent", "I", "we", "our", "us", "now", "currently",
"recently", "again", "so far", no run/arm/episode/round numbers, and none of the words governed, ungated,
naive, self_ref, frozen.
"""


# --- wire ------------------------------------------------------------------------------------------


class OptionWire(BaseModel):
    label: str
    definition: str
    verdict: Literal["chosen", "rejected"]
    prior: bool


class KeySetWire(BaseModel):
    terms: list[str]
    collections: list[str]
    persona: str | None = None


class NotThisWire(KeySetWire):
    contrast: str


class FloorWire(BaseModel):
    collection: str
    match_json: str


class DraftWire(BaseModel):
    title: str
    kind: DecisionKind
    payload: str
    options: list[OptionWire]
    forecloses: str
    fires_when: KeySetWire
    not_this: list[NotThisWire]
    revisit_signature: Signature
    floor: FloorWire | None = None
    residue: str
    falsifier: str
    new_terms: list[str]
    supersedes: str | None = None


DATE_LITERAL = 'dates as {"$date": "YYYY-MM-DDT00:00:00Z"}, never a string'


class AggregateWire(BaseModel):
    collection: str
    pipeline_json: str = Field(description=f"The aggregation pipeline as a strict JSON array of stages; "
                                           f"{DATE_LITERAL}")
    answer_path: str = ""
    option: str = "explore"
    episode_id: str = ""


class ProfileWire(BaseModel):
    collection: str


def _inline(schema: dict[str, Any]) -> dict[str, Any]:
    """Pydantic JSON Schema with `$defs` references inlined (tool input schemas stay self-contained)."""
    defs = schema.pop("$defs", {})

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(dict(defs[node["$ref"].rsplit("/", 1)[-1]]))
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)


TOOLS: list[dict[str, Any]] = [
    {
        "name": "aggregate",
        "description": (
            "Run a read-only MongoDB aggregation pipeline on one world collection and read the answer at "
            "answer_path ('0.total' = row 0, key total; '*.name' = a list over rows). Name the option the run "
            "tests (its label, or 'explore') and the source episode whose figure it should reproduce. The "
            "result reports the answer, that episode's figure and whether they match. Rows are capped. "
            f"Write {DATE_LITERAL}."),
        "input_schema": _inline(AggregateWire.model_json_schema()),
    },
    {
        "name": "profile",
        "description": (
            "List the fields of one world collection over a sample of its documents: each field's types, its "
            "number of distinct values in the sample, and the values with their counts when there are few. "
            "Use it before proposing definitions: a definition may live in a coded field whose name does not "
            "name it."),
        "input_schema": _inline(ProfileWire.model_json_schema()),
    },
    {
        "name": "submit_draft",
        "description": "Submit the entry contract. Problems come back as an error to fix and resubmit.",
        "input_schema": _inline(DraftWire.model_json_schema()),
    },
]


# --- the run log -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Run:
    option: str
    episode_id: str
    answer: Answer
    reproduced: bool
    error: str | None = None
    collection: str = ""
    pipeline: tuple[Any, ...] = ()
    refused: bool = False          # refused before running (a literal source figure): not evidence

    def row(self) -> dict[str, Any]:
        return {"option": self.option, "episode_id": self.episode_id, "collection": self.collection,
                "pipeline": list(self.pipeline), "answer": self.answer, "reproduced": self.reproduced,
                "error": self.error, "refused": self.refused}


_NUMERIC = re.compile(r"^\s*-?\d+(?:\.\d+)?\s*$")


def literal_figures(pipeline: Any, figures: Sequence[float], min_abs: float) -> list[float]:
    """JSON number literals (and fully numeric strings) in a pipeline equal by value to a source figure.
    Digits inside dates or other strings never match, and figures below `min_abs` in magnitude are ignored,
    so `$sum: 1`, `$limit: 2` and small codes pass."""
    targets = {float(f) for f in figures if abs(float(f)) >= min_abs}
    found: set[float] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            if float(node) in targets:
                found.add(float(node))
        elif isinstance(node, str) and _NUMERIC.match(node) and float(node) in targets:
            found.add(float(node))

    if targets:
        walk(pipeline)
    return sorted(found)


@dataclass
class Session:
    """State of one nomination: source figures by episode, and every world-tool run in order."""

    settings: Settings
    inp: NominatorInput
    figures: dict[str, Answer]
    runs: list[Run] = field(default_factory=list)

    @classmethod
    def open(cls, settings: Settings, inp: NominatorInput) -> Session:
        figures: dict[str, Answer] = {e.id: e.confirmed_figure for e in inp.episodes}
        for o in inp.sources:
            if o.figure is not None:
                figures[o.episode_id] = o.figure
        return cls(settings, inp, figures)

    def source_figures(self) -> list[float]:
        return [x for o in self.inp.sources for x in (o.answer, o.figure) if isinstance(x, (int, float))]

    def log(self, run: Run) -> None:
        self.runs.append(run)
        self.inp.run_log.append(run.row())

    async def aggregate(self, raw: dict[str, Any]) -> tuple[str, bool]:
        try:
            call = AggregateWire.model_validate(raw)
            pipeline, _repairs = parse_pipeline(call.pipeline_json)   # `$date` literals become dates
            if pipeline is None:
                raise ValueError("pipeline_json must be a JSON array of stages")
        except (ValidationError, ValueError) as e:
            return f"invalid call: {e}", True
        leaked = literal_figures(pipeline, self.source_figures(), self.settings.leak_min_abs)
        if leaked:   # a pipeline that writes the figure in reproduces nothing
            self.log(Run(call.option, call.episode_id, None, False, f"source figure as a literal: {leaked}",
                         call.collection, tuple(pipeline), refused=True))
            return f"refused: the pipeline contains a source figure as a literal: {leaked}", True
        capped = [*pipeline, {"$limit": self.settings.nominator_tool_max_rows}]
        try:
            rows = await self.inp.world.aggregate(call.collection, capped,
                                                  max_time_ms=self.settings.nominator_tool_max_time_ms)
        except Exception as e:   # driver and guard refusals are data for the model, not a crash
            err = short_error(f"{type(e).__name__}: {e}", self.settings.error_prompt_chars)
            self.log(Run(call.option, call.episode_id, None, False, err, call.collection, tuple(pipeline)))
            return err, True
        answer: Answer = None
        read_error = None
        if call.answer_path:
            try:
                answer = read_path(rows, call.answer_path)
            except ExecutionError as e:
                read_error = str(e)
        figure = self.figures.get(call.episode_id)
        reproduced = bool(call.episode_id) and matches(answer, figure, rel_tol=self.settings.score_rel_tol)
        self.log(Run(call.option, call.episode_id, answer, reproduced, read_error, call.collection,
                     tuple(pipeline)))
        body = {"rows": rows, "answer": answer, "answer_error": read_error,
                "episode_id": call.episode_id or None,
                "figure": figure if call.episode_id else None, "reproduced": reproduced}
        text = json.dumps(body, default=str)
        limit = self.settings.nominator_tool_result_chars
        return (text if len(text) <= limit else text[:limit] + " …(truncated)"), False

    def reproduced_by(self, label: str) -> tuple[str, ...]:
        return tuple(sorted({r.episode_id for r in self.runs if r.option == label and r.reproduced}))

    def ran(self, label: str) -> bool:
        """Run and read: a run against a source episode that read an answer (what a chosen option needs)."""
        return any(r.option == label and r.error is None and r.episode_id in self.figures
                   and r.answer is not None for r in self.runs)

    def attempted(self, label: str) -> bool:
        """Run against a source episode, whatever came back. A rejected option whose pipeline errored or
        read nothing reproduced nothing, which is the rejection's evidence. A run refused before execution
        is not."""
        return any(r.option == label and r.episode_id in self.figures and not r.refused for r in self.runs)

    def example_episode(self) -> str:
        return next(iter(sorted(self.figures)), "")

    async def profile(self, raw: dict[str, Any]) -> tuple[str, bool]:
        try:
            call = ProfileWire.model_validate(raw)
        except ValidationError as e:
            return f"invalid call: {e}", True
        st = self.settings
        try:
            docs = await self.inp.world.aggregate(call.collection, [{"$sample": {"size": st.nominator_profile_sample}}],
                                                  max_time_ms=st.nominator_tool_max_time_ms)
        except Exception as e:   # noqa: BLE001 - a refusal is data for the model
            return short_error(f"{type(e).__name__}: {e}", st.error_prompt_chars), True
        fields: dict[str, dict[str, Any]] = {}
        for d in docs:
            for k, v in d.items():
                if k == "_id":
                    continue
                f = fields.setdefault(k, {"types": set(), "values": Counter()})
                f["types"].add(type(v).__name__)
                if isinstance(v, (str, int, float, bool)) or v is None:
                    f["values"][json.dumps(v, default=str)] += 1
                else:
                    f["values"][f"<{type(v).__name__}>"] += 1
        out = {"collection": call.collection, "sampled": len(docs), "fields": {}}
        for k, f in sorted(fields.items()):
            vals: Counter[str] = f["values"]
            row: dict[str, Any] = {"types": sorted(f["types"]), "distinct_in_sample": len(vals)}
            if len(vals) <= st.nominator_profile_max_values:
                row["values"] = dict(vals.most_common())
            out["fields"][k] = row
        text = json.dumps(out, default=str)
        limit = st.nominator_tool_result_chars
        return (text if len(text) <= limit else text[:limit] + " …(truncated)"), False


# --- the entry -------------------------------------------------------------------------------------


def contested_neighbours(inp: NominatorInput) -> set[str]:
    return {d.id for d in inp.neighbours if d.evidence_state is EvidenceState.CONTESTED}


def build_hook(w: DraftWire) -> HookLatch:
    return HookLatch(
        fires_when=KeySet(terms=tuple(t.lower() for t in w.fires_when.terms),
                          collections=tuple(w.fires_when.collections), persona=w.fires_when.persona),
        not_this=tuple(NotThisRow(terms=tuple(t.lower() for t in r.terms), collections=tuple(r.collections),
                                  persona=r.persona, contrast=r.contrast) for r in w.not_this))


def build_entry(w: DraftWire, s: Session) -> EntryContract:
    st, shape = s.settings, s.inp.shape
    options = tuple(Option(definition=o.definition, figures_reproduced=s.reproduced_by(o.label),
                           verdict=o.verdict, prior=o.prior) for o in w.options)
    chosen = next((o for o in w.options if o.verdict == "chosen"), None)
    hook = build_hook(w)
    latches: list[Any] = [
        hook,
        RevisitLatch(id=f"{PENDING}-{REVISIT_K}", signature=w.revisit_signature,
                     guard=Guard(min_residuals=st.fire_min_residuals, window=st.fire_window)),
        RetireLatch(id=f"{PENDING}-{RETIRE_K}", moot_when=MootWhen(idle_episodes=st.retire_idle),
                    max_fires=st.retire_fires),
        WiringLatch.build(supersedes=w.supersedes),
    ]
    if w.floor is not None:
        match = decode_dates(json.loads(w.floor.match_json))
        latches.insert(2, FloorLatch(collection=w.floor.collection, match=match))
    warrant = Warrant(source_observation_ids=shape.observation_ids, source_episode_ids=shape.episode_ids,
                      templates=len(shape.templates),
                      figures_reproduced=s.reproduced_by(chosen.label) if chosen else (),
                      falsifier=w.falsifier)
    return EntryContract(title=w.title, kind=w.kind, payload=w.payload, options=options,
                         forecloses=w.forecloses, latches=tuple(latches), residue=w.residue, warrant=warrant)


def unreached_sources(w: DraftWire, s: Session) -> list[str]:
    """The hook must match every source question of its own shape (`hook_reaches`, the domain definition).
    A source it misses is refused, naming the blocking `not_this` row or the missing key."""
    hook = build_hook(w)
    keys = [QuestionKeys(terms=frozenset(e.terms), collections=frozenset(e.collections or (e.collection,)),
                         persona=e.persona) for e in s.inp.episodes]
    return [f"the hook does not reach source episode {s.inp.episodes[i].id!r} "
            f"({s.inp.episodes[i].text!r}): {why_unreached(hook, keys[i])}. A not_this row must use keys "
            "the hook's own questions do not present"
            for i in hook_reaches(hook, keys)]


def submission_problems(w: DraftWire, s: Session) -> list[str]:
    out: list[str] = []
    labels = [o.label for o in w.options]
    if len(w.options) < s.settings.nominator_min_options:
        out.append(f"options need at least {s.settings.nominator_min_options} rows")
    if len(set(labels)) != len(labels):
        out.append("option labels must be distinct")
    priors = [o for o in w.options if o.prior]
    if not priors or any(o.verdict != "rejected" for o in priors):
        out.append("one option must be the prior convention, with prior: true and verdict: rejected")
    chosen = [o for o in w.options if o.verdict == "chosen"]
    if len(chosen) != 1:
        out.append("exactly one option must be chosen")
    for o in w.options:
        done = s.ran(o.label) if o.verdict == "chosen" else s.attempted(o.label)
        if not done:
            out.append(f"run option {o.label!r} against episode {s.example_episode()!r} or drop it")
    shared = set(s.inp.shape.terms)
    if shared and not shared & {t.lower() for t in w.fires_when.terms}:
        out.append(f"key fires_when on the shape's shared terms: {sorted(shared)}")
    out += unreached_sources(w, s)
    if w.supersedes is not None and w.supersedes not in contested_neighbours(s.inp):
        out.append(f"supersedes {w.supersedes!r} is not a contested neighbour; set it to null")
    if w.floor is not None:
        try:
            if not isinstance(json.loads(w.floor.match_json), dict):
                out.append("floor.match_json must be a JSON object")
        except ValueError:
            out.append("floor.match_json must be valid JSON")
    if out:
        return out
    entry = build_entry(w, s)
    return (entry.l0_violations(s.source_figures(), s.settings.leak_min_abs)
            + lint_draft_language(entry, s.inp.vocabulary, w.new_terms))


# --- prompt ----------------------------------------------------------------------------------------


def residual_view(r: Residual) -> dict[str, Any]:
    """Where a neighbour loses, without its figures: answer, figure, ratio and delta of a neighbour's
    consultations would hand the nominator confirmed figures from the backtest population."""
    sign = None if r.delta is None else ("+" if r.delta > 0 else "-" if r.delta < 0 else "0")
    return {"signature_match": r.signature_match, "attributable": r.attributable, "direction": sign}


def logical_collections(names: list[str]) -> list[str]:
    """World collections as a question names them: floor views (`<coll>__<decision>`) and system
    collections are not logical collections."""
    return sorted(n for n in names if VIEW_SEP not in n and not n.startswith("system."))


def short_error(error: str, limit: int) -> str:
    """The driver's code and errmsg only: pymongo appends the full error document after ", full error:"."""
    return error.split(", full error:")[0][:limit]


def render(inp: NominatorInput, collections: list[str]) -> str:
    contested = contested_neighbours(inp)
    view = {
        "shape": {"id": inp.shape.id, "templates": sorted(inp.shape.templates),
                  "personas": sorted(inp.shape.personas), "shared_terms": sorted(inp.shape.terms)},
        "observations": [
            {"episode_id": o.episode_id, "template": o.template, "persona": o.persona, "noticed": o.noticed,
             "terms": list(o.surfaces.terms), "stakeholder_phrasing": o.surfaces.phrasing,
             "answer": o.answer, "figure": o.figure, "signature_guess": o.signature_guess,
             "retry_pipeline": o.retry_pipeline, "retry_correct": o.retry_correct}
            for o in inp.sources],
        "episodes": [
            {"episode_id": e.id, "question": e.text, "template": e.template, "persona": e.persona,
             "terms": list(e.terms), "collection": e.collection, "pipeline": e.pipeline,
             "answer_path": e.answer_path, "answer": e.answer, "confirmed_figure": e.confirmed_figure}
            for e in inp.episodes],
        "vocabulary": sorted(inp.vocabulary),
        "world_collections": collections,
        "neighbours": [
            {"id": d.id, "title": d.title, "kind": d.kind.value, "payload": d.payload,
             "fires_when": d.hook.fires_when.model_dump(mode="json"),
             "evidence_state": d.evidence_state.value, "contested": d.id in contested,
             "recent_residuals": [residual_view(r) for r in inp.neighbour_residuals.get(d.id, ())]}
            for d in inp.neighbours],
    }
    return ("Nominate the decision for this shape. Run the prior convention first.\n\n"
            + json.dumps(view, default=str, indent=1))


# --- the loop --------------------------------------------------------------------------------------


async def run(llm: LLM, settings: Settings, inp: NominatorInput) -> tuple[EntryContract, tuple[str, ...]]:
    session = Session.open(settings, inp)
    arm = inp.sources[0].arm if inp.sources else ""
    try:
        collections = logical_collections(await inp.world.collection_names())
    except Exception:  # noqa: BLE001 - a listing failure only removes a hint from the prompt
        collections = []
    messages: list[dict[str, Any]] = [{"role": "user", "content": render(inp, collections)}]
    last_problems: list[str] = []
    turns = settings.nominator_max_tool_turns
    for turn in range(turns):
        t0 = time.monotonic()
        try:
            resp = await llm.client.messages.create(
                model=settings.nominator_model, max_tokens=settings.nominator_max_tokens,
                system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
                tools=TOOLS, messages=messages, output_config={"effort": settings.nominator_effort})
        except Exception as e:   # a failed call is a spend row (evidence), then propagates
            await llm.record_error(stage=STAGE, arm=arm, model=settings.nominator_model, error=e,
                                   latency_ms=int((time.monotonic() - t0) * 1000), system=SYSTEM)
            raise
        await llm.record_call(stage=STAGE, arm=arm, model=settings.nominator_model, usage=resp.usage,
                              latency_ms=int((time.monotonic() - t0) * 1000), system=SYSTEM,
                              request_id=getattr(resp, "_request_id", None),
                              served_model=getattr(resp, "model", None))
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"{STAGE}: refusal")
        messages.append({"role": "assistant", "content": resp.content})
        results: list[dict[str, Any]] = []
        accepted: tuple[EntryContract, tuple[str, ...]] | None = None
        for block in resp.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            if block.name == "aggregate":
                text, is_error = await session.aggregate(dict(block.input))
            elif block.name == "profile":
                text, is_error = await session.profile(dict(block.input))
            elif block.name == "submit_draft":
                try:
                    wire = DraftWire.model_validate(block.input)
                    last_problems = submission_problems(wire, session)
                except ValidationError as e:
                    last_problems = [f"invalid entry: {e}"]
                if last_problems:
                    text, is_error = "Fix and resubmit:\n- " + "\n- ".join(last_problems), True
                else:
                    accepted = (build_entry(wire, session), tuple(wire.new_terms))
                    text, is_error = "accepted", False
            else:
                text, is_error = f"unknown tool {block.name!r}", True
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": text,
                            "is_error": is_error})
        if accepted is not None:
            return accepted
        remaining = turns - turn - 1
        note = (f"{remaining} turn(s) left. Submit the entry with submit_draft."
                if remaining <= 2 else "Continue; finish with submit_draft.")
        messages.append({"role": "user", "content": [*results, {"type": "text", "text": note}]})
    raise RuntimeError(f"{STAGE}: no accepted draft within {turns} turns; last problems: {last_problems}")
