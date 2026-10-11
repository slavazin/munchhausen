"""Deterministic identifiers.

Ids derive from (run, arm, index) wherever possible, so a resumed run re-issues the same id and every
write is an idempotent upsert (SPEC § 10.4).
"""

from __future__ import annotations

import hashlib


def episode_id(run_id: str, arm: str, idx: int, *, stream: str = "stream", question_id: str = "") -> str:
    """Stream episodes key on the index; V-set and injection episodes key on (stream, question, index)."""
    if stream == "stream":
        return f"{run_id}:{arm}:e{idx}"
    return f"{run_id}:{arm}:{stream}:{question_id}:{idx}"


def observation_id(episode_id_: str, k: int) -> str:
    return f"{episode_id_}:o{k}"


def residual_id(episode_id_: str, decision_id_: str) -> str:
    return f"{episode_id_}:r:{decision_id_}"


def draft_id(run_id: str, arm: str, round_: int, shape_key: str) -> str:
    return f"{run_id}:{arm}:r{round_}:{_short(shape_key)}"


def decision_id(draft_id_: str) -> str:
    """Minted at admission (SPEC § 2, admission); stable under replay of the same draft."""
    return f"D-{_short(draft_id_)}"


def latch_id(decision_id_: str, k: int) -> str:
    return f"T-{decision_id_}-{k}"


def backtest_id(draft_id_: str) -> str:
    return f"B-{_short(draft_id_)}"


def fire_id(decision_id_: str, latch: str, at_idx: int) -> str:
    return f"F-{decision_id_}-{latch}-{at_idx}"


def _short(s: str, n: int = 10) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:n]


def shape_id(observation_ids: tuple[str, ...]) -> str:
    return f"S-{_short('|'.join(sorted(observation_ids)))}"
