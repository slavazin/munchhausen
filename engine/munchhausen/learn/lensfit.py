"""Second-order loop (SPEC § 9; stretch; its own process). Grades the adjudicator only on backtest and
lifecycle outcomes — never on its own L3 verdicts."""

from __future__ import annotations


async def fit_once() -> None:
    raise NotImplementedError("M5: labels from L4 outcomes (relabel on early supersede/retire) → prequential "
                              "AUC → fold ρ > LENS_FOLD_RHO → LogisticRegression → lens_weights version")
