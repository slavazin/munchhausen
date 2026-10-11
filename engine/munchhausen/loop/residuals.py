"""Residuals and revisit guards (SPEC § 6.3). Computed in the harness, mechanically, from stored
figures — never by asking the proposer whether its decisions held."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from munchhausen.domain.common import Answer, Disposition, Signature
from munchhausen.domain.decision import Decision
from munchhausen.domain.episode import Consultation, Episode, Residual
from munchhausen.domain.ids import residual_id
from munchhausen.domain.latches import Guard
from munchhausen.domain.scoring import ratio_delta

# Per-episode signature predicates over (ratio, delta, figure). Every one but ROUNDING reduces to "the answer
# differs", so on its own a per-episode check discriminates little. The discriminating read is the guard's: a
# shifted world moves one decision's answers the same way on every consultation (D1 undercounts active
# customers each time), while poisoned figures and residuals borrowed from another quirk scatter.
# ROUNDING is derived from the figure, never from a pack: the gap lies within half the figure's rounding unit
# (the largest power of `base` dividing it), so a figure of 1,204,000 tolerates a gap ≤ 500 and 1,204 one ≤ 0.5.
# `date_offset` needs question params (a boundary-crossing window) the Question does not carry: post-event.
Check = Callable[[float | None, float | None, float | None, int], bool]


def rounding_unit(figure: float, base: int) -> float:
    """The largest power of `base` that divides `round(figure)` (1 for a figure that is not round)."""
    n, unit = abs(round(figure)), 1
    while n and n % (unit * base) == 0:
        unit *= base
    return float(unit)


def _rounding(r: float | None, d: float | None, f: float | None, base: int) -> bool:
    return d is not None and f is not None and 0 < abs(d) <= rounding_unit(f, base) / 2


SIGNATURE_CHECKS: dict[Signature, Check] = {
    Signature.RATIO: lambda r, d, f, b: r is not None and abs(r - 1.0) > 1e-6,
    Signature.EXCLUSION: lambda r, d, f, b: d is not None and d != 0,
    Signature.SET_MEMBER: lambda r, d, f, b: d is not None and d != 0,
    Signature.THRESHOLD: lambda r, d, f, b: d is not None and d != 0,
    Signature.DATE_OFFSET: lambda r, d, f, b: d is not None and d != 0,
    Signature.ROUNDING: _rounding,
}


def compute_residuals(episode_id: str, consulted: Sequence[Consultation], decisions: dict[str, Decision],
                      answer: Answer, figure: Answer, phrasing_terms: frozenset[str], *,
                      rounding_base: int) -> tuple[Residual, ...]:
    """One residual per `applied` decision on a miss with an authority figure (SPEC § 6.3).

    Attributable: the authority's phrasing names a concept in the decision's `fires_when`, and no other
    applied decision's hook names that concept (some named concept is this decision's alone)."""
    applied = [decisions[c.decision_id] for c in consulted
               if c.disposition is Disposition.APPLIED and c.decision_id in decisions]
    ratio, delta = ratio_delta(answer, figure)
    fig = float(figure) if isinstance(figure, (int, float)) else None
    out = []
    for d in applied:
        named = phrasing_terms & set(d.hook.fires_when.terms)
        others = set().union(*(set(o.hook.fires_when.terms) for o in applied if o.id != d.id))
        attributable = bool(named - others)
        sig_match = any(SIGNATURE_CHECKS[r.signature](ratio, delta, fig, rounding_base) for r in d.revisits)
        out.append(Residual(id=residual_id(episode_id, d.id), decision_id=d.id, answer=answer, figure=figure,
                            ratio=ratio, delta=delta, signature_match=sig_match, attributable=attributable))
    return tuple(out)


def guard_holds(recent: Sequence[Episode], decision_id: str, guard: Guard) -> tuple[bool, list[str], list[str]]:
    """≥ min_residuals residuals within the decision's last `window` consultations that are attributable,
    signature-matched, and agree in direction (the sign of answer − figure). Returns the largest agreeing
    group's episode and residual ids."""
    window = sorted((e for e in recent if e.stream == "stream"), key=lambda e: e.idx, reverse=True)[: guard.window]
    by_sign: dict[int, list[tuple[str, str]]] = {}
    for e in window:
        for r in e.residuals:
            if r.decision_id == decision_id and r.attributable and r.signature_match:
                by_sign.setdefault(_sign(r.delta), []).append((e.id, r.id))
    hits = max(by_sign.values(), key=len, default=[])
    return len(hits) >= guard.min_residuals, [h[0] for h in hits], [h[1] for h in hits]


def _sign(delta: float | None) -> int:
    """Direction of a residual; non-numeric answers (sets) share one group."""
    return 0 if delta is None else (delta > 0) - (delta < 0)
