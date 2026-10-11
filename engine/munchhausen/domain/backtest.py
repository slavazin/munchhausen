"""Backtest records and the admission rule (SPEC § 7.4). The dispositive layer's read is pure.

The read is paired: each sampled question is replayed twice under the arm's current admitted store, once
with the draft and once without it. Only the difference counts, so a miss the proposer re-solves by chance
in both replays fixes nothing, and a hit it loses in both breaks nothing.
"""

from __future__ import annotations

from enum import StrEnum

from munchhausen.domain.common import Record, Value


class BacktestVerdict(StrEnum):
    ADMIT = "admit"
    REFUSE = "refuse"


class BacktestSample(Value):
    episode_id: str
    template: str
    original_correct: bool            # the recorded first attempt; a sampling stratum, not the counterfactual
    replay_correct: bool              # replay with the draft, against the confirmed figure
    baseline_correct: bool            # paired replay without the draft, same context
    context: tuple[str, ...] = ()     # admitted decision ids both replays consulted (current store)

    @property
    def fixed(self) -> bool:
        return self.replay_correct and not self.baseline_correct

    @property
    def broken(self) -> bool:
        return self.baseline_correct and not self.replay_correct


class BacktestThresholds(Value):
    min_fixed: int
    min_fixed_heldout: int
    max_broken: int


class Backtest(Record):
    draft_id: str
    sampled: tuple[BacktestSample, ...]
    source_templates: frozenset[str]
    fixed: int
    fixed_heldout: int
    broken: int
    verdict: BacktestVerdict

    @classmethod
    def read(
        cls,
        *,
        id: str,
        run_id: str,
        arm: str,
        draft_id: str,
        sampled: tuple[BacktestSample, ...],
        source_templates: frozenset[str],
        thresholds: BacktestThresholds,
    ) -> Backtest:
        fixed = [s for s in sampled if s.fixed]
        fixed_heldout = sum(1 for s in fixed if s.template not in source_templates)
        broken = sum(1 for s in sampled if s.broken)
        admit = (
            len(fixed) >= thresholds.min_fixed
            and fixed_heldout >= thresholds.min_fixed_heldout
            and broken <= thresholds.max_broken
        )
        return cls(
            _id=id, run_id=run_id, arm=arm, draft_id=draft_id, sampled=sampled,
            source_templates=source_templates, fixed=len(fixed), fixed_heldout=fixed_heldout, broken=broken,
            verdict=BacktestVerdict.ADMIT if admit else BacktestVerdict.REFUSE,
        )
