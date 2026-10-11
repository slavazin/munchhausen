"""Observations: the episodic store's records (SPEC § 23.1, which amends § 7.1 and § 10.1)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from munchhausen.domain.common import Answer, Pipeline, Record, Signature, Value


class ObservationClass(StrEnum):
    REDUCIBLE = "reducible"       # a concept or definition
    IRREDUCIBLE = "irreducible"   # execution error, empty result, wrong answer_path, malformed syntax


class Via(StrEnum):
    OBSERVER = "observer"
    OWNER = "owner"
    INJECTION = "injection"
    ANOMALY = "anomaly"


class ObservationDisposition(StrEnum):
    OPEN = "open"
    SHAPED = "shaped"
    SPENT = "spent"
    NOISE = "noise"
    DROPPED = "dropped"
    MOOT = "moot"


class Surfaces(Value):
    terms: tuple[str, ...] = ()
    collection: str | None = None
    fields: tuple[str, ...] = ()
    phrasing: str | None = None   # the authority's phrasing, verbatim


class ReCheckWhen(Value):
    terms: tuple[str, ...] = ()
    templates: tuple[str, ...] = ()


class ObservationNote(Value):
    """What the observer model writes for one noticing. The harness wraps it into an `Observation`."""

    cls: ObservationClass = Field(alias="class")
    noticed: str
    surfaces: Surfaces
    signature_guess: Signature | None = None
    re_check_when: ReCheckWhen | None = None


class Observation(Record):
    episode_id: str                          # the anchor; required
    via: Via
    cls: ObservationClass = Field(alias="class")
    noticed: str
    surfaces: Surfaces
    template: str
    persona: str
    answer: Answer
    figure: Answer
    ratio: float | None = None
    delta: float | None = None
    pipeline: Pipeline = Field(default_factory=list)
    retry_pipeline: Pipeline | None = None
    retry_correct: bool | None = None
    signature_guess: Signature | None = None
    re_check_when: ReCheckWhen | None = None
    disposition: ObservationDisposition = ObservationDisposition.OPEN
    disposed_by: str | None = None
    round: int
    rep: dict[str, str] = Field(default_factory=dict)        # {embedder_id}
    emb: dict[str, list[float]] = Field(default_factory=dict)
