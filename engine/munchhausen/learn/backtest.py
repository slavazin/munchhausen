"""Backtest (SPEC § 7.4): the dispositive layer.

Population: episodes whose questions the draft's hook matches, minus every episode the nominator saw; for a
supersede draft, only from the predecessor's earliest open dispositive fire on; for a new draft, only the
last BACKTEST_RECENT episodes. Balanced sample of ≤ BACKTEST_N, misses meeting the hook's terms first.
Replay, paired: for each sampled question, consult the arm's **current** admitted store (minus the
predecessor), then run the proposer twice on that context — once with the draft, once without. Both
replays are scored against the episode's confirmed figure — never `truth.gold`. `fixed` and `broken` read
the difference between the two replays (`domain/backtest.py`), and a fix counts only where the with-draft
replay applied the draft; the episode's recorded outcome is only the sampling stratum. Cost: 2 × BACKTEST_N
proposer calls per draft.

A backtest that cannot read (fewer than BACKTEST_MIN_N scored pairs: a thin population, or replays that
raised) is INSUFFICIENT: L4 holds the draft, never refuses it. Its id is keyed by (draft, adjudication index),
so a later round reads afresh.

Leakage guards, each a refusal of a population member rather than a correction after the fact:
- every episode the nominator saw is excluded (`Draft.nominator_seen_episode_ids`: the shape's episodes and
  the episodes behind the neighbours' residuals), with the warrant's and the context's source episodes;
- so is every episode asking one of those episodes' questions, or the same question text (a twin carries the
  source's figure, and a payload fitted to it would "fix" it);
- only stream episodes with a confirmed figure (an authority's reply or a scored hit) enter;
- a supersede draft reads only episodes from the predecessor's earliest open dispositive fire on, and never
  without one (the fire marks where the world shifted; before it, the predecessor's figures are right);
- the context is the arm's current store through the arm's own consultation, minus the predecessor; the
  episode's old `consulted` list is a context the draft will never run in.

Residue: the read is the authority's, not the world's. An authority wrong the same way on every episode
reproduces itself out of sample and passes (§ 0, § 7.4).
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from munchhausen.agent.consultation import Consulter
from munchhausen.agent.execute import ExecutionError, execute
from munchhausen.agent.proposer import Proposer
from munchhausen.domain.backtest import Backtest, BacktestSample, BacktestThresholds, BacktestVerdict
from munchhausen.domain.common import Disposition, FireDisposition, FireRole, LifecycleStatus
from munchhausen.domain.decision import Decision, EntryContract, Lifecycle
from munchhausen.domain.draft import Draft, Route
from munchhausen.domain.episode import Episode, Proposal
from munchhausen.domain.ids import backtest_id, decision_id
from munchhausen.domain.latches import HookLatch
from munchhausen.domain.question import Question, QuestionKeys, SchemaSummary
from munchhausen.domain.scoring import matches
from munchhausen.ports.curation import CurationContext
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import (
    BacktestRepository,
    DocumentReader,
    EpisodeRepository,
    FireRepository,
    ToolAccessRepository,
)


def population_filter(hook: HookLatch, *, exclude_ids: Sequence[str], exclude_questions: Sequence[str],
                      after_idx: int | None, exclude_texts: Sequence[str] = ()) -> dict[str, Any]:
    """The hook's match (`HookLatch.matches`) as one `$match` over episode keys, plus the leakage guards.
    The domain function stays the one definition: `Backtester` re-checks every sampled episode with it."""
    fw = hook.fires_when
    ors: list[dict[str, Any]] = []
    if fw.terms:
        ors.append({"terms": {"$in": sorted(fw.terms)}})
    if fw.collections:
        ors.append({"collections": {"$in": sorted(fw.collections)}})
    if not ors:
        return {"_id": {"$in": []}}            # a hook with no keys matches nothing
    f: dict[str, Any] = {"stream": "stream", "confirmed_figure": {"$ne": None}, "$or": ors,
                         "_id": {"$nin": sorted(exclude_ids)}, "question_id": {"$nin": sorted(exclude_questions)}}
    if exclude_texts:
        f["text"] = {"$nin": sorted(exclude_texts)}
    if fw.persona is not None:
        f["persona"] = fw.persona
    nots = []
    for row in hook.not_this:
        if row.is_empty():
            continue
        cond: dict[str, Any] = {}
        if row.terms:
            cond["terms"] = {"$all": list(row.terms)}
        if row.collections:
            cond["collections"] = {"$all": list(row.collections)}
        if row.persona is not None:
            cond["persona"] = row.persona
        nots.append(cond)
    if nots:
        f["$nor"] = nots
    if after_idx is not None:
        f["idx"] = {"$gt": after_idx}
    return f


def episode_keys(e: Episode) -> QuestionKeys:
    return QuestionKeys(terms=frozenset(e.terms), collections=frozenset(e.collections or (e.collection,)),
                        persona=e.persona)


def episode_question(e: Episode) -> Question:
    """Rebuild the legible `Question` an episode asked (no hidden tags exist on either side)."""
    return Question(id=e.question_id, text=e.text, template=e.template, persona=e.persona,
                    collections=e.collections or (e.collection,))


def provisional_decision(draft: Draft, at_idx: int) -> Decision:
    """The draft as the proposer would meet it once admitted: same entry, the id admission would mint."""
    entry = {k: getattr(draft, k) for k in EntryContract.model_fields}
    return Decision(_id=decision_id(draft.id), run_id=draft.run_id, arm=draft.arm,
                    lifecycle=Lifecycle(status=LifecycleStatus.ADMITTED, at_idx=at_idx), **entry)


def excluded_from_context(draft: Draft) -> frozenset[str]:
    """Decisions the draft would replace: they leave the replay's context (and their floor views)."""
    out = set(draft.wiring.converged_from) if draft.route is Route.REFINE else set()
    if draft.route is Route.SUPERSEDE and draft.supersedes:
        out.add(draft.supersedes)
    return frozenset(out)


