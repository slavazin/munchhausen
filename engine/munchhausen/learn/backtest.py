"""Backtest (SPEC § 7.4): the dispositive layer.

Population: episodes whose questions the draft's hook matches, minus the draft's sources; for a supersede
draft, only after the predecessor's earliest open dispositive fire. Balanced sample of ≤ BACKTEST_N.
Replay: re-run the proposer with each episode's consulted decisions plus the draft (minus the
predecessor). Score against the episode's confirmed figure — never `truth.gold`.
"""

from __future__ import annotations

from dataclasses import dataclass

from munchhausen.agent.proposer import Proposer
from munchhausen.domain.backtest import Backtest, BacktestThresholds
from munchhausen.domain.draft import Draft
from munchhausen.ports.store import DecisionRepository, DocumentReader, EpisodeRepository, FireRepository


@dataclass
class Backtester:
    episodes: EpisodeRepository
    decisions: DecisionRepository
    fires: FireRepository
    proposer: Proposer
    world: DocumentReader
    thresholds: BacktestThresholds
    n: int
    rel_tol: float
    max_time_ms: int

    async def run(self, draft: Draft) -> Backtest:
        raise NotImplementedError(
            "M3: population → replay each with consulted ∪ {draft} − predecessor → matches(confirmed_figure) "
            "→ Backtest.read(thresholds) → backtests.put")
