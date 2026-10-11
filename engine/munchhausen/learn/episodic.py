"""Episodic pass (SPEC § 7.2), once per (arm, round); idempotent.

group (Grouper port) → coherence guard → bar → direction read → nominate → adjudicate. The guard and the
bar are pure and live here; grouping, nomination and adjudication are injected.

Every open observation is carried until a shape spends it (CARRY_ROUNDS unset): evidence for a rare
template or one persona arrives slowly, and an expiry window shorter than its arrival rate refuses it
by construction.

Observation dispositions are owned here, not by the adjudicator:
- a nominated shape's observations become `shaped` when its draft is written;
- after adjudication they become `spent` when the draft is admitted or refused, and go back to `open` when
  it is held (L1): held evidence is carried and joins later shapes;
- a held draft is never duplicated. A shape with exactly the held draft's sources is skipped (it waits for
  new evidence); a shape that overlaps them with anything more is re-nominated, and the held draft is
  closed (`refused`, adjudication entry `renominated` naming the successor draft).
A bar or direction-read refusal leaves the observations `open`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from munchhausen.config import Settings
from munchhausen.domain.draft import DirectionRead, Draft, DraftStatus, LayerOutcome, Shape, Verdict
from munchhausen.domain.ids import draft_id, shape_id
from munchhausen.domain.observation import Observation, ObservationClass, ObservationDisposition
from munchhausen.learn.nominate import Nominator
from munchhausen.ports.curation import Adjudicator, CurationContext
from munchhausen.ports.grouper import Grouper
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import DraftRepository, EpisodeRepository, ObservationRepository

RENOMINATED = "renominated"


def norm(term: str) -> str:
    return " ".join(term.lower().split())


def shape_of(members: Sequence[Observation]) -> Shape:
    """A shape's terms are the normalized terms its members share: the presentation the direction read
    keys on. One definition for every grouper and for the guard."""
    ids = tuple(sorted(o.id for o in members))
    term_sets = [{norm(t) for t in o.surfaces.terms} for o in members]
    return Shape(
        id=shape_id(ids),
        observation_ids=ids,
        episode_ids=tuple(sorted({o.episode_id for o in members})),
        templates=frozenset(o.template for o in members),
        personas=frozenset(o.persona for o in members),
        terms=frozenset(set.intersection(*term_sets)) if term_sets else frozenset(),
    )


def coherence_guard(shape: Shape, members: Sequence[Observation]) -> list[Shape]:
    """A cluster whose members share no normalized term or authority phrasing is split by term.
    The guard checks the grouping and proposes nothing.

    The split is a partition: each member joins its most frequent term within the cluster (ties by name);
    a member with no term joins no shape and stays open."""
    if len(members) <= 1:
        return [shape_of(members)] if members else []
    term_sets = [{norm(t) for t in o.surfaces.terms} for o in members]
    phrasings = {o.surfaces.phrasing for o in members}
    if set.intersection(*term_sets) or (len(phrasings) == 1 and None not in phrasings):
        return [shape_of(members)]
    freq = Counter(t for ts in term_sets for t in ts)
    groups: dict[str, list[Observation]] = {}
    for o, ts in zip(members, term_sets, strict=True):
        if ts:
            best = min(ts, key=lambda t: (-freq[t], t))
            groups.setdefault(best, []).append(o)
    return [shape_of(g) for _, g in sorted(groups.items())]


@dataclass(frozen=True)
class Bar:
    min_obs: int
    min_templates: int
    min_gap: float          # BAR_MIN_GAP: miss rate inside the shape's presentation minus outside it
    min_matched: int        # BAR_MIN_MATCHED: episodes the presentation must match before the gap reads

    @classmethod
    def from_settings(cls, s: Settings) -> Bar:
        return cls(min_obs=s.bar_min_obs, min_templates=s.bar_min_templates, min_gap=s.bar_min_gap,
                   min_matched=s.bar_min_matched)

    def clears(self, shape: Shape, members: Sequence[Observation]) -> bool:
        """≥ min_obs observations from ≥ min_templates templates; persona-scoped shapes need ≥ 2
        observations from the same persona."""
        if len(members) < self.min_obs or len(shape.templates) < self.min_templates:
            return False
        if len(shape.personas) == 1:
            return len(members) >= 2
        return True

    def direction_clears(self, read: DirectionRead) -> bool:
        """E4: the shape's presentation marks a real gap, read over hits and misses alike."""
        return read.n_in >= self.min_matched and read.gap >= self.min_gap