def read_id(draft_id: str, at_idx: int) -> str:
    """A backtest belongs to one adjudication: (draft, index). A later round's read is a new record."""
    return backtest_id(f"{draft_id}@{at_idx}")


@dataclass(frozen=True)
class BacktestRun:
    """The record plus the telemetry that is not a `backtests` field (it lands in the L4 outcome)."""

    backtest: Backtest
    population_after_idx: int | None = None
    calls: int = 0
    errors: int = 0
    applied: int = 0                        # with-draft replays whose proposer recorded the draft `applied`
    hook_mismatch: int = 0                  # sampled by the `$match` but refused by `HookLatch.matches`
    reason: str | None = None               # set when the population is refused before sampling
    reused: bool = False
    replays: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    @property
    def insufficient(self) -> bool:
        return self.backtest.verdict is BacktestVerdict.INSUFFICIENT

    def detail(self) -> dict[str, Any]:
        bt = self.backtest
        misses = [s for s in bt.sampled if not s.original_correct]
        return {
            "backtest_id": bt.id, "verdict": bt.verdict.value, "fixed": bt.fixed, "fixed_heldout": bt.fixed_heldout,
            "broken": bt.broken, "n": len(bt.sampled), "sampled": [s.episode_id for s in bt.sampled],
            "misses_sampled": len(misses), "misses_fixed": sum(1 for s in misses if s.fixed),
            "source_templates": sorted(bt.source_templates), "after_idx": self.population_after_idx,
            "calls": self.calls, "errors": self.errors or len(bt.errors), "applied": self.applied,
            "holdout_reserved": bt.holdout_reserved, "holdout_available": bt.holdout_available,
            "hook_mismatch": self.hook_mismatch, "reason": self.reason or ("insufficient" if self.insufficient
                                                                           else None),
            "reused": self.reused,
        }


