"""Proposer party (SPEC § 6.1; consultation language, LANGUAGE.md § 6). Owner: forward-pass surface (M2).

The system prompt is the always-loaded set: the role, the tool contract and the schema summary. It holds
nothing learned, so its hash is stable across a run. Consulted decisions arrive in the user turn, framed in
consultation language: each one is presumed to hold and is applied wherever its hook matched; the proposer
reports one disposition per decision through `consulted[]`, never a bare assurance.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any

from pydantic import BaseModel, Field

from munchhausen.config import Settings
from munchhausen.domain.common import Answer, Disposition
from munchhausen.domain.decision import Decision
from munchhausen.domain.episode import Consultation, Proposal
from munchhausen.domain.pipeline_json import parse_pipeline
from munchhausen.domain.question import SchemaSummary
from munchhausen.impl.parties import LLM
from munchhausen.ports.models import ProposerInput

log = logging.getLogger(__name__)


class ProposalWire(BaseModel):
    """Pipeline travels as a JSON string: arbitrary-key objects don't fit strict structured output."""

    collection: str = Field(description="One logical collection named in the schema summary")
    pipeline_json: str = Field(description="The aggregation pipeline as a strict JSON array of stages; dates "
                                           "as {\"$date\": \"YYYY-MM-DDT00:00:00Z\"}")
    answer_path: str = Field(description="Where the answer sits in the result rows: `0.<field>` for a number in "
                                         "the first row, `*.<field>` for a list over rows")
    terms_used: list[str]
    consulted: list[Consultation] = Field(description="One entry per consulted decision, by id")
    anomalies: list[str] = Field(description="Data that contradicts an applied decision; empty when none")
    confidence: float = Field(description="Probability in [0, 1] that the answer is the figure expected")
    rationale: str = Field(description="At most two sentences")

    def to_domain(self, consulted_ids: list[str]) -> Proposal:
        pipeline, repairs = _pipeline(self.pipeline_json)
        return Proposal(collection=self.collection, pipeline=pipeline,
                        answer_path=self.answer_path, terms_used=tuple(self.terms_used),
                        consulted=_dispositions(self.consulted, consulted_ids), anomalies=tuple(self.anomalies),
                        confidence=min(max(self.confidence, 0.0), 1.0), rationale=self.rationale, repairs=repairs)


TOOL_CONTRACT = """\
You answer analytics questions over a MongoDB database by writing one aggregation pipeline.

Tool contract:
- Name one logical collection from the schema summary in `collection`; the pipeline runs against it, read-only.
- `pipeline_json` is a JSON array of stages in strict JSON: double-quoted keys and strings, no comments, no
  shell helpers. Allowed stages: $match, $project, $addFields, $set, $unset,
  $group, $sort, $limit, $skip, $unwind, $count, $lookup, $graphLookup, $unionWith, $facet, $bucket,
  $bucketAuto, $sortByCount, $replaceRoot, $replaceWith, $sample, $densify, $fill, $setWindowFields.
  $lookup, $graphLookup and $unionWith reach only collections in the schema summary. Writing stages,
  server-side JavaScript ($where, $function, $accumulator) and introspection stages are refused.
- Literal values must have the stored BSON type. A `date` field compares only with a date literal, written
  in Extended JSON: {"$date": "2012-01-01T00:00:00Z"}. Never write new Date(...) or ISODate(...), and never
  compare a date field with a string such as "2012-01-01": it matches nothing. Date operators ($year,
  $month, $dateToString) also apply to date fields. String comparison is exact and case-sensitive: match
  the stored values (the schema summary lists the values of some fields and notes lowercase text).
- A field typed `array<object>` holds subdocuments, listed under dotted paths (`items.price` is the
  `price` of each element of `items`). To count, filter or sum elements, {"$unwind": "$items"} first and
  then filter on `items.<field>`; a $match before the $unwind keeps whole documents in which any element
  matches, so repeat the element conditions after it.
- A `string` field noted `numbers stored as text` converts with $toDouble, never $toInt: $toInt fails the
  whole pipeline on decimal text. A number answer is a number, not a string.
- The pipeline runs with a time limit; a result past the row cap is refused. Aggregate to the answer.
- `answer_path` reads the answer from the result rows: `<row>.<field>`, where <row> is a row index and
  <field> is a field (dotted for nested fields) of that row; `*.<field>` reads the field from every row as
  a list of names. Examples: after {"$count": "n"} the path is `0.n`; after
  {"$group": {"_id": null, "total": {"$sum": "$x"}}} it is `0.total`; after
  {"$group": {"_id": "$name"}} a list of names is `*._id`. A result with no rows is an error: when a
  pipeline returns nothing, a filter has not matched the stored values or types.
- `confidence` is the probability that the answer equals the figure the asker expects.
- `rationale` is at most two sentences.
- `anomalies` lists values in the data that contradict a consulted decision you applied (for example, values
  of a field outside the set the decision names). Leave it empty when nothing contradicts one.

Consulted decisions:
- A question may arrive with consulted decisions: admitted definitions and procedures of this organisation,
  each reached because its hook matched how the question presents. Apply each consulted decision whose
  hook matched; it states how this organisation counts, and it holds over the conventional reading.
- Report every consulted decision in `consulted`, by id, with one disposition: `applied` when the pipeline
  follows it, `considered-not-applicable` when the question falls outside what it defines. A decision that
  is not reported is a reporting error."""


