"""Per-episode model usage (S2): a context variable the forward pass sets for the span of one episode.

`ForwardPass.run` binds an `EpisodeUsage`; the shared call path (`impl/models_anthropic._record`) stamps
`episode_id` into each spend row's meta and adds the call's tokens. Context variables follow asyncio tasks
(each child task copies the context, and the accumulator is shared by reference), so concurrent episodes
never mix. Nothing on the learning path reads it; `episodes.tokens` is a record of cost, not a signal.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class EpisodeUsage:
    episode_id: str
    tokens: dict[str, int] = field(default_factory=lambda: {"in": 0, "out": 0, "calls": 0})

    def add(self, tokens_in: int, tokens_out: int) -> None:
        self.tokens["in"] += tokens_in
        self.tokens["out"] += tokens_out
        self.tokens["calls"] += 1


CURRENT_EPISODE: ContextVar[EpisodeUsage | None] = ContextVar("munchhausen_current_episode", default=None)