@dataclass
class Backtester:
    episodes: EpisodeRepository
    fires: FireRepository
    consulter: Consulter          # the arm's own consultation, so replays run in the context the draft will meet
    proposer: Proposer
    world: DocumentReader
    thresholds: BacktestThresholds
    n: int
    rel_tol: float
    max_time_ms: int
    backtests: BacktestRepository
    tool_access: ToolAccessRepository
    schema: Callable[[], SchemaSummary]
    seed: int | None = None       # None: `$sample` (not replayable); else a seeded hash order
    concurrency: int = 4
    trace: Trace | None = None
    question_of: Callable[[Episode], Question] = episode_question   # the episode's legible fields suffice; the
    #                     composition root may point this at the world's id-based rebuild once the port has one
    recent: int | None = None     # BACKTEST_RECENT: a new draft reads only the last N episodes
    holdout_share: float = 0.25   # BACKTEST_HOLDOUT_SHARE: slots reserved for the draft's held-out templates

    async def run(self, draft: Draft, ctx: CurationContext) -> BacktestRun:
        bid = read_id(draft.id, ctx.at_idx)
        existing = await self.backtests.get(bid)
        if existing is not None:                        # resume: one read per (draft, index)
            return BacktestRun(backtest=existing, reused=True)

        warrant_ids = set(draft.warrant.source_episode_ids) | {o.episode_id for o in ctx.sources}
        seen_ids = warrant_ids | set(draft.nominator_seen_episode_ids)
        seen = [e for e in [await self.episodes.get(i) for i in sorted(seen_ids)] if e]
        source_templates = frozenset({e.template for e in seen if e.id in warrant_ids}
                                     | {o.template for o in ctx.sources})
        excluded = excluded_from_context(draft)

        after_idx, reason = None, None
        if draft.route is Route.SUPERSEDE:
            opened = [f for f in await self.fires.open_for(draft.supersedes or "")
                      if f.role is FireRole.DISPOSITIVE and f.disposition is FireDisposition.OPEN]
            if opened:
                after_idx = min(f.at_idx for f in opened) - 1     # from the firing episode on
            else:
                reason = "supersede without an open dispositive fire on the predecessor"
        elif self.recent is not None:
            after_idx = ctx.at_idx - self.recent - 1 if ctx.at_idx > self.recent else None

        sampled: list[Episode] = []
        mismatch, reserved, available = 0, 0, None
        if reason is None:
            match = population_filter(draft.hook, exclude_ids=sorted(seen_ids),
                                      exclude_questions=sorted({e.question_id for e in seen}),
                                      exclude_texts=sorted({e.text for e in seen}), after_idx=after_idx)
            drawn, reserved, available = await self._draw(draft, match)
            sampled = [e for e in drawn if draft.hook.matches(episode_keys(e))]
            mismatch = len(drawn) - len(sampled)
            if not sampled:
                reason = "empty population"

        view_map = {t.logical: t.view for t in await self.tool_access.rewires(draft.run_id, draft.arm)
                    if t.decision_id not in excluded}
        candidate = provisional_decision(draft, ctx.at_idx)
        sem = asyncio.Semaphore(max(1, self.concurrency))
        results = await asyncio.gather(*(self._pair(e, candidate, excluded, view_map, sem) for e in sampled))

        samples = tuple(s for s, _ in results if s is not None)
        replays = tuple(r for _, r in results)
        errors = tuple(f"{r['episode_id']}: {r['error']}" for s, r in results if s is None)
        bt = Backtest.read(id=bid, run_id=draft.run_id, arm=draft.arm, draft_id=draft.id, sampled=samples,
                           source_templates=source_templates, thresholds=self.thresholds, errors=errors,
                           at_idx=ctx.at_idx, holdout_reserved=reserved, holdout_available=available)
        await self.backtests.put(bt)
        run = BacktestRun(backtest=bt, population_after_idx=after_idx, calls=2 * len(sampled), errors=len(errors),
                          applied=sum(1 for r in replays if r.get("applied")), hook_mismatch=mismatch,
                          reason=reason, replays=replays)
        if self.trace is not None:
            self.trace.event("backtest", {"draft_id": draft.id, "arm": draft.arm, **run.detail(),
                                          "replays": list(replays)})
        return run

    async def _draw(self, draft: Draft, match: dict[str, Any]) -> tuple[list[Episode], int, int | None]:
        """The sample. With a held-out template fold (`draft.holdout_templates`), ceil(n · HOLDOUT_SHARE)
        slots go first to episodes of those templates (hits and misses, misses first), so `fixed_heldout`
        has episodes to read; the rest is drawn as usual. A population short of held-out episodes gives what
        it has, recorded as `holdout_available`."""
        terms = tuple(draft.hook.fires_when.terms)
        held: list[Episode] = []
        reserved, available = 0, None
        if draft.holdout_templates and "$nin" in match.get("_id", {}):
            reserved = min(self.n, math.ceil(self.n * self.holdout_share))
            hmatch = {**match, "template": {"$in": sorted(draft.holdout_templates)}}
            held = await self.episodes.backtest_sample(draft.run_id, draft.arm, hmatch, n=reserved, seed=self.seed,
                                                       prefer_terms=terms)
            available = len(held)
            match = {**match, "_id": {"$nin": sorted(set(match["_id"]["$nin"]) | {e.id for e in held})}}
        rest = await self.episodes.backtest_sample(draft.run_id, draft.arm, match, n=self.n - len(held),
                                                   seed=self.seed, prefer_terms=terms)
        return held + rest, reserved, available

    async def _pair(self, e: Episode, candidate: Decision, excluded: frozenset[str], view_map: dict[str, str],
                    sem: asyncio.Semaphore) -> tuple[BacktestSample | None, dict[str, Any]]:
        question = self.question_of(e)
        async with sem:
            try:
                _, consulted = await self.consulter.consult(e.run_id, e.arm, question)
                context = [d for d in consulted if d.id not in excluded and d.id != candidate.id]
                schema = self.schema()
                with_p, without_p = await asyncio.gather(
                    self.proposer.propose(e.arm, question, schema, [candidate, *context], stage="replay"),
                    self.proposer.propose(e.arm, question, schema, context, stage="replay"))
            except Exception as exc:  # a model or consultation failure drops the pair; it never scores one side
                return None, {"episode_id": e.id, "error": f"{type(exc).__name__}: {exc}"}
        with_ok, with_ans = await self._score(with_p, e, view_map, candidate)
        without_ok, without_ans = await self._score(without_p, e, view_map, None)
        applied = any(c.decision_id == candidate.id and c.disposition is Disposition.APPLIED
                      for c in with_p.consulted)
        sample = BacktestSample(episode_id=e.id, template=e.template, original_correct=e.correct,
                                replay_correct=with_ok, baseline_correct=without_ok,
                                context=tuple(d.id for d in context), applied=applied,
                                replay_answer=with_ans, baseline_answer=without_ans)
        return sample, {"episode_id": e.id, "with": with_ans, "without": without_ans, "applied": applied,
                        "figure": e.confirmed_figure}

    async def _score(self, p: Proposal, e: Episode, view_map: dict[str, str],
                     candidate: Decision | None) -> tuple[bool, Any]:
        floor = candidate.floor if candidate is not None else None
        if floor is not None and p.collection == floor.collection:
            # the view the floor would create is its `$match` prepended; replaying it inline needs no DDL
            p = p.model_copy(update={"pipeline": [{"$match": floor.match}, *p.pipeline]})
        try:
            answer = (await execute(p, view_map, self.world, max_time_ms=self.max_time_ms)).answer
        except ExecutionError:
            return False, None
        return matches(answer, e.confirmed_figure, rel_tol=self.rel_tol), answer


def applied_premise(backtests: Sequence[Backtest], first: int = 10) -> dict[str, Any]:
    """SPEC § 12 second premise, read from `backtests`: over the first `first` backtests that read (not
    INSUFFICIENT), the share of sampled first-attempt misses the paired replay fixes. Which quirk a draft
    encodes is evaluation-side (`planted_map`); this is the learner-side read of the same premise."""
    head = [b for b in backtests if b.verdict is not BacktestVerdict.INSUFFICIENT][:first]
    misses = [s for b in head for s in b.sampled if not s.original_correct]
    fixed = sum(1 for s in misses if s.fixed)
    return {"backtests": len(head), "misses_sampled": len(misses), "misses_fixed": fixed,
            "rate": fixed / len(misses) if misses else None}
