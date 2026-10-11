"""A small synthetic run shaped like the one complete story (SPEC § 13), for developing and testing the
viewer before a real run exists: Q1 learned → applied on an unseen template → D1 fires → superseded with a
tombstone → recovery on the paired curve, plus a floor decision and a refused draft.

Every record is a domain model, and `seed` writes them through the engine's repositories and the decision
store's own write path (`admit`, `supersede`), so the viewer reads exactly the shapes a run writes.
Synthetic outcomes are drawn from a seeded RNG; nothing here is a reading.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from munchhausen.config import Settings
from munchhausen.domain.admission import Admission, plan_admission
from munchhausen.domain.arm import ArmSpec, WritePath
from munchhausen.domain.backtest import Backtest, BacktestSample
from munchhausen.domain.common import (
    DecisionKind,
    Disposer,
    Disposition,
    FireDisposition,
    FireRole,
    LayerRole,
    Signature,
)
from munchhausen.domain.decision import Decision, Option, Warrant
from munchhausen.domain.draft import Draft, DraftStatus, LayerOutcome, Route, Verdict
from munchhausen.domain.episode import Consultation, Episode, Residual
from munchhausen.domain.fire import Fire, FireCause
from munchhausen.domain.ids import backtest_id, decision_id, draft_id, episode_id, fire_id, latch_id, observation_id
from munchhausen.domain.latches import (
    FloorLatch,
    Guard,
    HookLatch,
    KeySet,
    MootWhen,
    NotThisRow,
    RetireLatch,
    RevisitLatch,
)
from munchhausen.domain.observation import Observation, ObservationClass, Surfaces, Via
from munchhausen.domain.registers import RoundRecord, RunRecord
from munchhausen.store.names import view_name

# (template, persona, terms, collection, quirk group)
TEMPLATES: tuple[tuple[str, str, tuple[str, ...], str, str], ...] = (
    ("active_customers_count", "ops", ("active customers",), "customers", "q1"),
    ("active_customers_by_tier", "finance", ("active customers", "tier"), "customers", "q1"),
    ("active_customer_share", "ops", ("active customers", "share"), "customers", "q1"),
    ("accounts_with_limit", "ops", ("accounts", "limit"), "accounts", "floor"),
    ("open_accounts_count", "finance", ("accounts",), "accounts", "floor"),
    ("trades_by_symbol", "dana", ("transactions", "symbol"), "transactions", "control"),
    ("revenue_by_quarter", "finance", ("revenue", "fiscal quarter"), "transactions", "control"),
)
Q1_HELDOUT = "active_customer_share"   # the unseen template Q1's decision is applied on


@dataclass
class SyntheticRun:
    run_id: str
    length: int
    run: RunRecord
    episodes: list[Episode] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    drafts: list[Draft] = field(default_factory=list)
    backtests: list[Backtest] = field(default_factory=list)
    fires: list[Fire] = field(default_factory=list)
    rounds: list[RoundRecord] = field(default_factory=list)
    admissions: list[tuple[str, Admission]] = field(default_factory=list)   # ("admit"|"supersede", plan)


def _hook(terms: Sequence[str], colls: Sequence[str], contrast_terms: Sequence[str], contrast: str) -> HookLatch:
    return HookLatch(fires_when=KeySet(terms=tuple(terms), collections=tuple(colls)),
                     not_this=(NotThisRow(terms=tuple(contrast_terms), contrast=contrast),))


def _draft(run_id: str, arm: str, round_: int, key: str, *, title: str, kind: DecisionKind, payload: str,
           hook: HookLatch, sig: Signature, obs: Sequence[Observation], extra: tuple = (),
           route: Route = Route.NEW, supersedes: str | None = None, status: DraftStatus = DraftStatus.PENDING,
           options: tuple[Option, ...] = ()) -> Draft:
    did = draft_id(run_id, arm, round_, key)
    dec = decision_id(did)
    latches = (hook,
               RevisitLatch(id=latch_id(dec, 1), signature=sig, guard=Guard(min_residuals=2, window=30)),
               RetireLatch(id=latch_id(dec, 2), moot_when=MootWhen(idle_episodes=300), max_fires=6), *extra)
    return Draft(
        _id=did, run_id=run_id, arm=arm, title=title, kind=kind, payload=payload,
        options=options or (Option(definition=payload, verdict="chosen"),
                            Option(definition="every customer record counts", verdict="rejected", prior=True)),
        forecloses="the prior convention for this concept", latches=latches,
        residue="pipelines that $lookup into the collection from another one are not checked",
        warrant=Warrant(source_observation_ids=tuple(o.id for o in obs),
                        source_episode_ids=tuple(o.episode_id for o in obs),
                        templates=len({o.template for o in obs}),
                        falsifier="two attributable residuals agreeing in direction within 30 consultations"),
        shape_id=f"S-{key}", source_observation_ids=tuple(o.id for o in obs), round=round_, route=route,
        supersedes=supersedes, status=status)


def _layers(bt: Backtest | None, lens: float) -> dict[str, LayerOutcome]:
    out = {"L0": LayerOutcome(layer="L0", role=None, verdict=Verdict.PASS),
           "L1": LayerOutcome(layer="L1", role=None, verdict=Verdict.PASS),
           "L2": LayerOutcome(layer="L2", role=LayerRole.ROUTING, verdict=Verdict.PASS, route=Route.NEW),
           "L3": LayerOutcome(layer="L3", role=LayerRole.CORROBORATING, verdict=Verdict.PASS, score=lens,
                              detail={"generalizes": 0.7, "case_leak": 0.2})}
    if bt is not None:
        out["L4"] = LayerOutcome(layer="L4", role=LayerRole.DISPOSITIVE,
                                 verdict=Verdict.ADMIT if bt.verdict.value == "admit" else Verdict.REFUSE,
                                 detail={"backtest_id": bt.id, "fixed": bt.fixed, "broken": bt.broken})
    return out


def _backtest(run_id: str, arm: str, d: Draft, eps: Sequence[Episode], fixed: int, broken: int,
              settings: Settings, src: frozenset[str]) -> Backtest:
    rows = []
    for k, e in enumerate(eps):
        is_fixed, is_broken = k < fixed, fixed <= k < fixed + broken
        rows.append(BacktestSample(episode_id=e.id, template=e.template, original_correct=e.correct,
                                   replay_correct=is_fixed or (not is_broken and k % 2 == 0),
                                   baseline_correct=is_broken or (not is_fixed and k % 2 == 0)))
    return Backtest.read(id=backtest_id(d.id), run_id=run_id, arm=arm, draft_id=d.id, sampled=tuple(rows),
                         source_templates=src, thresholds=settings.backtest_thresholds)


def build(settings: Settings, run_id: str, *, length: int | None = None, seed: int = 5) -> SyntheticRun:
    """The story over `length` stream indices (default: D1 + 5 rounds), every arm in `Settings.arms()`."""
    arms = settings.arms()
    R, d1 = settings.round_size, settings.d1_at
    n = length or d1 + 5 * R
    rng = random.Random(seed)
    run = RunRecord(_id=run_id, world="synthetic", pack=settings.world_pack, seeds={"synthetic": seed},
                    knobs={"synthetic": True}, ports={a: dict(s.ports) for a, s in arms.items()},
                    forecasts={}, started_at=datetime.now(UTC))
    sr = SyntheticRun(run_id=run_id, length=n, run=run)

    learners = {a: s for a, s in arms.items() if s.write_path is not WritePath.NONE}
    gov = [a for a, s in learners.items() if s.authority and s.write_path is WritePath.EPISODIC]
    q1_admit = 2 * R + R - 1                     # end of round 2
    floor_admit = 5 * R + R - 1                  # end of round 5
    fire_at = d1 + 18
    succ_round = (d1 + 2 * R) // R               # successor admitted two rounds after D1
    succ_admit = succ_round * R + R - 1

    def p_correct(spec: ArmSpec, group: str, idx: int, holds_q1: bool, holds_succ: bool, floor: bool) -> float:
        base = {"control": 0.8, "q1": 0.2, "floor": 0.45}[group]
        if group == "q1" and spec.authority and spec.write_path is not WritePath.NONE and idx > q1_admit:
            base = 0.85 if idx < d1 else (0.85 if holds_succ else 0.25)
        if group == "floor" and floor:
            base = 0.85
        return base

    q1_ids: dict[str, dict[str, str]] = {}
    pending: list[tuple[str, Draft, Draft, Draft, Draft]] = []
    srcs: dict[str, frozenset[str]] = {}
    # --- decisions' drafts first (ids are needed by consultations) ----------------------------------
    for arm in learners:
        if arm not in gov:
            continue
        o_ids = [observation_id(episode_id(run_id, arm, i, stream="stream"), 0) for i in (31, 47, 70)]
        obs = [Observation(_id=oid, run_id=run_id, arm=arm, episode_id=oid.rsplit(":", 1)[0], via=Via.OBSERVER,
                           cls=ObservationClass.REDUCIBLE,
                           noticed="The count includes customers with no transaction in the trailing window; "
                                   "the authority names active customers.",
                           surfaces=Surfaces(terms=("active customers",), collection="customers",
                                             phrasing="active customers"),
                           template=TEMPLATES[k % 2][0], persona=TEMPLATES[k % 2][1], answer=1200 + k,
                           figure=880 + k, round=oid_round, )
               for k, (oid, oid_round) in enumerate(zip(o_ids, (1, 1, 2), strict=True))]
        sr.observations += obs
        hook = _hook(("active customers",), ("customers",), ("all customers",),
                     "'how many customers in total' names every customer, active or not")
        a = _draft(run_id, arm, 2, "q1", title="Active customers have a transaction in the trailing 90 days",
                   kind=DecisionKind.TAXONOMIC, hook=hook, sig=Signature.SET_MEMBER, obs=obs,
                   payload="A customer is active when some account of theirs has a transaction dated within "
                           "the trailing 90 days of the question's as-of date.")
        f_obs = [Observation(_id=observation_id(episode_id(run_id, arm, i), 0), run_id=run_id, arm=arm,
                             episode_id=episode_id(run_id, arm, i), via=Via.OBSERVER, cls=ObservationClass.REDUCIBLE,
                             noticed="Counts over accounts include rows carrying deleted_at.",
                             surfaces=Surfaces(terms=("accounts",), collection="accounts", fields=("deleted_at",)),
                             template=TEMPLATES[3][0], persona="ops", answer=1746, figure=1702, round=4)
                 for k, i in enumerate((121, 133, 140))]
        sr.observations += f_obs
        c = _draft(run_id, arm, 5, "floor", title="Soft-deleted accounts are outside every count",
                   kind=DecisionKind.FLOOR, sig=Signature.EXCLUSION, obs=f_obs,
                   hook=_hook(("accounts",), ("accounts",), ("deleted accounts",),
                              "'how many accounts were deleted' asks for exactly the excluded rows"),
                   payload="Accounts whose deleted_at is set are excluded before any count or sum over accounts.",
                   extra=(FloorLatch(collection="accounts", match={"deleted_at": None}),))
        s_obs = [Observation(_id=observation_id(episode_id(run_id, arm, i), 0), run_id=run_id, arm=arm,
                             episode_id=episode_id(run_id, arm, i), via=Via.OBSERVER, cls=ObservationClass.REDUCIBLE,
                             noticed="Active-customer counts exceed the authority's figure after the window "
                                     "boundary moves; the authority names active customers.",
                             surfaces=Surfaces(terms=("active customers",), collection="customers",
                                               phrasing="active customers"),
                             template=TEMPLATES[k % 2][0], persona="ops", answer=880, figure=610, round=succ_round)
                 for k, i in enumerate((d1 + 4, d1 + 11, d1 + 25))]
        sr.observations += s_obs
        b = _draft(run_id, arm, succ_round, "q1-v2",
                   title="Active customers have a transaction in the trailing 30 days",
                   kind=DecisionKind.TAXONOMIC, hook=hook, sig=Signature.SET_MEMBER, obs=s_obs,
                   payload="A customer is active when some account of theirs has a transaction dated within "
                           "the trailing 30 days of the question's as-of date.",
                   route=Route.SUPERSEDE, supersedes=decision_id(a.id))
        r_obs = [Observation(_id=observation_id(f"{run_id}:{arm}:injection:q{k}:{d1 - 40}", 0), run_id=run_id,
                             arm=arm, episode_id=f"{run_id}:{arm}:injection:q{k}:{d1 - 40}", via=Via.INJECTION,
                             cls=ObservationClass.REDUCIBLE, noticed="The authority names revenue as gross bookings.",
                             surfaces=Surfaces(terms=("revenue",), phrasing="gross bookings"),
                             template=TEMPLATES[6][0], persona="finance", answer=5.1e6, figure=9.9e6, round=8)
                 for k in range(2)]
        sr.observations += r_obs
        r = _draft(run_id, arm, 8, "inj", title="Revenue is gross bookings before refunds",
                   kind=DecisionKind.TAXONOMIC, sig=Signature.RATIO, obs=r_obs,
                   hook=_hook(("revenue",), ("transactions",), ("net revenue",),
                              "'net revenue after refunds' asks for the refunded figure"),
                   payload="Revenue sums price times amount over buy transactions, refunds not netted.",
                   status=DraftStatus.REFUSED)
        q1_ids[arm] = {"a": decision_id(a.id), "b": decision_id(b.id), "c": decision_id(c.id), "r": r.id}
        sr.drafts += [a, b, c, r]
        pending.append((arm, a, b, c, r))

    # --- episodes -----------------------------------------------------------------------------------
    for arm, spec in arms.items():
        ids = q1_ids.get(arm, {})
        for idx in range(n):
            t, persona, terms, coll, group = TEMPLATES[rng.randrange(len(TEMPLATES))]
            holds_q1 = bool(ids) and q1_admit < idx <= succ_admit
            holds_succ = bool(ids) and idx > succ_admit
            floor = bool(ids) and idx > floor_admit
            ok = rng.random() < p_correct(spec, group, idx, holds_q1, holds_succ, floor)
            consulted: list[Consultation] = []
            if group == "q1" and (holds_q1 or holds_succ):
                consulted.append(Consultation(decision_id=ids["a"] if holds_q1 else ids["b"],
                                              disposition=Disposition.APPLIED))
            if group == "floor" and floor:
                consulted.append(Consultation(decision_id=ids["c"], disposition=Disposition.APPLIED))
            if group == "control" and ids and rng.random() < 0.2:
                consulted.append(Consultation(decision_id=ids["a"] if idx <= succ_admit else ids["b"],
                                              disposition=Disposition.CONSIDERED_NOT_APPLICABLE))
            eid = episode_id(run_id, arm, idx)
            figure = 610 if idx >= d1 else 880
            answer = figure if ok else (880 if holds_q1 and idx >= d1 else 1200 + idx % 7)
            residuals: tuple[Residual, ...] = ()
            if not ok and consulted and consulted[0].disposition is Disposition.APPLIED and spec.authority:
                residuals = (Residual(id=f"{eid}:r:{consulted[0].decision_id}", decision_id=consulted[0].decision_id,
                                      answer=answer, figure=figure, ratio=answer / figure, delta=answer - figure,
                                      signature_match=True, attributable=True),)
            view_map = {"accounts": view_name("accounts", ids["c"])} if floor else {}
            pipe = [{"$match": {"status": "active"}}, {"$count": "n"}] if group != "floor" else \
                [{"$match": {"limit": {"$gte": 10000}}}, {"$count": "n"}]
            sr.episodes.append(Episode(
                _id=eid, run_id=run_id, arm=arm, idx=idx, question_id=f"{t}:{idx}",
                text=f"[{t}] How many {terms[0]} as of fiscal day {idx}?", template=t, persona=persona,
                terms=terms, world_version="v0" if idx < d1 else "v0+D1", consulted=tuple(consulted),
                collection=coll, pipeline=pipe, answer_path="n", view_map=view_map, answer=answer,
                confidence=round(0.62 + 0.3 * rng.random(), 2), correct=ok,
                figure=None if ok or not spec.authority else figure, phrasing=None if ok or not spec.authority
                else ("active customers" if group == "q1" else None),
                confirmed_figure=(answer if ok else figure) if spec.authority else None,
                residuals=residuals, collections=(coll,)))
        for vk, v_at in enumerate(range(settings.v_offset, n, settings.v_every)):
            for k in range(10):
                t, persona, terms, coll, group = TEMPLATES[k % len(TEMPLATES)]
                p = p_correct(spec, group, v_at, bool(ids) and v_at > q1_admit, bool(ids) and v_at > succ_admit,
                              bool(ids) and v_at > floor_admit)
                sr.episodes.append(Episode(
                    _id=episode_id(run_id, arm, v_at, stream="v", question_id=f"v{k}"), run_id=run_id, arm=arm,
                    idx=-(1 + vk * 10 + k), v_at=v_at, question_id=f"v{k}",
                    text=f"[V] {t} #{k}", template=t, persona=persona, terms=terms,
                    world_version="v0", consulted=(), collection=coll, pipeline=[], answer_path="n", view_map={},
                    answer=0, confidence=0.7, correct=rng.random() < p, stream="v", collections=(coll,)))

    # --- fires, backtests, admissions --------------------------------------------------------------
    for o in sr.observations:
        srcs[o.id] = frozenset({o.template})
    for arm, a, b, c, r in pending:
        ids = q1_ids[arm]
        resid = [e for e in sr.episodes if e.arm == arm and e.stream == "stream" and e.residuals
                 and e.residuals[0].decision_id == ids["a"] and e.idx <= fire_at]
        if len(resid) < 2:   # the story needs the fire; make the two residuals explicit
            resid = [e for e in sr.episodes if e.arm == arm and e.stream == "stream" and d1 <= e.idx <= fire_at][:2]
        sr.fires.append(Fire(_id=fire_id(ids["a"], latch_id(ids["a"], 1), fire_at), run_id=run_id, arm=arm,
                             decision_id=ids["a"], latch=latch_id(ids["a"], 1), role=FireRole.DISPOSITIVE,
                             cause=FireCause.RESIDUALS, episode_ids=tuple(e.id for e in resid[-2:]),
                             residual_ids=tuple(x.id for e in resid[-2:] for x in e.residuals), at_idx=fire_at))
        sr.fires.append(Fire(_id=fire_id(ids["a"], "unattributed", fire_at + 3), run_id=run_id, arm=arm,
                             decision_id=ids["a"], latch="residual", role=FireRole.CORROBORATING,
                             cause=FireCause.UNATTRIBUTED, episode_ids=(resid[-1].id,), at_idx=fire_at + 3))
        pool = [e for e in sr.episodes if e.arm == arm and e.stream == "stream"]

        def sample(group: str, lo: int, hi: int, k: int, held: frozenset[str],
                   pool: list[Episode] = pool) -> list[Episode]:
            rows = [e for e in pool if lo <= e.idx < hi and any(t[0] == e.template and t[4] == group
                                                                  for t in TEMPLATES)]
            rows.sort(key=lambda e: (e.template in held, e.idx))   # held-out templates first
            return rows[:k]

        def src(d: Draft) -> frozenset[str]:
            return frozenset().union(*(srcs.get(o, frozenset()) for o in d.source_observation_ids))

        bt_a = _backtest(run_id, arm, a, sample("q1", 0, q1_admit, 8, src(a)), 3, 0, settings, src(a))
        bt_c = _backtest(run_id, arm, c, sample("floor", 0, floor_admit, 8, src(c)), 4, 1, settings, src(c))
        bt_b = _backtest(run_id, arm, b, sample("q1", fire_at, succ_admit, 8, src(b)), 4, 0, settings, src(b))
        bt_r = _backtest(run_id, arm, r, sample("control", 0, d1, 8, src(r)), 0, 2, settings, src(r))
        sr.backtests += [bt_a, bt_b, bt_c, bt_r]
        for d, bt in ((a, bt_a), (b, bt_b), (c, bt_c), (r, bt_r)):
            idx_ = sr.drafts.index(d)
            sr.drafts[idx_] = d.model_copy(update={"adjudication": _layers(bt, 0.66 if d is not r else 0.31)})
        plan_a = plan_admission(a, at_idx=q1_admit, backtest_id=bt_a.id, lens_score=0.66)
        plan_c = plan_admission(c, at_idx=floor_admit, backtest_id=bt_c.id, lens_score=0.71,
                                view_name=view_name("accounts", ids["c"]))
        plan_b = plan_admission(b, at_idx=succ_admit, backtest_id=bt_b.id, lens_score=0.69,
                                predecessors=(plan_a.decision,))
        sr.admissions += [("admit", plan_a), ("admit", plan_c), ("supersede", plan_b)]

    # --- rounds (S5 writes these at round close in a real run) --------------------------------------
    for arm in arms:
        eps = [e for e in sr.episodes if e.arm == arm and e.stream == "stream"]
        for r_ in range(n // R):
            win = [e for e in eps if r_ * R <= e.idx < (r_ + 1) * R]
            v = [e for e in sr.episodes if e.arm == arm and e.stream == "v" and r_ * R <= (e.v_at or 0) < (r_ + 1) * R]
            sr.rounds.append(RoundRecord(
                run_id=run_id, arm=arm, round=r_, idx_range=(r_ * R, (r_ + 1) * R - 1),
                acc_stream=sum(e.correct for e in win) / len(win),
                acc_self_assessed=sum(e.confidence for e in win) / len(win),
                acc_v=(sum(e.correct for e in v) / len(v)) if v else None))
    return sr


def apply_plan(decisions: dict[str, Decision], fires: list[Fire], plan: Admission) -> None:
    """In-memory mirror of `DecisionRepository.admit` for the offline read model."""
    decisions[plan.decision.id] = plan.decision
    for f in plan.flips:
        decisions[f.decision_id] = decisions[f.decision_id].model_copy(update={"lifecycle": f.lifecycle})
        for k, fire in enumerate(fires):
            if fire.decision_id == f.decision_id and fire.disposition.value == "open":
                fires[k] = fire.model_copy(update={"disposition": FireDisposition.APPLIED,
                                                   "disposer": Disposer.LIFECYCLE})


async def seed(store: object, sr: SyntheticRun, *, concurrency: int = 32) -> dict[str, int]:
    """Write the synthetic run through the engine's repositories (idempotent upserts; resume-safe)."""
    sem = asyncio.Semaphore(concurrency)

    async def put(repo: object, rec: object) -> None:
        async with sem:
            await repo.put(rec)  # type: ignore[attr-defined]

    s = store
    await s.runs.start(sr.run)  # type: ignore[attr-defined]
    # V episodes follow the runner's convention (negative ordinal idx, `v_at`), so they never collide
    stream = sr.episodes
    await asyncio.gather(*(put(s.episodes, e) for e in stream))  # type: ignore[attr-defined]
    await asyncio.gather(*(put(s.observations, o) for o in sr.observations))  # type: ignore[attr-defined]
    await asyncio.gather(*(put(s.drafts, d) for d in sr.drafts))  # type: ignore[attr-defined]
    await asyncio.gather(*(put(s.backtests, b) for b in sr.backtests))  # type: ignore[attr-defined]
    await asyncio.gather(*(put(s.fires, f) for f in sr.fires))  # type: ignore[attr-defined]
    for r in sr.rounds:
        await s.runs.put_round(r)  # type: ignore[attr-defined]
    for verb, plan in sr.admissions:
        existing = await s.decisions.get(plan.decision.id)  # type: ignore[attr-defined]
        if existing is not None:
            continue
        await getattr(s.decisions, verb)(plan)  # type: ignore[attr-defined]
    return {"episodes": len(stream), "observations": len(sr.observations), "drafts": len(sr.drafts),
            "backtests": len(sr.backtests), "fires": len(sr.fires), "rounds": len(sr.rounds),
            "decisions": len(sr.admissions)}
