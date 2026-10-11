"""Lifecycle service (SPEC § 7.5, § 8): orchestrates admission and terminal transitions across the
decision store, floor views and the memory sink. The decision store's own write path is
`DecisionRepository`'s six functions; this service is their only caller.

View DDL is not transactional. Order, for every transition: create the successor's view → commit the
store transaction (which rewires or deletes `tool_access` rows) → drop the views the commit released. A
crash between steps leaves an unused view, never a register row pointing at a missing view.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from munchhausen.domain.admission import Admission
from munchhausen.domain.common import Disposer, FireDisposition, FireRole
from munchhausen.domain.decision import Decision
from munchhausen.domain.pipeline_guard import check_floor
from munchhausen.ports.sinks import MemorySink, Trace
from munchhausen.ports.store import (
    DecisionRepository,
    EpisodeRepository,
    FireRepository,
    ToolAccessRepository,
    WorldWriter,
)

FLOOR_VIEW_NAME = re.compile(r"[A-Za-z0-9_.]+__D-[0-9a-f]+")


@dataclass
class LifecycleService:
    decisions: DecisionRepository
    world: WorldWriter
    sink: MemorySink
    tool_access: ToolAccessRepository | None = None
    fires: FireRepository | None = None
    episodes: EpisodeRepository | None = None
    trace: Trace | None = None
    retire_idle: int | None = None        # RETIRE_IDLE, unless the decision's retire latch names its own
    retire_fires: int | None = None       # RETIRE_FIRES, likewise

    async def admit(self, plan: Admission) -> None:
        """Successor view → one transaction (insert, flip predecessors, dispose their fires `applied`,
        rewire tool access, close the draft) → drop the predecessors' views → sink."""
        d = plan.decision
        floor = d.floor
        if plan.rewire is not None and floor is not None:
            # S2 sandbox: the floor's definition passes the pipeline guard before any DDL (raises PipelineRefused)
            check_floor(floor.collection, floor.match, collections=await self.world.collection_names())
            await self.world.create_view(plan.rewire.view, floor.collection, [{"$match": floor.match}])
            self._event("view.create", {"view": plan.rewire.view, "on": floor.collection, "match": floor.match,
                                        "decision_id": d.id})
        released = await self._views_of(d.run_id, d.arm, plan.restore_views_of)
        if d.wiring.supersedes:
            await self.decisions.supersede(plan)
        elif d.wiring.converged_from:
            await self.decisions.converge(plan)
        else:
            await self.decisions.admit(plan)
        self._event("admission", {"decision_id": d.id, "draft_id": plan.draft_id, "kind": d.kind.value,
                                  "at_idx": d.lifecycle.at_idx, "backtest_id": d.warrant.backtest_id,
                                  "flips": [{"decision_id": f.decision_id, "status": f.lifecycle.status.value}
                                            for f in plan.flips],
                                  "rewire": plan.rewire.model_dump() if plan.rewire else None,
                                  "restore_views_of": list(plan.restore_views_of)})
        if plan.rewire is not None:
            self._event("tool_access.rewire", {**plan.rewire.model_dump(), "released": released})
        await self._drop(released, by=d.id)
        for flip in plan.flips:
            await self.decisions.refresh_evidence_state(flip.decision_id)
            await self.sink.withdraw(flip.decision_id, flip.lifecycle.status.value)
        await self.sink.publish(d)

    async def moot(self, decision: Decision, at_idx: int, reason: str) -> None:
        released = await self._views_of(decision.run_id, decision.arm, (decision.id,))
        await self.decisions.moot(decision.id, at_idx, reason)
        await self._after_terminal(decision, "moot", at_idx, reason, released)

    async def retire(self, decision: Decision, at_idx: int, reason: str) -> None:
        released = await self._views_of(decision.run_id, decision.arm, (decision.id,))
        await self.decisions.retire(decision.id, at_idx, reason)
        if self.fires is not None:   # retirement is the consumer acting on the fires: dispose them applied
            open_ids = [f.id for f in await self.fires.open_for(decision.id)]
            if open_ids:
                await self.fires.dispose(open_ids, FireDisposition.APPLIED, Disposer.LIFECYCLE)
                self._event("fire.dispose", {"fire_ids": open_ids, "disposition": "applied",
                                             "disposer": "lifecycle", "by": "retire"})
            await self.decisions.refresh_evidence_state(decision.id)
        await self._after_terminal(decision, "retired", at_idx, reason, released)

    async def sweep(self, run_id: str, arm: str, at_idx: int) -> dict[str, list[str]]:
        """At each round close (§ 7.5): refresh every admitted decision's evidence state; moot a decision
        no consultation matched for its idle window; retire one whose **dispositive** fires, counted from its
        first open one, reached the limit with no successor admitted. Corroborating fires (anomalies,
        unattributed residuals) never settle anything (§ 6.3), so they never retire a decision: at a drift,
        retirement must not beat the supersession the open fire is waiting for. Moot reads consultations
        (episodes' `consulted`), retire reads fires; neither reads correctness."""
        out: dict[str, list[str]] = {"moot": [], "retired": [], "contested": []}
        for d in await self.decisions.admitted(run_id, arm):
            await self.decisions.refresh_evidence_state(d.id)
            idle_limit = d.retire_latch.moot_when.idle_episodes if d.retire_latch else self.retire_idle
            fire_limit = d.retire_latch.max_fires if d.retire_latch else self.retire_fires
            fires = await self.fires.for_decision(d.id) if self.fires is not None else []
            dispositive = [f for f in fires if f.role is FireRole.DISPOSITIVE]
            opened = [f.at_idx for f in dispositive if f.disposition is FireDisposition.OPEN]
            if opened:
                out["contested"].append(d.id)
            counted = [f for f in dispositive if opened and f.at_idx >= min(opened)]
            if opened and fire_limit is not None and len(counted) >= fire_limit:
                await self.retire(d, at_idx, f"{len(counted)} dispositive fires without a successor "
                                             f"(limit {fire_limit})")
                out["retired"].append(d.id)
                continue
            if idle_limit is not None and self.episodes is not None:
                last = await self.episodes.consultations_of(run_id, arm, d.id, 1)
                since = max([d.lifecycle.at_idx, *(e.idx for e in last)])
                if at_idx - since >= idle_limit:
                    await self.moot(d, at_idx, f"no consultation for {at_idx - since} episodes (limit {idle_limit})")
                    out["moot"].append(d.id)
        self._event("lifecycle.sweep", {"run_id": run_id, "arm": arm, "at_idx": at_idx, **out})
        return out

    # --- internals -----------------------------------------------------------------------------------

    async def _after_terminal(self, d: Decision, status: str, at_idx: int, reason: str, released: list[str]) -> None:
        self._event(f"lifecycle.{status}", {"decision_id": d.id, "at_idx": at_idx, "reason": reason,
                                             "released_views": released})
        await self._drop(released, by=d.id)
        await self.sink.withdraw(d.id, status)

    async def _views_of(self, run_id: str, arm: str, decision_ids: tuple[str, ...]) -> list[str]:
        if not decision_ids or self.tool_access is None:
            return []
        wanted = set(decision_ids)
        return [t.view for t in await self.tool_access.rewires(run_id, arm) if t.decision_id in wanted]

    async def _drop(self, views: list[str], *, by: str) -> None:
        """Drops only floor views (`<collection>__D-<hash>`, SPEC § 8): a register row naming anything else
        is refused and traced, never dropped."""
        for v in views:
            if not FLOOR_VIEW_NAME.fullmatch(v):
                self._event("view.drop_refused", {"view": v, "by": by})
                continue
            await self.world.drop_view(v)
            self._event("view.drop", {"view": v, "by": by})

    def _event(self, name: str, payload: dict[str, Any]) -> None:
        if self.trace is not None:
            self.trace.event(name, payload)
