"""Episodic pass (SPEC § 7.2), once per (arm, round); idempotent.

group (Grouper port) → coherence guard → bar → nominate → curate. The guard and the bar are pure and
live here; grouping and nomination are ports.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from munchhausen.domain.draft import Shape
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

    def clears(self, shape: Shape, members: Sequence[Observation]) -> bool:
        """≥ min_obs observations from ≥ min_templates templates; persona-scoped shapes need ≥ 2
        observations from the same persona."""
        if len(members) < self.min_obs or len(shape.templates) < self.min_templates:
            return False
        if len(shape.personas) == 1:
            return len(members) >= 2
        return True


@dataclass
class EpisodicPass:
    async def run(self, run_id: str, arm: str, round_: int) -> None:
        raise NotImplementedError(
            "M3: open observations (carry CARRY_ROUNDS) → Grouper.group → coherence_guard → Bar → "
            "Nominator → Draft → Curator.curate → lifecycle.admit on ADMIT; mark observations shaped/spent")
