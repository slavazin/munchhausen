"""Store port (SPEC § 21): repositories per store, plus capabilities.

No module outside `store/` imports `pymongo`. Transactions never leak out of this port: an atomic change
is expressed as a domain plan (e.g. `domain.admission.Admission`) and committed by one repository call.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any, Protocol, runtime_checkable

from munchhausen.domain.admission import Admission
from munchhausen.domain.backtest import Backtest
from munchhausen.domain.common import Disposer, FireDisposition, Pipeline
from munchhausen.domain.decision import Amendment, Decision
from munchhausen.domain.draft import DirectionRead, Draft, LayerOutcome
from munchhausen.domain.episode import Episode
from munchhausen.domain.fire import Fire
from munchhausen.domain.lens import LensEntry, LensWeights
from munchhausen.domain.observation import Observation, ObservationDisposition
from munchhausen.domain.question import QuestionKeys
from munchhausen.domain.registers import Cursor, RoundRecord, RunRecord, SpendRow, Term

# --- the `world` database ---------------------------------------------------------------------------


@runtime_checkable
class DocumentReader(Protocol):
    """Read-only access to one database. `execute` and the nominator's world tool get only this."""

    async def find(self, collection: str, filter: dict[str, Any] | None = None,
                   projection: dict[str, Any] | None = None, limit: int = 0) -> list[dict[str, Any]]: ...

    async def aggregate(self, collection: str, pipeline: Pipeline, *, max_time_ms: int) -> list[dict[str, Any]]: ...

    async def collection_names(self) -> list[str]: ...


@runtime_checkable
class WorldWriter(DocumentReader, Protocol):
    """Write access to `world`: used by the adapter at build time and by floor views (SPEC § 8)."""

    async def replace_collection(self, collection: str, docs: Sequence[dict[str, Any]]) -> int: ...

    async def create_view(self, name: str, source: str, pipeline: Pipeline) -> None: ...

    async def drop_view(self, name: str) -> None: ...


# --- ledgers ----------------------------------------------------------------------------------------


