"""Backtest (SPEC § 7.4): the dispositive layer.

Population: episodes whose questions the draft's hook matches, minus the draft's sources; for a supersede
draft, only after the predecessor's earliest open dispositive fire. Balanced sample of ≤ BACKTEST_N.
Replay, paired: for each sampled question, consult the arm's **current** admitted store (minus the
predecessor), then run the proposer twice on that context — once with the draft, once without. Both
replays are scored against the episode's confirmed figure — never `truth.gold`. `fixed` and `broken` read
the difference between the two replays (`domain/backtest.py`); the episode's recorded outcome is only the
sampling stratum. Cost: 2 × BACKTEST_N proposer calls per draft.
"""

from __future__ import annotations

from dataclasses import dataclass

from munchhausen.agent.consultation import Consulter
from munchhausen.agent.proposer import Proposer
from munchhausen.domain.backtest import Backtest, BacktestThresholds
from munchhausen.domain.draft import Draft
from munchhausen.ports.store import DocumentReader, EpisodeRepository, FireRepository


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

    async def run(self, draft: Draft) -> Backtest:
        raise NotImplementedError(
            "M3: population → per episode: consulter.consult(question) − predecessor → replay with draft "
            "and without (stage='replay') → matches(confirmed_figure) each → BacktestSample(context=…) "
            "→ Backtest.read(thresholds) → backtests.put")
