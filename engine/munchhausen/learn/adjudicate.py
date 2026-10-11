"""The stand-in adjudicator (SPEC § 7.3, § 14 departure 1): where a draft goes after nomination.

curator (L0 … L4) → on ADMIT: the admission plan (`domain/admission.plan_admission`) → `LifecycleService.admit`
(one transaction: insert, flip the predecessor, dispose its open fires `applied`, rewire tool access, close
the draft) → the lens-fit label. On HOLD the draft is kept `held` (L1: more observations; `hitl`: the
owner, L5). On REFUSE the draft is recorded `refused`. The draft's status is always set here; the source
observations' dispositions belong to the write path that nominated it (the episodic pass), never to the
adjudicator.

Every layer outcome is persisted on the draft (`drafts.adjudication.<layer>`) and traced. The owner port
(L5) disposes any held draft or any fire, recorded `disposer: owner`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from munchhausen.domain.admission import plan_admission
from munchhausen.domain.common import Disposer, FireDisposition, LayerRole, emb_key
from munchhausen.domain.decision import Decision, LifecycleError, Representation
from munchhausen.domain.draft import Draft, DraftStatus, LayerOutcome, Route, Verdict
from munchhausen.domain.ids import decision_id
from munchhausen.learn.curators import routed
from munchhausen.learn.lifecycle import LifecycleService
from munchhausen.ports.curation import CurationContext, Curator
from munchhausen.ports.representation import Representation as RepresentationPort
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import DecisionRepository, DraftRepository, FireRepository

_STATUS = {Verdict.ADMIT: DraftStatus.PENDING, Verdict.HOLD: DraftStatus.HELD, Verdict.REFUSE: DraftStatus.REFUSED,
           Verdict.PASS: DraftStatus.PENDING}


def decision_text(d: Decision | Draft) -> str:
    """What a decision is embedded and reranked as (`emb.<embedder>`, L2, semantic consultation)."""
    return f"{d.title}\n{d.payload}"


@dataclass
class Adjudicator:
    curator: Curator
    drafts: DraftRepository
    decisions: DecisionRepository
    fires: FireRepository
    lifecycle: LifecycleService
    view_name: Callable[[str, str], str]           # floor views `<collection>__<decision_id>` (store-owned name)
    representation: RepresentationPort | None = None
    trace: Trace | None = None

    async def adjudicate(self, draft: Draft, ctx: CurationContext) -> list[LayerOutcome]:
        prior = await self.drafts.get(draft.id)
        if prior is not None and prior.status in (DraftStatus.ADMITTED, DraftStatus.REFUSED):
            return list(prior.adjudication.values())          # idempotent per draft (resume, § 10.4)

        outcomes = await self.curator.curate(draft, ctx)
        final = outcomes[-1].verdict if outcomes else Verdict.REFUSE
        draft = routed(draft, outcomes)
        record = draft.model_copy(update={"adjudication": {o.layer: o for o in outcomes},
                                          "status": _STATUS[final], "explore": any(o.explore for o in outcomes)})
        await self.drafts.put(record)
        for o in outcomes:
            self._event("adjudication.layer", {"draft_id": draft.id, "arm": draft.arm, "layer": o.layer,
                                               "role": o.role.value if o.role else None, "verdict": o.verdict.value,
                                               "route": o.route.value if o.route else None,
                                               "neighbour_id": o.neighbour_id, "score": o.score, "detail": o.detail})
        if final is Verdict.ADMIT:
            try:
                await self.admit(record, ctx.at_idx, outcomes)
            except LifecycleError as e:   # e.g. the predecessor left `admitted` between L2 and commit
                final = Verdict.REFUSE
                await self.drafts.put(record.model_copy(update={"status": DraftStatus.REFUSED}))
                self._event("admission.failed", {"draft_id": draft.id, "error": str(e)})
        if any(o.role is LayerRole.DISPOSITIVE for o in outcomes):
            label = int(final is Verdict.ADMIT) if final is not Verdict.HOLD else None
            self._event("lensfit.label", {"draft_id": draft.id, "arm": draft.arm, "label": label,
                                          "lens_score": _score(outcomes, "L3")})
        self._event("adjudication", {"draft_id": draft.id, "arm": draft.arm, "verdict": final.value,
                                     "status": record.status.value, "curator": self.curator.name})
        return outcomes

    async def admit(self, draft: Draft, at_idx: int, outcomes: Sequence[LayerOutcome]) -> Decision:
        """Plan → lifecycle (the one transaction). Source observations are the write path's to dispose (the
        episodic pass: admit or refuse → spent, hold → open; the direct writer likewise)."""
        did = decision_id(draft.id)
        preds: list[Decision] = []
        for pid in _predecessor_ids(draft):
            p = await self.decisions.get(pid)
            if p is None:
                raise ValueError(f"{draft.id}: predecessor {pid} does not exist")
            preds.append(p)
        floor = draft.floor
        rep, emb = await self._embed(draft)
        l4 = next((o for o in outcomes if o.layer == "L4"), None)
        plan = plan_admission(draft, at_idx=at_idx, backtest_id=(l4.detail.get("backtest_id") if l4 else None),
                              lens_score=_score(outcomes, "L3"), predecessors=tuple(preds),
                              view_name=self.view_name(floor.collection, did) if floor else None, rep=rep, emb=emb)
        await self.lifecycle.admit(plan)
        return plan.decision

    # --- the owner port (L5) -------------------------------------------------------------------------

    async def owner_dispose_draft(self, draft_id: str, verdict: Verdict, at_idx: int, note: str = "") -> Draft:
        """L5 overrides L3–L4: `admit` a held or refused draft, or `refuse` a held one. Recorded as the
        draft's `L5` outcome with `disposer: owner`."""
        draft = await self.drafts.get(draft_id)
        if draft is None:
            raise ValueError(f"unknown draft {draft_id}")
        if draft.status is DraftStatus.ADMITTED:
            raise ValueError(f"{draft_id} is already admitted")
        if verdict not in (Verdict.ADMIT, Verdict.REFUSE):
            raise ValueError("the owner admits or refuses")
        l5 = LayerOutcome(layer="L5", role=None, verdict=verdict, detail={"disposer": Disposer.OWNER.value,
                                                                           "note": note, "at_idx": at_idx})
        outcomes = [*draft.adjudication.values(), l5]
        status = DraftStatus.PENDING if verdict is Verdict.ADMIT else DraftStatus.REFUSED
        record = draft.model_copy(update={"adjudication": {**draft.adjudication, "L5": l5}, "status": status})
        await self.drafts.put(record)
        self._event("owner.dispose", {"draft_id": draft_id, "verdict": verdict.value, "disposer": "owner",
                                      "note": note, "at_idx": at_idx})
        if verdict is Verdict.ADMIT:
            await self.admit(record, at_idx, outcomes)
        return record

    async def owner_dispose_fire(self, fire_id: str, disposition: FireDisposition, note: str = "") -> None:
        fire = await self.fires.get(fire_id)
        if fire is None:
            raise ValueError(f"unknown fire {fire_id}")
        await self.fires.dispose([fire_id], disposition, Disposer.OWNER)
        await self.decisions.refresh_evidence_state(fire.decision_id)
        self._event("owner.dispose", {"fire_id": fire_id, "decision_id": fire.decision_id,
                                      "disposition": disposition.value, "disposer": "owner", "note": note})

    # --- internals -----------------------------------------------------------------------------------

    async def _embed(self, draft: Draft) -> tuple[Representation | None, dict[str, list[float]] | None]:
        if self.representation is None:
            return None, None
        text = decision_text(draft)
        vecs = await self.representation.embed([text], "decision")
        if vecs is None or len(vecs) == 0:
            return None, None
        rid = self.representation.id
        rep = Representation(embedder_id=rid, text_hash=hashlib.sha1(text.encode()).hexdigest())
        return rep, {emb_key(rid): [float(x) for x in vecs[0]]}

    def _event(self, name: str, payload: dict[str, Any]) -> None:
        if self.trace is not None:
            self.trace.event(name, payload)


def _predecessor_ids(draft: Draft) -> tuple[str, ...]:
    if draft.route is Route.SUPERSEDE and draft.supersedes:
        return (draft.supersedes,)
    if draft.route is Route.REFINE:
        return draft.wiring.converged_from
    return ()


def _score(outcomes: Sequence[LayerOutcome], layer: str) -> float | None:
    return next((o.score for o in outcomes if o.layer == layer), None)
