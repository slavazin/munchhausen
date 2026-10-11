"""Lifecycle service (SPEC § 7.5, § 8): orchestrates admission and terminal transitions across the
decision store, floor views and the memory sink. The decision store's own write path is
`DecisionRepository`'s six functions; this service is their only caller."""

from __future__ import annotations

from dataclasses import dataclass

from munchhausen.domain.admission import Admission
from munchhausen.ports.sinks import MemorySink
from munchhausen.ports.store import DecisionRepository, WorldWriter


@dataclass
class LifecycleService:
    decisions: DecisionRepository
    world: WorldWriter
    sink: MemorySink

    async def admit(self, plan: Admission) -> None:
        """View DDL is not transactional: create the successor's view first, commit, then drop
        predecessors' views. A crash between steps leaves an unused view, repaired on resume."""
        floor = plan.decision.floor
        if plan.rewire is not None and floor is not None:
            await self.world.create_view(plan.rewire.view, floor.collection, [{"$match": floor.match}])
        if plan.decision.wiring.supersedes:
            await self.decisions.supersede(plan)
        elif plan.decision.wiring.converged_from:
            await self.decisions.converge(plan)
        else:
            await self.decisions.admit(plan)
        for flip in plan.flips:
            await self.sink.withdraw(flip.decision_id, flip.lifecycle.status.value)
        await self.sink.publish(plan.decision)
        # M3: drop views of plan.restore_views_of (names from tool_access history)

    async def sweep(self, run_id: str, arm: str, at_idx: int) -> None:
        raise NotImplementedError("M3: moot after RETIRE_IDLE idle episodes; retire at RETIRE_FIRES without successor")