def presentation_filter(shape: Shape) -> dict[str, object]:
    """Episodes a shape's presentation matches: its shared terms, else its templates."""
    if shape.terms:
        return {"terms": {"$in": sorted(shape.terms)}}
    return {"template": {"$in": sorted(shape.templates)}}


@dataclass
class PassReport:
    """What one episodic pass did, for tests and the evidence report (every row is also a trace event)."""

    shapes: list[str] = field(default_factory=list)
    refused: list[tuple[str, str]] = field(default_factory=list)    # (shape id, reason)
    drafts: list[str] = field(default_factory=list)
    outcomes: dict[str, list[LayerOutcome]] = field(default_factory=dict)
    failed: list[tuple[str, str]] = field(default_factory=list)     # (shape id, error)


@dataclass
class EpisodicPass:
    observations: ObservationRepository
    episodes: EpisodeRepository
    drafts: DraftRepository
    grouper: Grouper
    bar: Bar
    nominator: Nominator
    adjudicator: Adjudicator
    round_size: int
    carry_rounds: int | None = None
    with_authority: bool = True       # the direction read reads `correct`: arms with an authority only
    trace: Trace | None = None

    async def run(self, run_id: str, arm: str, round_: int,
                  idx_range: tuple[int, int] | None = None) -> PassReport:
        report = PassReport()
        at_idx = idx_range[1] if idx_range else (round_ + 1) * self.round_size
        since = 0 if self.carry_rounds is None else max(0, round_ - self.carry_rounds + 1)
        open_ = [o for o in await self.observations.open_for_pass(run_id, arm, since_round=since)
                 if o.cls is ObservationClass.REDUCIBLE]
        if not open_:
            return report
        by_id = {o.id: o for o in open_}
        held = await self.drafts.held(run_id, arm)

        shapes: list[tuple[Shape, list[Observation]]] = []
        for located in await self.grouper.group(open_):
            members = [by_id[i] for i in located.observation_ids if i in by_id]
            guarded = coherence_guard(located, members)
            if len(guarded) != 1 or guarded[0].id != located.id:
                self._event("shape.split", {"arm": arm, "round": round_, "located": located.id,
                                            "into": [g.id for g in guarded], "grouper": self.grouper.id})
            shapes += [(g, [by_id[i] for i in g.observation_ids]) for g in guarded]

        for shape, members in shapes:
            report.shapes.append(shape.id)
            self._event("shape.formed", {"arm": arm, "round": round_, "shape_id": shape.id,
                                         "n_obs": len(members), "templates": sorted(shape.templates),
                                         "personas": sorted(shape.personas), "terms": sorted(shape.terms),
                                         "grouper": self.grouper.id})
            reason = await self._bar(run_id, arm, round_, shape, members, at_idx)
            if reason is None:
                reason = await self._held_or_done(run_id, arm, round_, shape, held)
            if reason is not None:
                report.refused.append((shape.id, reason))
                self._event("shape.refused", {"arm": arm, "round": round_, "shape_id": shape.id,
                                              "reason": reason})
                continue
            await self._nominate(run_id, arm, round_, shape, members, held, at_idx, report)
        return report

    # --- steps ---------------------------------------------------------------------------------------

    async def _bar(self, run_id: str, arm: str, round_: int, shape: Shape, members: list[Observation],
                   at_idx: int) -> str | None:
        clears = self.bar.clears(shape, members)
        self._event("bar.verdict", {"arm": arm, "round": round_, "shape_id": shape.id, "clears": clears,
                                    "n_obs": len(members), "templates": len(shape.templates),
                                    "min_obs": self.bar.min_obs, "min_templates": self.bar.min_templates})
        if not clears:
            return "bar"
        if not self.with_authority:
            return None
        flt = presentation_filter(shape)
        read = await self.episodes.direction_read(run_id, arm, flt, before_idx=at_idx)
        ok = self.bar.direction_clears(read)
        self._event("bar.direction_read", {"arm": arm, "round": round_, "shape_id": shape.id, "filter": flt,
                                           "n_in": read.n_in, "misses_in": read.misses_in, "n_out": read.n_out,
                                           "misses_out": read.misses_out, "gap": read.gap, "clears": ok,
                                           "min_gap": self.bar.min_gap, "min_matched": self.bar.min_matched})
        return None if ok else "direction"

    async def _held_or_done(self, run_id: str, arm: str, round_: int, shape: Shape,
                            held: Sequence[Draft]) -> str | None:
        ids = set(shape.observation_ids)
        if any(set(h.source_observation_ids) == ids for h in held):
            return "held"          # the same evidence is already held; it waits for more
        if await self.drafts.get(draft_id(run_id, arm, round_, shape.id)) is not None:
            return "nominated"     # idempotent re-run of this (arm, round)
        return None

    async def _nominate(self, run_id: str, arm: str, round_: int, shape: Shape, members: list[Observation],
                        held: Sequence[Draft], at_idx: int, report: PassReport) -> None:
        try:
            nom = await self.nominator.nominate(run_id, arm, round_, shape, members)
        except Exception as e:  # noqa: BLE001 - one failed nomination never sinks the round
            report.failed.append((shape.id, f"{type(e).__name__}: {e}"))
            self._event("nomination.failed", {"arm": arm, "round": round_, "shape_id": shape.id,
                                              "error": f"{type(e).__name__}: {e}"})
            return
        draft = nom.draft
        await self.drafts.put(draft)
        await self.observations.dispose(shape.observation_ids, ObservationDisposition.SHAPED, by=draft.id)
        report.drafts.append(draft.id)
        self._event("draft.written", draft_event(draft, nom.neighbours))

        ids = set(shape.observation_ids)
        for h in held:
            if set(h.source_observation_ids) & ids:
                closed = LayerOutcome(layer=RENOMINATED, role=None, verdict=Verdict.REFUSE,
                                      detail={"renominated_as": draft.id})
                await self.drafts.put(h.model_copy(update={"status": DraftStatus.REFUSED,
                                                           "adjudication": {**h.adjudication,
                                                                            RENOMINATED: closed}}))
                self._event("draft.renominated", {"arm": arm, "held": h.id, "successor": draft.id})

        ctx = CurationContext(run_id=run_id, arm=arm, at_idx=at_idx, sources=tuple(members),
                              neighbours=nom.neighbours)
        outcomes = await self.adjudicator.adjudicate(draft, ctx)
        report.outcomes[draft.id] = outcomes
        final = outcomes[-1].verdict if outcomes else None
        if final is Verdict.HOLD:
            await self.observations.dispose(shape.observation_ids, ObservationDisposition.OPEN, by=draft.id)
        elif final in (Verdict.ADMIT, Verdict.REFUSE):
            await self.observations.dispose(shape.observation_ids, ObservationDisposition.SPENT, by=draft.id)
        self._event("draft.adjudicated", {"arm": arm, "draft_id": draft.id,
                                          "verdict": final.value if final else None,
                                          "layers": [o.layer for o in outcomes]})

    def _event(self, name: str, payload: dict[str, Any]) -> None:
        if self.trace is not None:
            self.trace.event(name, payload)


def draft_event(draft: Draft, neighbours: Sequence[tuple[Any, float]]) -> dict[str, Any]:
    """Why this draft was written: neighbours shown, options run, figures reproduced."""
    return {
        "arm": draft.arm, "round": draft.round, "draft_id": draft.id, "shape_id": draft.shape_id,
        "title": draft.title, "kind": draft.kind.value, "route": draft.route.value,
        "supersedes": draft.supersedes, "new_terms": list(draft.new_terms),
        "hook_terms": list(draft.hook.fires_when.terms),
        "neighbours": [{"id": d.id, "score": s, "evidence_state": d.evidence_state.value} for d, s in neighbours],
        "options": [{"definition": o.definition, "verdict": o.verdict, "prior": o.prior,
                     "figures_reproduced": list(o.figures_reproduced)} for o in draft.options],
        "figures_reproduced": list(draft.warrant.figures_reproduced),
        "sources": len(draft.source_observation_ids),
    }
