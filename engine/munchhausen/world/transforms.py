"""Transform registry (SPEC § 4.1): materialize transforms write fields into `world`; gold transforms
build gold pipeline fragments. Keyed by name; packs reference them by name with parameters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Doc = dict[str, Any]
MaterializeFn = Callable[[dict[str, list[Doc]], dict[str, Any], int], dict[str, list[Doc]]]
GoldFn = Callable[[dict[str, Any], dict[str, Any]], list[Doc]]   # (question params, gold params) → stages

MATERIALIZE: dict[str, MaterializeFn] = {}
GOLD: dict[str, GoldFn] = {}


def materialize(name: str) -> Callable[[MaterializeFn], MaterializeFn]:
    def deco(fn: MaterializeFn) -> MaterializeFn:
        MATERIALIZE[name] = fn
        return fn
    return deco


def gold(name: str) -> Callable[[GoldFn], GoldFn]:
    def deco(fn: GoldFn) -> GoldFn:
        GOLD[name] = fn
        return fn
    return deco


def stable_bucket(key: str, seed: int, buckets: int = 10_000) -> int:
    """Deterministic hash assignment (e.g. Q1's 50/20/15/15% status split) under WORLD_SEED."""
    import hashlib

    return int(hashlib.sha256(f"{seed}:{key}".encode()).hexdigest(), 16) % buckets


# M1: register Q1–Q8 transforms here, each covered by a gold test on a hand-computed fixture
# (SPEC § 4.3 Do) before any arm runs.
