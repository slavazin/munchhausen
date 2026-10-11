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
- a failed adjudication sets them back to `open`; a re-run resumes the pending draft of that round;
- a held draft is never duplicated. A shape that strictly contains the held draft's sources (and, for an
  L1 hold, adds a template) is re-nominated and the held draft closed (`refused`, adjudication entry
  `renominated`); any other overlap waits.
A bar or direction-read refusal leaves the observations `open`.

The direction read is windowed: from the nearest contested neighbour's earliest open dispositive fire
(members before it are left out of the shape), else over the last DIRECTION_WINDOW matched episodes.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from munchhausen.config import Settings
from munchhausen.domain.common import DecisionKind, EvidenceState, FireDisposition, FireRole
from munchhausen.domain.draft import DirectionRead, Draft, DraftStatus, LayerOutcome, Shape, Verdict
from munchhausen.domain.ids import draft_id, shape_id
from munchhausen.domain.observation import Observation, ObservationClass, ObservationDisposition
from munchhausen.learn.nominate import Nominator
from munchhausen.ports.curation import Adjudicator, CurationContext
from munchhausen.ports.grouper import Grouper
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import DraftRepository, EpisodeRepository, FireRepository, ObservationRepository

RENOMINATED = "renominated"


def _unit(key: str) -> float:
    return int(hashlib.sha256(key.encode()).hexdigest()[:12], 16) / 16**12


@dataclass(frozen=True)
class Fold:
    """The held-out template fold of one shape: what the nominator is shown, and what is withheld."""

    shape: Shape                          # the shape the nominator sees (the whole shape when nothing is held out)
    members: tuple[Observation, ...]
    templates: tuple[str, ...]            # withheld templates
    withheld: tuple[str, ...]             # withheld observation ids


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


def _sign(o: Observation) -> str | None:
    if o.delta is None:
        return None
    return "+" if o.delta > 0 else "-" if o.delta < 0 else "0"


def coherent(members: Sequence[Observation]) -> str | None:
    """Why a cluster holds together, or None. Members share a normalized term, or one authority phrasing,
    or one persona and agree in direction (sign of answer − figure) or in signature (a persona's preference
    spans unrelated control templates), or one collection with a consistent direction (a floor's population
    surfaces under different terms on different templates)."""
    term_sets = [{norm(t) for t in o.surfaces.terms} for o in members]
    if set.intersection(*term_sets):
        return "term"
    phrasings = {o.surfaces.phrasing for o in members}
    if len(phrasings) == 1 and None not in phrasings:
        return "phrasing"
    signs = {_sign(o) for o in members}
    one_sign = len(signs) == 1 and None not in signs
    sigs = {o.signature_guess for o in members}
    if len({o.persona for o in members}) == 1 and (one_sign or (len(sigs) == 1 and None not in sigs)):
        return "persona"
    collections = {o.surfaces.collection for o in members}
    if len(collections) == 1 and None not in collections and one_sign:
        return "collection"
    return None


def coherence_guard(shape: Shape, members: Sequence[Observation]) -> list[Shape]:
    """A cluster whose members hold together by none of `coherent`'s reads is split by term.
    The guard checks the grouping and proposes nothing.

    The split is a partition: each member joins its most frequent term within the cluster (ties by name);
    a member with no term joins no shape and stays open."""
    if len(members) <= 1:
        return [shape_of(members)] if members else []
    if coherent(members) is not None:
        return [shape_of(members)]
    term_sets = [{norm(t) for t in o.surfaces.terms} for o in members]
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
    """Episodes a shape's presentation matches: its shared (normalized) terms, else its templates — and,
    for a single-persona shape with no shared term, that persona (a preference shape presents as a persona
    across unrelated templates). A shared-term shape is not narrowed to its persona: an organizational
    quirk seen through one persona would read its own population as outside and dilute the gap."""
    if shape.terms:
        return {"terms": {"$in": sorted({norm(t) for t in shape.terms})}}
    out: dict[str, object] = {"template": {"$in": sorted(shape.templates)}}
    if len(shape.personas) == 1:
        out["persona"] = next(iter(shape.personas))
    return out


