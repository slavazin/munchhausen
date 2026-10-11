"""Episodic pass (SPEC § 7.2), once per (arm, round); idempotent.

group (Grouper port) → coherence guard → bar → nominate → curate. The guard and the bar are pure and
live here; grouping and nomination are ports.

Every open observation is carried until a shape spends it (CARRY_ROUNDS unset): evidence for a rare
template or one persona arrives slowly, and an expiry window shorter than its arrival rate refuses it
by construction.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from munchhausen.domain.draft import DirectionRead, Shape
from munchhausen.domain.ids import shape_id
from munchhausen.domain.observation import Observation


def coherence_guard(shape: Shape, members: Sequence[Observation]) -> list[Shape]:
    """A cluster whose members share no normalized term or authority phrasing is split by term.
    The guard checks the grouping and proposes nothing."""
    shared_terms = set.intersection(*(set(o.surfaces.terms) for o in members)) if members else set()
    phrasings = {o.surfaces.phrasing for o in members if o.surfaces.phrasing}
    if shared_terms or (len(phrasings) == 1 and len(members) > 1):
        return [shape]
    by_term: dict[str, list[Observation]] = {}
    for o in members:
        for t in o.surfaces.terms or ("",):
            by_term.setdefault(t, []).append(o)
    out = []
    for t, group in by_term.items():
        if not t:
            continue
        ids = tuple(sorted({o.id for o in group}))
        out.append(Shape(id=shape_id(ids), observation_ids=ids,
                         episode_ids=tuple(sorted({o.episode_id for o in group})),
                         templates=frozenset(o.template for o in group),
                         personas=frozenset(o.persona for o in group), terms=frozenset({t})))
    return out


@dataclass(frozen=True)
class Bar:
    min_obs: int
    min_templates: int
    min_gap: float          # BAR_MIN_GAP: miss rate inside the shape's presentation minus outside it
    min_matched: int        # BAR_MIN_MATCHED: episodes the presentation must match before the gap reads

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
class EpisodicPass:
    async def run(self, run_id: str, arm: str, round_: int) -> None:
        raise NotImplementedError(
            "M3: open observations (all, or the last CARRY_ROUNDS) → Grouper.group → coherence_guard → "
            "Bar.clears → episodes.direction_read(presentation_filter) → Bar.direction_clears → Nominator "
            "→ Draft → Curator.curate → lifecycle.admit on ADMIT; mark observations shaped/spent")
