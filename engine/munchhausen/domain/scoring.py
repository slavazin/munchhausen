"""Scoring (SPEC § 4.4): pure comparison of an answer against an expected figure.

Numbers: relative tolerance (absolute tolerance after Claire rounding). Lists: set equality after
lower-casing. Only the first attempt counts toward accuracy — the caller decides which attempt this is.
"""

from __future__ import annotations

import math

from munchhausen.domain.common import Answer


def matches(answer: Answer, expected: Answer, *, rel_tol: float, abs_tol: float = 0.0) -> bool:
    if answer is None or expected is None:
        return False
    if isinstance(expected, list) or isinstance(answer, list):
        if not (isinstance(expected, list) and isinstance(answer, list)):
            return False
        return {str(a).strip().lower() for a in answer} == {str(e).strip().lower() for e in expected}
    return math.isclose(float(answer), float(expected), rel_tol=rel_tol, abs_tol=abs_tol)


def ratio_delta(answer: Answer, figure: Answer) -> tuple[float | None, float | None]:
    """The residual's numeric gap: answer/figure and answer−figure, where both are numbers."""
    if isinstance(answer, (int, float)) and isinstance(figure, (int, float)):
        ratio = float(answer) / float(figure) if figure else None
        return ratio, float(answer) - float(figure)
    return None, None