@runtime_checkable
class EpisodeRepository(Protocol):
    async def put(self, episode: Episode) -> None: ...

    async def get(self, episode_id: str) -> Episode | None: ...

    async def exists(self, run_id: str, arm: str, idx: int) -> bool: ...

    async def for_learner(self, run_id: str, arm: str, *, with_authority: bool,
                          filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Learner-facing read. Without an authority, evaluation-only fields are projected away."""
        ...

    async def backtest_population(self, run_id: str, arm: str, keys_filter: dict[str, Any], *,
                                  exclude_ids: Sequence[str], after_idx: int | None, n: int) -> list[Episode]:
        """Balanced `$facet` + `$sample` over correct episodes and first-attempt misses (§ 7.4, § 20.2)."""
        ...

    async def consultations_of(self, run_id: str, arm: str, decision_id: str, last_n: int) -> list[Episode]: ...

    async def direction_read(self, run_id: str, arm: str, inside: dict[str, Any], *, before_idx: int) -> DirectionRead:
        """Stream misses inside vs outside a presentation filter, hits included (E4). Reads `correct`, so
        only arms with an authority call it; there the authority's reply makes a miss learner-legal."""
        ...


@runtime_checkable
class ObservationRepository(Protocol):
    async def put(self, observation: Observation) -> None: ...

    async def open_for_pass(self, run_id: str, arm: str, *, since_round: int) -> list[Observation]: ...

    async def dispose(self, ids: Sequence[str], disposition: ObservationDisposition, by: str) -> None: ...


@runtime_checkable
class DecisionRepository(Protocol):
    """The decision store. Its write surface is exactly the six lifecycle functions (SPEC § 10.2)."""

    async def get(self, decision_id: str) -> Decision | None: ...

    async def admitted(self, run_id: str, arm: str) -> list[Decision]: ...

    async def match_hooks(self, run_id: str, arm: str, keys: QuestionKeys) -> list[Decision]: ...

    async def lineage(self, decision_id: str) -> list[Decision]: ...

    # the write path — nothing else in the codebase updates `decisions`
    async def admit(self, plan: Admission) -> None: ...

    async def amend(self, decision_id: str, amendment: Amendment) -> None: ...

    async def supersede(self, plan: Admission) -> None: ...

    async def converge(self, plan: Admission) -> None: ...

    async def moot(self, decision_id: str, at_idx: int, reason: str) -> None: ...

    async def retire(self, decision_id: str, at_idx: int, reason: str) -> None: ...

    async def refresh_evidence_state(self, decision_id: str) -> None:
        """Recompute `evidence_state` from open fires. Computed, never written by hand."""
        ...


@runtime_checkable
class FireRepository(Protocol):
    async def put(self, fire: Fire) -> None: ...

    async def open_for(self, decision_id: str) -> list[Fire]: ...

    async def dispose(self, fire_ids: Sequence[str], disposition: FireDisposition, disposer: Disposer) -> None: ...


@runtime_checkable
class DraftRepository(Protocol):
    async def put(self, draft: Draft) -> None: ...

    async def get(self, draft_id: str) -> Draft | None: ...

    async def record(self, draft_id: str, outcome: LayerOutcome) -> None: ...

    async def held(self, run_id: str, arm: str) -> list[Draft]: ...


@runtime_checkable
class BacktestRepository(Protocol):
    async def put(self, backtest: Backtest) -> None: ...

    async def get(self, backtest_id: str) -> Backtest | None: ...


# --- registers --------------------------------------------------------------------------------------


@runtime_checkable
class CursorRepository(Protocol):
    async def get(self, run_id: str, arm: str) -> Cursor: ...

    async def claim_next(self, run_id: str, arm: str, *, limit: int) -> int | None:
        """Atomically claim the next stream index (`find_one_and_update` + `$inc`), or None at `limit`."""
        ...

    async def set_round(self, run_id: str, arm: str, round_: int) -> None: ...

    async def save_resume_token(self, run_id: str, consumer: str, token: dict[str, Any]) -> None: ...


@runtime_checkable
class LeaseRepository(Protocol):
    async def acquire(self, run_id: str, arm: str, idx: int, worker: str) -> bool: ...

    async def release(self, run_id: str, arm: str, idx: int) -> None: ...

    async def orphaned(self, run_id: str, arm: str, below_idx: int) -> list[int]:
        """Claimed indices with neither a live lease nor an episode: re-issued on resume (§ 10.4)."""
        ...


@runtime_checkable
class ToolAccessRepository(Protocol):
    async def view_map(self, run_id: str, arm: str) -> dict[str, str]: ...


@runtime_checkable
class TermRepository(Protocol):
    async def all(self) -> list[Term]: ...

    async def add(self, term: Term) -> None: ...

    async def extract(self, text: str) -> frozenset[str]:
        """Question text → presented terms (`$search` over `terms` with synonyms, § 20.3)."""
        ...


@runtime_checkable
class RunRepository(Protocol):
    async def start(self, run: RunRecord) -> RunRecord:
        """Insert the run, or return the existing record for this run id (resume)."""
        ...

    async def put_round(self, round_: RoundRecord) -> None: ...


@runtime_checkable
class SpendRepository(Protocol):
    async def record(self, row: SpendRow) -> None: ...


@runtime_checkable
class LensRepository(Protocol):
    async def entries(self) -> list[LensEntry]: ...

    async def current_weights(self) -> LensWeights: ...

    async def put_weights(self, weights: LensWeights) -> None: ...


# --- the aggregate port -----------------------------------------------------------------------------


@runtime_checkable
class Store(Protocol):
    episodes: EpisodeRepository
    observations: ObservationRepository
    decisions: DecisionRepository
    fires: FireRepository
    drafts: DraftRepository
    backtests: BacktestRepository
    cursors: CursorRepository
    leases: LeaseRepository
    tool_access: ToolAccessRepository
    terms: TermRepository
    runs: RunRepository
    spend: SpendRepository
    lenses: LensRepository

    def world(self) -> DocumentReader:
        """The `world` database as the read-only executor user."""
        ...

    def source(self) -> DocumentReader:
        """The source database a dataset adapter materializes `world` from (e.g. `sample_analytics`)."""
        ...

    def world_writer(self) -> WorldWriter:
        """The `world` database with write access: adapter build and floor views only. The `truth`
        database is deliberately absent from this port; only the Truth implementation is handed it."""
        ...

    async def capabilities(self) -> dict[str, Any]:
        """vector_search, search_indexes_left, auto_embed, rank_fusion, score_fusion, change_streams,
        transactions, agent_engine, server_version (SPEC § 21)."""
        ...

    def watch(self, collection: str, *, resume_token: dict[str, Any] | None = None) -> AsyncIterator[dict[str, Any]]:
        """Change stream over one store (the event bus, § 20.2)."""
        ...

    async def vector_search(self, collection: str, embedder_id: str, vector: Sequence[float], k: int,
                            filter: dict[str, Any], *, exact: bool = False) -> list[tuple[str, float]]: ...

    async def close(self) -> None: ...
