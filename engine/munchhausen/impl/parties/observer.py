"""Observer party (SPEC § 7.1, § 23.1). Owner: backward-pass shaping surface (M3).

The system prompt is compiled from § 23.1 (the observer's contract) and LANGUAGE.md § 2/§ 5. The observer
sees one episode and nothing else (written blind). It is not shown the retry pipeline: a `noticed` written
beside the repair restates the repair, and a fix is the nominator's act.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from munchhausen.config import Settings
from munchhausen.domain.common import Signature
from munchhausen.domain.episode import Episode
from munchhausen.domain.observation import ObservationClass, ObservationNote, ReCheckWhen, Surfaces
from munchhausen.impl.parties import LLM

SYSTEM = """\
You write observations about one missed answer to an analytics question over a MongoDB world.
An observation is a noticing: it states where an answer and the expected figure part ways. It never
states a fix.

The record you write, per noticing:
- class: "irreducible" when the miss is mechanical (execution error, empty result, wrong answer path,
  malformed pipeline); "reducible" when it concerns a concept or a definition (who counts, which period,
  which field, which unit).
- noticed: 1-3 sentences, present tense, impersonal. State the surface (the population, the field, the
  period) and the gap (the answer against the figure, as a ratio or a difference). Quote no definition.
- terms: the presentation terms the miss sits on, chosen from the question's presented terms when they
  are listed (lower-case noun phrases, e.g. "active customers", "fiscal quarter").
- collection and fields: where the gap sits.
- signature_guess: one of set_member, ratio, date_offset, exclusion, threshold, rounding, or null.
- re_check_terms: presentation terms the same gap should recur on; empty if none.

Rules:
- Noticing only. Never write what the pipeline should do ("should", "must", "instead of", "exclude ...").
  Never guess a definition. A fix is written later, from many observations, by someone else.
- One noticing per record. A miss that touches two surfaces gets two records; most misses get one.
- Do not restate the stakeholder's phrasing as a finding; it is stored verbatim beside your record.
- Never name a party or a moment: no "the agent", "I", "we", "our", "us", "now", "currently",
  "recently", "again", "so far", no run, arm or episode numbers, and none of the words governed, ungated,
  naive, self_ref, frozen.

Good: "The count of customers for 2016 exceeds the figure by 3.1%. The pipeline counts every customer
document."
Good: "The quarterly sum for Q1 2015 differs from the figure by the sum of one calendar month of trades.
The pipeline windows Q1 as January to March."
Bad: "The agent should exclude customers with src k7." (a fix, a leaked definition)
Bad: "Wrong answer on active customers." (no surface, no gap)
"""


class NoteWire(BaseModel):
    cls: Literal["reducible", "irreducible"] = Field(alias="class")
    noticed: str
    terms: list[str]
    collection: str | None
    fields: list[str]
    signature_guess: Signature | None
    re_check_terms: list[str]

    model_config = {"populate_by_name": True}


class ObservationWire(BaseModel):
    notes: list[NoteWire]


def short_error(error: str | None, limit: int) -> str | None:
    """The driver's code and errmsg only: pymongo appends the full error document after ", full error:"."""
    if error is None:
        return None
    return error.split(", full error:")[0][:limit]


def norm(term: str) -> str:
    return " ".join(term.lower().split())


def render(episode: Episode, settings: Settings) -> str:
    """The episode as the observer reads it: the question, the attempt, the gap. No other record."""
    view = {
        "question": episode.text,
        "template": episode.template,
        "persona": episode.persona,
        "presented_terms": list(episode.terms),
        "collection": episode.collection,
        "pipeline": episode.pipeline,
        "answer_path": episode.answer_path,
        "answer": episode.answer,
        "execution_error": short_error(episode.error, settings.error_prompt_chars),
        "expected_figure": episode.figure,
        "stakeholder_phrasing": episode.phrasing,
    }
    return "Write the observations for this miss.\n\n" + json.dumps(view, default=str, indent=1)


def to_note(w: NoteWire, episode: Episode) -> ObservationNote:
    presented = {norm(t) for t in episode.terms}
    terms = [norm(t) for t in w.terms if t.strip()]
    if presented:   # keep the shared vocabulary: terms the question did not present fall back to its own
        terms = [t for t in terms if t in presented] or sorted(presented)
    known = {episode.collection, *episode.collections}
    collection = w.collection if w.collection in known else episode.collection
    return ObservationNote(
        cls=ObservationClass(w.cls), noticed=w.noticed.strip(),
        surfaces=Surfaces(terms=tuple(dict.fromkeys(terms)), collection=collection,
                          fields=tuple(w.fields), phrasing=episode.phrasing),
        signature_guess=w.signature_guess,
        re_check_when=ReCheckWhen(terms=tuple(w.re_check_terms)) if w.re_check_terms else None,
    )


async def run(llm: LLM, settings: Settings, episode: Episode) -> list[ObservationNote]:
    wire = await llm.parse(stage="observe", arm=episode.arm, model=settings.observer_model, system=SYSTEM,
                           user=render(episode, settings), wire=ObservationWire,
                           max_tokens=settings.observer_max_tokens)
    return [to_note(w, episode) for w in wire.notes]
