"""The direct write path (SPEC § 5): `naive` and `self_ref`, no episodic pass.

`naive`: for each reducible observation, `Models.lesson(episode, observation)` writes one `Lesson`;
`self_ref`: `Models.self_grade(episode)` returns one on a self-judged miss. `lesson_entry` fills the entry
contract mechanically; the curator (`LessonShape` → `DirectAdmit`) admits it. A lesson within
NAIVE_MERGE_COSINE of an admitted decision is merged into it rather than admitted beside it.
"""

from __future__ import annotations

from dataclasses import dataclass

from munchhausen.domain.episode import Episode
from munchhausen.domain.observation import Observation
from munchhausen.ports.curation import Curator
from munchhausen.ports.models import Models


@dataclass
class DirectWriter:
    models: Models
    curator: Curator

    async def write(self, episode: Episode, observations: list[Observation]) -> None:
        raise NotImplementedError(
            "M3: lesson per reducible observation (naive) or self_grade (self_ref) → lesson_entry → "
            "Draft → curator.curate → merge at NAIVE_MERGE_COSINE, else lifecycle.admit")
