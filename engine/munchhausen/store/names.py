"""Collection and index names (SPEC § 10.1, § 10.3, § 20.1). Store-internal; application code names stores
through repository attributes, never through collection strings."""

from __future__ import annotations

from enum import StrEnum


class C(StrEnum):
    EPISODES = "episodes"
    OBSERVATIONS = "observations"
    DECISIONS = "decisions"
    FIRES = "fires"
    DRAFTS = "drafts"
    BACKTESTS = "backtests"
    LENS_WEIGHTS = "lens_weights"
    LENSES = "lenses"
    TOOL_ACCESS = "tool_access"
    CURSORS = "cursors"
    ROUNDS = "rounds"
    RUNS = "runs"
    TERMS = "terms"
    TERM_SYNONYMS = "term_synonyms"
    LEASES = "leases"
    SPEND = "spend"
    EMBEDDING_CACHE = "embedding_cache"   # additive: run-independent Voyage embedding cache
    RERANK_CACHE = "rerank_cache"         # additive: run-independent Voyage rerank cache


WORLD_TRUTH = "world_truth"   # lives in the `truth` database, readable by the evaluator role only


def view_name(logical: str, decision_id: str) -> str:
    """Floor views: `<collection>__<decision_id>` (SPEC § 8)."""
    return f"{logical}__{decision_id}"
