"""Invariants of the learning design (the M0 adversarial review): the gate's ablation, lessons, the lens
panel in record mode, the revisit guard, the nominator's inputs, one quirk per question, the direction
read, and paired readings."""

from __future__ import annotations

import asyncio

import pytest

from munchhausen.domain.common import DecisionKind, LayerRole
from munchhausen.domain.draft import DirectionRead, Draft, Shape, Verdict
from munchhausen.domain.episode import Episode, Residual
from munchhausen.domain.latches import Guard
from munchhausen.domain.lens import LensWeights
from munchhausen.domain.lesson import Lesson, lesson_entry
from munchhausen.domain.observation import Observation, Surfaces, Via
from munchhausen.learn.curators import governed, ungated
from munchhausen.learn.episodic import Bar, presentation_filter
from munchhausen.learn.layers import DirectAdmit, L3Lenses, LessonShape
from munchhausen.loop.residuals import guard_holds
from munchhausen.metrics.paired import paired_difference
from munchhausen.ports.curation import CurationContext
from munchhausen.ports.models import NominatorInput
from munchhausen.world.questions import QuestionBank, Template, hidden_quirks


def run(coro):  # noqa: ANN001, ANN201
    return asyncio.run(coro)


def obs(oid: str, episode: str, answer: float = 100.0, figure: float = 90.0) -> Observation:
    return Observation(_id=oid, run_id="r", arm="a", episode_id=episode, via=Via.OBSERVER, cls="reducible",
                       noticed="The count exceeds the figure.", surfaces=Surfaces(terms=("customers",)),
                       template="t1", persona="omar", answer=answer, figure=figure, round=1)


def episode(eid: str, idx: int, residuals: tuple[Residual, ...]) -> Episode:
    return Episode(_id=eid, run_id="r", arm="a", idx=idx, question_id="q", text="x", template="t1",
                   persona="omar", terms=(), world_version="v0", consulted=(), collection="c", pipeline=[],
                   answer_path="0.n", view_map={}, answer=1.0, confidence=0.5, correct=False, residuals=residuals)


def residual(rid: str, delta: float, *, attributable: bool = True, sig: bool = True) -> Residual:
    return Residual(id=rid, decision_id="D", answer=0.0, figure=0.0, delta=delta,
                    signature_match=sig, attributable=attributable)


# --- the gate's ablation ------------------------------------------------------------------------------


class _Layer:
    def __init__(self, name: str, role: LayerRole | None) -> None:
        self.name, self.role = name, role


def test_ungated_is_reported_ungoverned_and_governed_is_not() -> None:
    l0 = _Layer("L0", None)
    assert not ungated(l0).governed
    assert governed(l0, _Layer("L1", None), _Layer("L2", LayerRole.ROUTING),
                    _Layer("L3", LayerRole.CORROBORATING), _Layer("L4", LayerRole.DISPOSITIVE)).governed


# --- lessons --------------------------------------------------------------------------------------------


def _lesson_draft(payload: str) -> Draft:
    entry = lesson_entry(Lesson(title="Active customers exclude status code four", kind=DecisionKind.TAXONOMIC,
                                payload=payload),
                         terms=("active customers",), collections=("customers",),
                         observation_ids=("o1",), episode_ids=("e1",), templates=1)
    return Draft(_id="d", run_id="r", arm="a", shape_id="L-o1", source_observation_ids=("o1",), round=1,
                 **entry.model_dump())


def test_a_lesson_passes_its_own_l0_and_fails_the_entry_contract() -> None:
    draft = _lesson_draft("Count customers whose st field holds 2 or 7.")
    ctx = CurationContext(run_id="r", arm="a", at_idx=0, sources=(obs("o1", "e1"),))
    assert run(LessonShape().check(draft, ctx)).verdict is Verdict.PASS
    assert draft.l0_violations([]), "the entry-contract L0 would refuse every lesson"
    leaky = _lesson_draft("Active customers number 90 in total.")
    assert run(LessonShape().check(leaky, ctx)).verdict is Verdict.REFUSE
    assert run(DirectAdmit().check(draft, ctx)).verdict is Verdict.ADMIT


# --- L3 records by default -------------------------------------------------------------------------------


class _Panel:
    id = "fixed"

    async def score(self, draft, sources, neighbours):  # noqa: ANN001, ANN201
        return {"generalizes": 0.05}


class _Weights:
    async def current_weights(self) -> LensWeights:
        return LensWeights(version=0, weights={"generalizes": 1.0})