def system_prompt(schema: SchemaSummary) -> str:
    """The always-loaded set (SPEC § 6.2): the tool contract and the schema summary. Nothing learned."""
    lines = [TOOL_CONTRACT, "", "Schema summary (logical collection → field: type [note]):"]
    for coll, fields in sorted(schema.collections.items()):
        notes = schema.notes.get(coll, {})
        lines.append(f"- {coll}: " + ", ".join(f"{f}: {t}" + (f" [{notes[f]}]" if f in notes else "")
                                               for f, t in fields.items()))
    return "\n".join(lines)


def user_prompt(inp: ProposerInput) -> str:
    q = inp.question
    parts = [f"Question (asked by {q.persona}): {q.text}",
             f"Collections the question concerns: {', '.join(q.collections)}"]
    if inp.consulted:
        parts += ["", f"Consulted decisions ({len(inp.consulted)}). Apply each one whose hook matched:"]
        parts += [_render(d) for d in inp.consulted]
    else:
        parts += ["", "Consulted decisions: none."]
    if inp.retry_figure is not None:
        parts += ["", f"The asker expected {_figure(inp.retry_figure)}."]
        if inp.retry_phrasing:
            parts.append(f"The asker said: \"{inp.retry_phrasing}\"")
        parts.append("Write the pipeline that reproduces the expected figure from the data.")
    return "\n".join(parts)


async def run(llm: LLM, settings: Settings, inp: ProposerInput) -> Proposal:
    """`temperature` reaches `LLM.parse` when it accepts one. anthropic 1.13's `messages.parse` has no
    sampling parameters, so the shared call path must send it as `extra_body={"temperature": t}` (verified
    live on claude-haiku-4-5)."""
    kwargs: dict[str, Any] = {}
    if _accepts(llm, "temperature"):
        kwargs["temperature"] = settings.proposer_temperature
    elif not getattr(run, "_warned", False):
        log.warning("LLM.parse takes no `temperature`; PROPOSER_TEMPERATURE=%s is not applied",
                    settings.proposer_temperature)
        run._warned = True  # type: ignore[attr-defined]
    wire = await llm.parse(stage=inp.stage, arm=inp.arm, model=settings.proposer_model,
                           system=system_prompt(inp.schema), user=user_prompt(inp), wire=ProposalWire,
                           max_tokens=settings.proposer_max_tokens, **kwargs)
    return wire.to_domain([d.id for d in inp.consulted])


# --- mapping -----------------------------------------------------------------------------------------


def _render(d: Decision) -> str:
    return f"- [{d.id}] {d.title}\n  {d.payload}"


def _figure(f: Answer) -> str:
    return ", ".join(f) if isinstance(f, list) else f"{f}"


def _pipeline(raw: str) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    """(stages, repairs). Extended JSON dates decode to dates; text that is not strict JSON gets the lenient
    repairs of `domain/pipeline_json`, recorded by name on the proposal. A pipeline that still does not
    parse becomes one unknown stage, so the sandbox refuses it at execute and the miss is classified
    irreducible (the episode keeps the raw text for the observer)."""
    stages, repairs = parse_pipeline(raw)
    return ([{"$unparsed": raw}] if stages is None else stages), repairs


def _dispositions(reported: list[Consultation], consulted_ids: list[str]) -> tuple[Consultation, ...]:
    """One disposition per consulted decision, in consultation order. Ids the proposer invented are dropped;
    a consulted decision it left unreported is recorded `considered-not-applicable` (no residual is ever
    attributed to a decision the proposer did not say it applied)."""
    by_id = {c.decision_id: c.disposition for c in reported}
    return tuple(Consultation(decision_id=i, disposition=by_id.get(i, Disposition.CONSIDERED_NOT_APPLICABLE))
                 for i in consulted_ids)


def _accepts(llm: LLM, name: str) -> bool:
    try:
        params = inspect.signature(llm.parse).parameters
    except (TypeError, ValueError):
        return False
    return name in params or any(p.kind is p.VAR_KEYWORD for p in params.values())
