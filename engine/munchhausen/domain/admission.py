"""Admission as a plan: the pure description of one atomic write (SPEC § 7.5, § 20.2 transactions).

The domain decides *what* changes; `store/decisions.py` commits the plan in one transaction:
insert the successor, flip predecessors, dispose their open fires, rewire tool access, close the draft.
"""

from __future__ import annotations

from munchhausen.domain.common import DecisionKind, LifecycleStatus, Value
from munchhausen.domain.decision import Decision, Lifecycle, Representation
from munchhausen.domain.draft import Draft, Route
from munchhausen.domain.ids import decision_id
from munchhausen.domain.latches import WiringLatch
from munchhausen.domain.registers import ToolAccess


class PredecessorFlip(Value):
    decision_id: str
    lifecycle: Lifecycle


class Admission(Value):
    decision: Decision
    draft_id: str
    flips: tuple[PredecessorFlip, ...] = ()
    rewire: ToolAccess | None = None          # set when the decision is a floor
    restore_views_of: tuple[str, ...] = ()    # predecessor floor decisions whose views are dropped


def plan_admission(
    draft: Draft,
    *,
    at_idx: int,
    backtest_id: str,
    lens_score: float | None,
    predecessors: tuple[Decision, ...] = (),
    view_name: str | None = None,
    rep: Representation | None = None,
    emb: dict[str, list[float]] | None = None,
) -> Admission:
    """Turn a draft that passed its dispositive layer into an admission plan."""
    did = decision_id(draft.id)
    supersedes = draft.supersedes if draft.route is Route.SUPERSEDE else None
    converged_from = tuple(p.id for p in predecessors) if draft.route is Route.REFINE else ()
    wiring = WiringLatch.build(supersedes=supersedes, converged_from=converged_from)
    latches = tuple(lt for lt in draft.latches if not isinstance(lt, WiringLatch)) + (wiring,)
    warrant = draft.warrant.model_copy(update={"backtest_id": backtest_id, "lens_score": lens_score})

    decision = Decision(
        _id=did, run_id=draft.run_id, arm=draft.arm,
        title=draft.title, kind=draft.kind, payload=draft.payload, options=draft.options,
        forecloses=draft.forecloses, latches=latches, residue=draft.residue, warrant=warrant,
        lifecycle=Lifecycle(status=LifecycleStatus.ADMITTED, at_idx=at_idx),
        rep=rep, emb=emb or {}, admitted_at_idx=at_idx,
    )

    flips: list[PredecessorFlip] = []
    for p in predecessors:
        if supersedes and p.id == supersedes:
            flips.append(PredecessorFlip(decision_id=p.id, lifecycle=p.lifecycle.supersede(did, at_idx)))
        elif p.id in converged_from:
            flips.append(PredecessorFlip(decision_id=p.id, lifecycle=p.lifecycle.converge(did, at_idx)))

    rewire = None
    if decision.kind is DecisionKind.FLOOR and decision.floor is not None:
        if view_name is None:
            raise ValueError("a floor admission needs the view name it rewires to")
        rewire = ToolAccess(run_id=draft.run_id, arm=draft.arm, logical=decision.floor.collection,
                            view=view_name, decision_id=did)
    restore = tuple(p.id for p in predecessors if p.kind is DecisionKind.FLOOR and p.id != did)
    return Admission(decision=decision, draft_id=draft.id, flips=tuple(flips), rewire=rewire,
                     restore_views_of=restore)
