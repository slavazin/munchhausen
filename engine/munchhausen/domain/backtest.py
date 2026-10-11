"""Backtest records and the admission rule (SPEC § 7.4). The dispositive layer's read is pure.

The read is paired: each sampled question is replayed twice under the arm's current admitted store, once
with the draft and once without it. Only the difference counts, so a miss the proposer re-solves by chance
in both replays fixes nothing, and a hit it loses in both breaks nothing.
"""

from __future__ import annotations

from enum import StrEnum

from munchhausen.domain.common import Answer, Record, Value


class BacktestVerdict(StrEnum):
    ADMIT = "admit"
    REFUSE = "refuse"
    INSUFFICIENT = "insufficient"   # fewer than BACKTEST_MIN_N scored pairs: the read did not happen (L4 holds)
    AWAITING_HELDOUT = "awaiting_heldout"   # no held-out fold, and only the held-out fix is missing (L4 holds)


class BacktestSample(Value):
    episode_id: str
    template: str
    original_correct: bool            # the recorded first attempt; a sampling stratum, not the counterfactual
    replay_correct: bool              # replay with the draft, against the confirmed figure
    baseline_correct: bool            # paired replay without the draft, same context
    context: tuple[str, ...] = ()     # admitted decision ids both replays consulted (current store)
    applied: bool | None = None       # the with-draft replay recorded the draft `applied` (None: not recorded)
    replay_answer: Answer = None
    baseline_answer: Answer = None

    @property
    def fixed(self) -> bool:
        """A fix counts only where the with-draft replay applied the draft: a flip the proposer reached
        without applying it is replay noise, not the draft's effect."""
        return self.replay_correct and not self.baseline_correct and self.applied is not False

    @property
    def broken(self) -> bool:
        return self.baseline_correct and not self.replay_correct


class BacktestThresholds(Value):
    min_fixed: int
    min_fixed_heldout: int
    max_broken: int
    min_n: int = 0                    # scored pairs below this: INSUFFICIENT, never a refusal


class Backtest(Record):
    draft_id: str
    sampled: tuple[BacktestSample, ...]
    source_templates: frozenset[str]
    fixed: int
    fixed_heldout: int
    broken: int
    verdict: BacktestVerdict
    errors: tuple[str, ...] = ()      # pairs dropped because a replay or consultation raised
    at_idx: int | None = None         # the adjudication index this read belongs to
    holdout_reserved: int = 0         # sample slots reserved for the draft's held-out templates
    holdout_available: int | None = None   # held-out episodes the population supplied (≤ reserved); None: no fold

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
        errors: tuple[str, ...] = (),
        at_idx: int | None = None,
        holdout_reserved: int = 0,
        holdout_available: int | None = None,
        holdout_fold: bool = True,
    ) -> Backtest:
        """Admit on `fixed ≥ min ∧ fixed − broken ≥ min ∧ fixed_heldout ≥ min ∧ broken ≤ max`; fewer than
        `min_n` scored pairs is INSUFFICIENT (the backtest could not read, so it neither admits nor refuses)."""
        fixed = [s for s in sampled if s.fixed]
        fixed_heldout = sum(1 for s in fixed if s.template not in source_templates)
        broken = sum(1 for s in sampled if s.broken)
        admit = (
            len(fixed) >= thresholds.min_fixed
            and len(fixed) - broken >= thresholds.min_fixed
            and fixed_heldout >= thresholds.min_fixed_heldout
            and broken <= thresholds.max_broken
        )
        verdict = BacktestVerdict.ADMIT if admit else BacktestVerdict.REFUSE
        clears_but_heldout = (
            len(fixed) >= thresholds.min_fixed
            and len(fixed) - broken >= thresholds.min_fixed
            and broken <= thresholds.max_broken
            and fixed_heldout < thresholds.min_fixed_heldout
        )
        if not holdout_fold and clears_but_heldout:
            # a shape too narrow to fold (2 templates) cannot show a held-out fix yet: hold it to accrue a
            # template rather than refuse it and spend its evidence (approved departure, 2026-10-11)
            verdict = BacktestVerdict.AWAITING_HELDOUT
        if len(sampled) < thresholds.min_n:
            verdict = BacktestVerdict.INSUFFICIENT
        return cls(
            _id=id, run_id=run_id, arm=arm, draft_id=draft_id, sampled=sampled,
            source_templates=source_templates, fixed=len(fixed), fixed_heldout=fixed_heldout, broken=broken,
            verdict=verdict, errors=errors, at_idx=at_idx, holdout_reserved=holdout_reserved,
            holdout_available=holdout_available,
        )
