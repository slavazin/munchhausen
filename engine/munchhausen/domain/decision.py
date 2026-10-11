"""The entry contract (SPEC § 10.2) and the decision lifecycle (§ 7.5).

`EntryContract` is shared by drafts and decisions. A `Decision` is frozen at admission: only
`lifecycle`, `evidence_state` and `amendments` change afterwards, and only through the transitions
defined here. Persistence of those transitions has one home: `store/decisions.py`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Literal

from pydantic import Field

from munchhausen.domain.common import (
    DecisionKind,
    EvidenceState,
    FireDisposition,
    FireRole,
    LifecycleStatus,
    Record,
    Value,
)
from munchhausen.domain.latches import FloorLatch, HookLatch, Latch, RetireLatch, RevisitLatch, WiringLatch
from munchhausen.domain.pipeline_guard import PipelineRefused, check


class LifecycleError(ValueError):
    """An illegal lifecycle transition (e.g. superseding a decision that is not admitted)."""


class Option(Value):
    definition: str
    figures_reproduced: tuple[str, ...] = ()   # episode ids whose confirmed figure the definition reproduces
    verdict: Literal["chosen", "rejected"]
    prior: bool = False                         # the prior convention the nominator ran first


class Warrant(Value):
    source_observation_ids: tuple[str, ...]
    source_episode_ids: tuple[str, ...]
    templates: int
    figures_reproduced: tuple[str, ...] = ()
    falsifier: str
    lens: dict[str, float] = Field(default_factory=dict)
    lens_score: float | None = None
    backtest_id: str | None = None


class Amendment(Value):
    at_idx: int
    clause: str
    from_: object = Field(alias="from", default=None)
    to: object = None
    reached_by: str              # a fire id, or "owner"
    backtest_id: str | None = None


class Lifecycle(Value):
    status: LifecycleStatus
    at_idx: int
    seeded: bool = False
    superseded_by: str | None = None
    converged_into: str | None = None
    reason: str | None = None

    def _require_admitted(self) -> None:
        if self.status is not LifecycleStatus.ADMITTED:
            raise LifecycleError(f"transition from {self.status} is not allowed")

    def supersede(self, by: str, at_idx: int) -> Lifecycle:
        self._require_admitted()
        return self.model_copy(update={"status": LifecycleStatus.SUPERSEDED, "superseded_by": by, "at_idx": at_idx})

    def converge(self, into: str, at_idx: int) -> Lifecycle:
        self._require_admitted()
        return self.model_copy(
            update={"status": LifecycleStatus.CONVERGED, "converged_into": into, "at_idx": at_idx}
        )

    def moot(self, at_idx: int, reason: str) -> Lifecycle:
        self._require_admitted()
        return self.model_copy(update={"status": LifecycleStatus.MOOT, "reason": reason, "at_idx": at_idx})

    def retire(self, at_idx: int, reason: str) -> Lifecycle:
        self._require_admitted()
        return self.model_copy(update={"status": LifecycleStatus.RETIRED, "reason": reason, "at_idx": at_idx})


class Representation(Value):
    embedder_id: str
    text_hash: str


class EntryContract(Value):
    """The pentad: activation, payload, warrant, enforcement, lifecycle — each with its negative."""

    title: str = Field(max_length=120)          # ≤ 12 words; checked by the language lint
    kind: DecisionKind
    payload: str                                 # ≤ 60 words, present tense
    options: tuple[Option, ...]
    forecloses: str
    latches: tuple[Latch, ...]
    residue: str
    warrant: Warrant

    # --- latch accessors -------------------------------------------------------------------------

    @property
    def hook(self) -> HookLatch:
        return next(lt for lt in self.latches if isinstance(lt, HookLatch))

    @property
    def revisits(self) -> tuple[RevisitLatch, ...]:
        return tuple(lt for lt in self.latches if isinstance(lt, RevisitLatch))

    @property
    def floor(self) -> FloorLatch | None:
        return next((lt for lt in self.latches if isinstance(lt, FloorLatch)), None)

    @property
    def retire_latch(self) -> RetireLatch | None:
        return next((lt for lt in self.latches if isinstance(lt, RetireLatch)), None)

    @property
    def wiring(self) -> WiringLatch:
        return next((lt for lt in self.latches if isinstance(lt, WiringLatch)), WiringLatch())

    # --- the pure half of L0 (SPEC § 10.2 "L0 additions") ------------------------------------------

    def l0_violations(self, source_figures: Iterable[float], leak_min_abs: float = 0.0) -> list[str]:
        """Structural refusals that need no store. Anchor resolution and vocabulary checks need the
        store and run in the L0 layer (`learn/layers.py`)."""
        out: list[str] = []
        hooks = [lt for lt in self.latches if isinstance(lt, HookLatch)]
        if len(hooks) != 1:
            out.append("exactly one hook latch is required")
        if not any(o.verdict == "rejected" for o in self.options):
            out.append("options must hold at least one rejected row")
        for h in hooks:
            for row in h.not_this:
                if row.is_empty() or not row.contrast.strip():
                    out.append("every not_this row needs at least one key and a non-empty contrast")
        if not self.revisits:
            out.append("at least one revisit latch is required")
        if self.kind is DecisionKind.FLOOR and self.floor is None:
            out.append("kind floor requires a floor latch")
        if self.kind is not DecisionKind.FLOOR and self.floor is not None:
            out.append("a floor latch is allowed on kind floor only")
        floor = self.floor
        if floor is not None:   # the view's definition passes the runtime sandbox (collection checked at admit)
            try:
                check([{"$match": floor.match}], targets=())
            except PipelineRefused as e:
                out.append(f"floor match refused by the sandbox: {e}")
        leaked = leaked_figures(self.payload, source_figures, leak_min_abs)
        if leaked:
            out.append(f"payload contains a source figure: {leaked}")
        return out


class Decision(EntryContract, Record):
    """An admitted record in the decision store."""

    lifecycle: Lifecycle
    evidence_state: EvidenceState = EvidenceState.CLEAR
    amendments: tuple[Amendment, ...] = ()
    rep: Representation | None = None
    emb: dict[str, list[float]] = Field(default_factory=dict)   # emb.<embedder_id> (SPEC § 21, E10)
    admitted_at_idx: int | None = None   # the admission index; `lifecycle.at_idx` moves on every flip

    @property
    def is_admitted(self) -> bool:
        return self.lifecycle.status is LifecycleStatus.ADMITTED


def evidence_state(open_fire_roles: Iterable[tuple[FireRole, FireDisposition]]) -> EvidenceState:
    """Computed from open fires; never written by hand (SPEC § 10.2)."""
    contested = any(
        role is FireRole.DISPOSITIVE and disp is FireDisposition.OPEN for role, disp in open_fire_roles
    )
    return EvidenceState.CONTESTED if contested else EvidenceState.CLEAR


def leaked_figures(text: str, source_figures: Iterable[float], min_abs: float = 0.0) -> list[str]:
    """Numbers in `text` equal to a source answer or figure: the mechanical floor under `case_leak`.
    Digits inside ISO dates and times never count (`1970-01-01` is not a 1); figures with |x| < `min_abs`
    are ignored (the caller passes LEAK_MIN_ABS)."""
    figures = {_norm(f) for f in source_figures if abs(float(f)) >= min_abs}
    return sorted(_numbers_in(_DATE.sub(" ", text)) & figures)


_DATE = re.compile(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?")
_NUM = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")


def _norm(x: float) -> str:
    return f"{float(x):.6g}"


def _numbers_in(text: str) -> set[str]:
    return {_norm(float(m.group().replace(",", ""))) for m in _NUM.finditer(text)}
