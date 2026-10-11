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

# First-cut per-episode signature predicates over (ratio, delta). M2: refine with question params
# (e.g. `date_offset` needs the window to cross a period boundary).
SIGNATURE_CHECKS: dict[Signature, Callable[[float | None, float | None], bool]] = {
    Signature.RATIO: lambda r, d: r is not None and abs(r - 1.0) > 1e-6,
    Signature.EXCLUSION: lambda r, d: d is not None and d != 0,
    Signature.SET_MEMBER: lambda r, d: d is not None and d != 0,
    Signature.THRESHOLD: lambda r, d: d is not None and d != 0,
    Signature.DATE_OFFSET: lambda r, d: d is not None and d != 0,
    Signature.ROUNDING: lambda r, d: d is not None and 0 < abs(d) < 1000,
}


def compute_residuals(episode_id: str, consulted: Sequence[Consultation], decisions: dict[str, Decision],
                      answer: Answer, figure: Answer, phrasing_terms: frozenset[str]) -> tuple[Residual, ...]:
    """One residual per `applied` decision on a miss with an authority figure."""
    applied = [decisions[c.decision_id] for c in consulted
               if c.disposition is Disposition.APPLIED and c.decision_id in decisions]
    ratio, delta = ratio_delta(answer, figure)
    out = []
    for d in applied:
        named = phrasing_terms & set(d.hook.fires_when.terms)
        others = set().union(*(set(o.hook.fires_when.terms) for o in applied if o.id != d.id))
        attributable = bool(named) and not (named & others)
        sig_match = any(SIGNATURE_CHECKS[r.signature](ratio, delta) for r in d.revisits)
        out.append(Residual(id=residual_id(episode_id, d.id), decision_id=d.id, answer=answer, figure=figure,
                            ratio=ratio, delta=delta, signature_match=sig_match, attributable=attributable))
    return tuple(out)


def guard_holds(recent: Sequence[Episode], decision_id: str, guard: Guard) -> tuple[bool, list[str], list[str]]:
    """≥ min_residuals attributable residuals within the decision's last `window` consultations."""
    window = sorted(recent, key=lambda e: e.idx, reverse=True)[: guard.window]
    hits = [(e.id, r.id) for e in window for r in e.residuals if r.decision_id == decision_id and r.attributable]
    return len(hits) >= guard.min_residuals, [h[0] for h in hits], [h[1] for h in hits]
