"""Backtest records and the admission rule (SPEC § 7.4). The dispositive layer's read is pure."""

from __future__ import annotations

from enum import StrEnum

from munchhausen.domain.common import Record, Value


class BacktestVerdict(StrEnum):
    ADMIT = "admit"
    REFUSE = "refuse"


class BacktestSample(Value):
    episode_id: str
    template: str
    original_correct: bool
    replay_correct: bool

    @property
    def fixed(self) -> bool:
        return not self.original_correct and self.replay_correct

    @property
    def broken(self) -> bool:
        return self.original_correct and not self.replay_correct


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