@dataclass
class PassReport:
    """What one episodic pass did, for tests and the evidence report (every row is also a trace event)."""

    shapes: list[str] = field(default_factory=list)
    refused: list[tuple[str, str]] = field(default_factory=list)    # (shape id, reason)
    drafts: list[str] = field(default_factory=list)
    resumed: list[str] = field(default_factory=list)                # pending drafts re-adjudicated
    outcomes: dict[str, list[LayerOutcome]] = field(default_factory=dict)
    failed: list[tuple[str, str]] = field(default_factory=list)     # (shape or draft id, error)


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
    fires: FireRepository | None = None      # dates a contested neighbour's drift (earliest open dispositive fire)
    direction_window: int | None = None      # DIRECTION_WINDOW; None reads every matched episode (cumulative)
    holdout_templates: int | None = None     # HOLDOUT_TEMPLATES; 0 / None disables the held-out template fold
    min_templates_floor: int | None = None   # BAR_MIN_TEMPLATES_FLOOR (L1's need for kind floor)
    holdout_seed: int | None = None          # tie-break seed for the fold
    settings: Settings | None = None         # when given, fills every knob above that was left unset

    def __post_init__(self) -> None:
        s = self.settings
        if s is None:
            return
        if self.direction_window is None:
            self.direction_window = s.direction_window
        if self.holdout_templates is None:
            self.holdout_templates = s.holdout_templates
        if self.min_templates_floor is None:
            self.min_templates_floor = s.bar_min_templates_floor
        if self.holdout_seed is None:
            self.holdout_seed = s.stream_seed

    @classmethod
    def from_settings(cls, s: Settings, **ports: Any) -> EpisodicPass:
        """Knobs from settings; ports (observations, episodes, drafts, grouper, nominator, adjudicator,
        fires, trace, with_authority) from the composition root."""
        return cls(bar=Bar.from_settings(s), round_size=s.round_size, carry_rounds=s.carry_rounds,
                   direction_window=s.direction_window, holdout_templates=s.holdout_templates,
                   min_templates_floor=s.bar_min_templates_floor, holdout_seed=s.stream_seed, **ports)

    async def run(self, run_id: str, arm: str, round_: int,
                  idx_range: tuple[int, int] | None = None) -> PassReport:
        """`idx_range` is half-open (lo, hi), as the runner emits it; the direction read covers idx < hi."""
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
            try:
                await self._shape(run_id, arm, round_, shape, members, held, at_idx, report)
            except Exception as e:  # noqa: BLE001 - one shape's failure never sinks the round
                report.failed.append((shape.id, f"{type(e).__name__}: {e}"))
                self._event("shape.failed", {"arm": arm, "round": round_, "shape_id": shape.id,
                                             "error": f"{type(e).__name__}: {e}"})
        return report

    # --- one shape -----------------------------------------------------------------------------------

    async def _shape(self, run_id: str, arm: str, round_: int, shape: Shape, members: list[Observation],
                     held: Sequence[Draft], at_idx: int, report: PassReport) -> None:
        neighbours = await self.nominator.neighbours(run_id, arm, shape, members)
        drift_from = await self._drift_start(neighbours)
        if drift_from is not None:
            shape, members = await self._after_drift(arm, round_, shape, members, drift_from)
            if not members:
                self._refuse(report, arm, round_, shape, "predates drift")
                return
        fold = self.fold(shape, members)
        report.shapes.append(shape.id)
        self._event("shape.formed", {"arm": arm, "round": round_, "shape_id": shape.id,
                                     "n_obs": len(members), "templates": sorted(shape.templates),
                                     "personas": sorted(shape.personas), "terms": sorted(shape.terms),
                                     "grouper": self.grouper.id, "drift_from": drift_from,
                                     "coherent_by": coherent(members) if len(members) > 1 else None,
                                     "holdout_templates": list(fold.templates),
                                     "nominated_shape_id": fold.shape.id})

        all_ids = shape.observation_ids
        existing = await self.drafts.get(draft_id(run_id, arm, round_, fold.shape.id))
        if existing is not None:   # idempotent re-run of this (arm, round)
            await self._resume(existing, all_ids, neighbours, at_idx, report)
            return
        reason = await self._bar(run_id, arm, round_, shape, members, at_idx, drift_from)
        to_close: list[Draft] = []
        if reason is None:
            reason, to_close = self._held(shape, held)
        if reason is not None:
            self._refuse(report, arm, round_, shape, reason)
            return
        try:
            nom = await self.nominator.nominate(run_id, arm, round_, fold.shape, fold.members, neighbours)
        except Exception as e:  # noqa: BLE001 - one failed nomination never sinks the round
            report.failed.append((shape.id, f"{type(e).__name__}: {e}"))
            self._event("nomination.failed", {"arm": arm, "round": round_, "shape_id": shape.id,
                                              "error": f"{type(e).__name__}: {e}"})
            return
        draft = self._with_fold(nom.draft, shape, members, fold)
        await self.drafts.put(draft)
        await self.observations.dispose(all_ids, ObservationDisposition.SHAPED, by=draft.id)
        report.drafts.append(draft.id)
        self._event("draft.written", draft_event(draft, nom.neighbours))
        for h in to_close:
            await self.drafts.set_status(h.id, DraftStatus.REFUSED)
            await self.drafts.record(h.id, LayerOutcome(layer=RENOMINATED, role=None, verdict=Verdict.REFUSE,
                                                        detail={"renominated_as": draft.id}))
            self._event("draft.renominated", {"arm": arm, "held": h.id, "successor": draft.id})
        shown = [o for o in members if o.id in set(draft.source_observation_ids)]
        await self._adjudicate(draft, all_ids, nom.neighbours, at_idx, report, shown)

    # --- the held-out template fold ------------------------------------------------------------------

    def fold(self, shape: Shape, members: Sequence[Observation]) -> Fold:
        """Withhold `holdout_templates` templates (fewest observations first; ties by a seeded hash of
        (shape, template)) when the shape spans >= BAR_MIN_TEMPLATES + HOLDOUT_TEMPLATES templates and the
        rest still clears the bar on its own. Otherwise nothing is withheld."""
        k = self.holdout_templates or 0
        whole = Fold(shape=shape, members=tuple(members), templates=(), withheld=())
        if k <= 0 or len(shape.templates) < self.bar.min_templates + k:
            return whole
        count = Counter(o.template for o in members)
        order = sorted(shape.templates, key=lambda t: (count[t], _unit(f"{self.holdout_seed or 0}:{shape.id}:{t}")))
        out = frozenset(order[:k])
        kept = [o for o in members if o.template not in out]
        rest = shape_of(kept)
        if not kept or not self.bar.clears(rest, kept):
            return whole
        return Fold(shape=rest, members=tuple(kept), templates=tuple(sorted(out)),
                    withheld=tuple(sorted(o.id for o in members if o.template in out)))

    def _with_fold(self, draft: Draft, shape: Shape, members: Sequence[Observation], fold: Fold) -> Draft:
        """Record the fold on the draft. A floor draft needs BAR_MIN_TEMPLATES_FLOOR templates at L1; if the
        fold leaves fewer, it is undone: the withheld observations join the warrant and the seen list
        (conservative: their episodes leave the backtest population), and nothing is held out."""
        if not fold.templates:
            return draft
        floor_need = self.min_templates_floor or 0
        if draft.kind is DecisionKind.FLOOR and len(fold.shape.templates) < floor_need:
            warrant = draft.warrant.model_copy(update={
                "source_observation_ids": shape.observation_ids, "source_episode_ids": shape.episode_ids,
                "templates": len(shape.templates)})
            seen = tuple(sorted(set(draft.nominator_seen_episode_ids) | set(shape.episode_ids)))
            self._event("holdout.undone", {"arm": draft.arm, "draft_id": draft.id, "kind": draft.kind.value,
                                           "templates": list(fold.templates)})
            return draft.model_copy(update={"warrant": warrant, "source_observation_ids": shape.observation_ids,
                                            "nominator_seen_episode_ids": seen})
        return draft.model_copy(update={"holdout_templates": fold.templates,
                                        "holdout_observation_ids": fold.withheld})

    async def _resume(self, draft: Draft, all_ids: Sequence[str], neighbours: Sequence[tuple[Any, float]],
                      at_idx: int, report: PassReport) -> None:
        """A pending draft (adjudication never finished) is re-adjudicated; a terminal one repairs its
        sources' disposition; a held one waits (its sources are open by the hold rule)."""
        ids = tuple(sorted(set(all_ids) | set(draft.source_observation_ids) | set(draft.holdout_observation_ids)))
        if draft.status is DraftStatus.PENDING:
            await self.observations.dispose(ids, ObservationDisposition.SHAPED, by=draft.id)
            report.resumed.append(draft.id)
            self._event("draft.resumed", {"arm": draft.arm, "draft_id": draft.id})
            shown = [o for o in await self._observations_by_id(draft.source_observation_ids)]
            await self._adjudicate(draft, ids, neighbours, at_idx, report, shown)
        elif draft.status in (DraftStatus.ADMITTED, DraftStatus.REFUSED):
            await self.observations.dispose(ids, ObservationDisposition.SPENT, by=draft.id)
            report.refused.append((draft.shape_id, "nominated"))
        else:
            report.refused.append((draft.shape_id, "held"))

    async def _observations_by_id(self, ids: Sequence[str]) -> list[Observation]:
        return [o for o in [await self.observations.get(i) for i in ids] if o is not None]

    async def _adjudicate(self, draft: Draft, ids: Sequence[str], neighbours: Sequence[tuple[Any, float]],
                          at_idx: int, report: PassReport, shown: Sequence[Observation]) -> None:
        """`shown` (the context's sources) holds only the observations the nominator saw; `ids` (every
        observation of the shape, the withheld fold included) follow the verdict's disposition."""
        ctx = CurationContext(run_id=draft.run_id, arm=draft.arm, at_idx=at_idx, sources=tuple(shown),
                              neighbours=tuple(neighbours))
        try:
            outcomes = await self.adjudicator.adjudicate(draft, ctx)
        except Exception as e:  # noqa: BLE001 - evidence is never stranded `shaped` by a failed adjudication
            await self.observations.dispose(ids, ObservationDisposition.OPEN, by=draft.id)
            report.failed.append((draft.id, f"{type(e).__name__}: {e}"))
            self._event("adjudication.failed", {"arm": draft.arm, "draft_id": draft.id,
                                                "error": f"{type(e).__name__}: {e}"})
            return
        report.outcomes[draft.id] = outcomes
        final = outcomes[-1].verdict if outcomes else None
        if final is Verdict.HOLD:
            await self.observations.dispose(ids, ObservationDisposition.OPEN, by=draft.id)
        elif final in (Verdict.ADMIT, Verdict.REFUSE):
            await self.observations.dispose(ids, ObservationDisposition.SPENT, by=draft.id)
        self._event("draft.adjudicated", {"arm": draft.arm, "draft_id": draft.id,
                                          "verdict": final.value if final else None,
                                          "layers": [o.layer for o in outcomes]})

    # --- steps ---------------------------------------------------------------------------------------

    async def _drift_start(self, neighbours: Sequence[tuple[Any, float]]) -> int | None:
        """The nearest contested neighbour's earliest open dispositive fire, dated by the first stream
        index of the episodes behind it (the fire's own `at_idx` if they cannot be read)."""
        if self.fires is None:
            return None
        contested = [d for d, _ in neighbours if d.evidence_state is EvidenceState.CONTESTED]
        if not contested:
            return None
        fires = [f for f in await self.fires.open_for(contested[0].id)
                 if f.role is FireRole.DISPOSITIVE and f.disposition is FireDisposition.OPEN]
        if not fires:
            return None
        first = min(fires, key=lambda f: f.at_idx)
        idxs = [e.idx for e in [await self.episodes.get(i) for i in first.episode_ids] if e is not None]
        return min([first.at_idx, *idxs])

    async def _after_drift(self, arm: str, round_: int, shape: Shape, members: list[Observation],
                           drift_from: int) -> tuple[Shape, list[Observation]]:
        """Pre-drift and post-drift evidence never mix: members whose episode predates the drift are left
        out of the shape (and stay open)."""
        kept = []
        for o in members:
            e = await self.episodes.get(o.episode_id)
            if e is not None and e.idx >= drift_from:
                kept.append(o)
        if len(kept) == len(members):
            return shape, members
        windowed = shape_of(kept) if kept else shape
        self._event("shape.windowed", {"arm": arm, "round": round_, "shape_id": shape.id,
                                       "into": windowed.id if kept else None, "drift_from": drift_from,
                                       "dropped": sorted({o.id for o in members} - {o.id for o in kept})})
        return windowed, kept

    async def _bar(self, run_id: str, arm: str, round_: int, shape: Shape, members: list[Observation],
                   at_idx: int, drift_from: int | None) -> str | None:
        clears = self.bar.clears(shape, members)
        self._event("bar.verdict", {"arm": arm, "round": round_, "shape_id": shape.id, "clears": clears,
                                    "n_obs": len(members), "templates": len(shape.templates),
                                    "min_obs": self.bar.min_obs, "min_templates": self.bar.min_templates})
        if not clears:
            return "bar"
        if not self.with_authority:
            return None
        flt = presentation_filter(shape)
        if drift_from is not None:
            read = await self.episodes.direction_read_window(run_id, arm, flt, before_idx=at_idx,
                                                             after_idx=drift_from)
        elif self.direction_window is not None:
            read = await self.episodes.direction_read_window(run_id, arm, flt, before_idx=at_idx,
                                                             last_n=self.direction_window)
        else:
            read = await self.episodes.direction_read(run_id, arm, flt, before_idx=at_idx)
        ok = self.bar.direction_clears(read)
        self._event("bar.direction_read", {
            "arm": arm, "round": round_, "shape_id": shape.id, "filter": flt, "n_in": read.n_in,
            "misses_in": read.misses_in, "n_out": read.n_out, "misses_out": read.misses_out, "gap": read.gap,
            "clears": ok, "min_gap": self.bar.min_gap, "min_matched": self.bar.min_matched,
            "after_idx": drift_from, "last_n": None if drift_from is not None else self.direction_window,
            "before_idx": at_idx})
        return None if ok else "direction"

    @staticmethod
    def _held(shape: Shape, held: Sequence[Draft]) -> tuple[str | None, list[Draft]]:
        """A held draft is never duplicated. A shape overlapping a held draft's sources re-nominates only
        when it strictly contains them — and, for an L1 hold (too few templates), adds a template; the held
        draft is then closed. Any other overlap waits (`held`)."""
        ids, close = set(shape.observation_ids), []
        for h in held:
            hs = set(h.source_observation_ids) | set(h.holdout_observation_ids)
            if not hs & ids:
                continue
            l1 = h.adjudication.get("L1")
            l1_hold = l1 is not None and l1.verdict is Verdict.HOLD
            if hs < ids and (not l1_hold or len(shape.templates) > h.warrant.templates + len(h.holdout_templates)):
                close.append(h)
            else:
                return "held", []
        return None, close

    def _refuse(self, report: PassReport, arm: str, round_: int, shape: Shape, reason: str) -> None:
        report.refused.append((shape.id, reason))
        self._event("shape.refused", {"arm": arm, "round": round_, "shape_id": shape.id, "reason": reason})

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
        "nominator_seen_episode_ids": list(draft.nominator_seen_episode_ids),
        "holdout_templates": list(draft.holdout_templates),
        "source_templates": draft.warrant.templates,
        "sources": len(draft.source_observation_ids),
    }
