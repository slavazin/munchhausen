"""The forward pass's records: proposals, judgements, residuals, episodes (SPEC § 6, § 10.1)."""

from __future__ import annotations

from pydantic import Field

from munchhausen.domain.common import Answer, Disposition, Pipeline, Record, Value


class Consultation(Value):
    decision_id: str
    disposition: Disposition


class Proposal(Value):
    """The proposer contract (SPEC § 6.1). Wire formats for a model API live in `impl/`, not here."""

    collection: str                       # a logical collection; `execute` resolves it through tool access
    pipeline: Pipeline
    answer_path: str
    terms_used: tuple[str, ...] = ()
    consulted: tuple[Consultation, ...] = ()
    anomalies: tuple[str, ...] = ()
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    repairs: tuple[str, ...] = ()         # lenient rewrites applied to the pipeline text (domain/pipeline_json)


class Judgement(Value):
    """The world's verdict on a first attempt.

    `correct` is evaluation data. `figure` and `phrasing` are the authority's reply and reach the
    learner only in arms that receive the authority (SPEC § 5).
    """

    correct: bool
    figure: Answer = None
    phrasing: str | None = None


class Residual(Value):
    id: str
    decision_id: str
    answer: Answer
    figure: Answer
    ratio: float | None = None
    delta: float | None = None
    signature_match: bool
    attributable: bool


class Episode(Record):
    idx: int
    question_id: str
    text: str
    template: str
    persona: str
    terms: tuple[str, ...]
    world_version: str                    # evaluation-only
    consulted: tuple[Consultation, ...]
    collection: str
    pipeline: Pipeline
    answer_path: str
    view_map: dict[str, str]              # logical collection → resolved view, at execution time
    answer: Answer
    anomalies: tuple[str, ...] = ()
    confidence: float
    rationale: str = ""
    correct: bool                          # evaluation-only for arms without an authority
    figure: Answer = None
    phrasing: str | None = None
    confirmed_figure: Answer = None
    retry_pipeline: Pipeline | None = None
    retry_correct: bool | None = None
    residuals: tuple[Residual, ...] = ()
    error: str | None = None               # execution failure, if any (feeds the noise filter)
    tokens: dict[str, int] = Field(default_factory=dict)
    latency_ms: int = 0
    stream: str = "stream"                 # stream | v | injection
    collections: tuple[str, ...] = ()      # the template's logical collections: a replay rebuilds the Question
    v_at: int | None = None                # V episodes: stream index of their V point
    pipeline_repairs: tuple[str, ...] = ()  # the first attempt's pipeline text was repaired, not valid JSON


# Fields a learner in an arm without an authority must never read (SPEC § 5: self_ref self-grades).
# The Store's learner-facing reads project these away; see ports/store.py `EpisodeRepository`.
# (`retry_correct` is not here: the harness scores a retry against the authority's figure, never gold.)
EVALUATION_ONLY_FIELDS: frozenset[str] = frozenset({"correct", "world_version", "figure", "phrasing",
                                                     "confirmed_figure"})


def confirmed_figure(answer: Answer, judgement: Judgement) -> Answer:
    """The agent's answer if scored correct, otherwise the authority's figure (SPEC § 2)."""
    return answer if judgement.correct else judgement.figure