@pytest.mark.parametrize(("mode", "verdict"), [("record", Verdict.PASS), ("gate", Verdict.REFUSE)])
def test_l3_records_below_threshold_and_gates_only_when_asked(mode: str, verdict: Verdict) -> None:
    layer = L3Lenses(panel=_Panel(), weights=_Weights(), mode=mode, threshold=0.5, explore_eps=0.0, seed=7)
    out = run(layer.check(_lesson_draft("Count customers by st."), CurationContext("r", "a", 0, ())))
    assert out.verdict is verdict and out.score is not None and out.score < 0.5


# --- the revisit guard -------------------------------------------------------------------------------------


def test_guard_needs_attributable_signature_matched_residuals_that_agree_in_direction() -> None:
    g = Guard(min_residuals=2, window=30)
    scattered = [episode("e1", 1, (residual("r1", -5.0),)), episode("e2", 2, (residual("r2", +5.0),))]
    assert not guard_holds(scattered, "D", g)[0]          # poison-like: opposite directions
    unsigned = [episode("e1", 1, (residual("r1", -5.0, sig=False),)), episode("e2", 2, (residual("r2", -3.0),))]
    assert not guard_holds(unsigned, "D", g)[0]
    shifted = [episode("e1", 1, (residual("r1", -5.0),)), episode("e2", 2, (residual("r2", -3.0),)),
               episode("e3", 3, (residual("r3", +1.0),))]
    holds, eids, rids = guard_holds(shifted, "D", g)
    assert holds and set(rids) == {"r1", "r2"}


# --- the nominator's inputs ---------------------------------------------------------------------------------


class _World:
    async def find(self, *a, **k):  # noqa: ANN002, ANN003, ANN201
        return []

    async def aggregate(self, *a, **k):  # noqa: ANN002, ANN003, ANN201
        return []

    async def collection_names(self):  # noqa: ANN201
        return []


SHAPE = Shape(id="S", observation_ids=("o1",), episode_ids=("e1",), templates=frozenset({"t1"}),
              personas=frozenset({"omar"}), terms=frozenset({"customers"}))


def test_nominator_sees_only_its_shapes_episodes() -> None:
    NominatorInput(shape=SHAPE, sources=(obs("o1", "e1"),), episodes=(episode("e1", 1, ()),),
                   vocabulary=(), world=_World())
    with pytest.raises(ValueError, match="outside its shape"):
        NominatorInput(shape=SHAPE, sources=(obs("o1", "e1"),),
                       episodes=(episode("e1", 1, ()), episode("e9", 9, ())), vocabulary=(), world=_World())
    with pytest.raises(ValueError, match="outside its shape"):
        NominatorInput(shape=SHAPE, sources=(obs("o2", "e1"),), episodes=(), vocabulary=(), world=_World())


# --- one quirk per question ----------------------------------------------------------------------------------


def test_one_quirk_per_question() -> None:
    q1 = Template(id="active_by_year", text="{y}", collections=("customers",), quirks=("Q1",))
    control = Template(id="accounts_total", text="{y}", collections=("accounts",), quirks=())
    with pytest.raises(ValueError, match="more than one quirk"):
        QuestionBank(templates=(Template(id="x", text="", collections=(), quirks=("Q1", "Q2")),),
                     personas=("omar",), quirk_share=0.65)
    assert hidden_quirks(control, "dana", {"dana": "P1"}) == ("P1",)
    assert hidden_quirks(q1, "omar", {"dana": "P1"}) == ("Q1",)
    with pytest.raises(ValueError, match="one quirk per question"):
        hidden_quirks(q1, "dana", {"dana": "P1"})


# --- the direction read --------------------------------------------------------------------------------------


def test_direction_read_refuses_a_shape_with_no_gap() -> None:
    bar = Bar(min_obs=2, min_templates=2, min_gap=0.10, min_matched=10)
    assert bar.direction_clears(DirectionRead(misses_in=16, n_in=20, misses_out=40, n_out=100))
    assert not bar.direction_clears(DirectionRead(misses_in=9, n_in=20, misses_out=45, n_out=100))
    assert not bar.direction_clears(DirectionRead(misses_in=5, n_in=5, misses_out=10, n_out=100))
    assert presentation_filter(SHAPE) == {"terms": {"$in": ["customers"]}}


# --- paired readings ---------------------------------------------------------------------------------------------


def test_paired_difference_three_way_verdict() -> None:
    a, b = [1.0] * 80 + [0.0] * 20, [1.0] * 40 + [0.0] * 60
    r = paired_difference(a, b, n_boot=500, level=0.90, seed=1)
    assert r.n == 100 and r.lo <= r.diff <= r.hi and r.verdict(0.05) == "above"
    assert paired_difference(b, a, n_boot=500, level=0.90, seed=1).verdict(0.05) == "below"
    assert paired_difference(a, a, n_boot=500, level=0.90, seed=1).verdict(0.05) == "within"

