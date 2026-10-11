"""The runtime sandbox for pipelines against `world` (ORCHESTRATION.md § Sandbox; SPEC § 6.1, § 20.2).

Pure. The store applies it at its boundary, in the world `DocumentReader`, so every caller — the
proposer's `execute`, the nominator's world tool, the authority's gold reads — passes the same guard.

- A stage allowlist: anything not on it is refused, with writing and server-introspection stages named.
- Operators that run server-side JavaScript (`$where`, `$function`, `$accumulator`) are refused at any
  depth, in pipelines and in `find` filters.
- `$lookup`, `$graphLookup` and `$unionWith` reach only names in the world's collection/view set; their
  sub-pipelines (and `$facet` branches) pass the same guard.
- A row cap: `capped()` appends `$limit cap + 1`, and `check_rows()` refuses a result past the cap.

Residue: the guard reads the pipeline's shape, not its cost; `maxTimeMS` bounds the cost. It does not check
that a pipeline is correct, only that it reads `world` and nothing else.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

# The sandbox's definition, not a tunable: widening it is a code change with a test, never a knob.
ALLOWED_STAGES: frozenset[str] = frozenset({
    "$match", "$project", "$addFields", "$set", "$unset", "$group", "$sort", "$limit", "$skip", "$unwind",
    "$count", "$lookup", "$graphLookup", "$unionWith", "$facet", "$bucket", "$bucketAuto", "$sortByCount",
    "$replaceRoot", "$replaceWith", "$sample", "$densify", "$fill", "$setWindowFields", "$redact",
})
REFUSED_STAGES: frozenset[str] = frozenset({
    "$out", "$merge", "$currentOp", "$listSessions", "$listLocalSessions", "$collStats", "$indexStats",
    "$planCacheStats", "$listSearchIndexes", "$documents",
})
REFUSED_OPERATORS: frozenset[str] = frozenset({"$where", "$function", "$accumulator"})
CROSS_STAGES: frozenset[str] = frozenset({"$lookup", "$graphLookup", "$unionWith"})


class PipelineRefused(ValueError):
    """A pipeline the sandbox refuses. Callers classify it as an irreducible execution failure."""


def check(pipeline: Any, *, targets: Iterable[str]) -> None:
    """Raise `PipelineRefused` unless every stage, nested pipeline and expression is inside the sandbox.
    `targets`: the world's collection and view names (the only legal `from`/`coll`)."""
    names = frozenset(targets)
    _pipeline(pipeline, names, path="pipeline")


def check_filter(filter_: Any) -> None:
    """A `find` filter: refuse server-side JavaScript at any depth."""
    _operators(filter_, "filter")


def lookup_targets(pipeline: Any) -> set[str]:
    """Every collection a pipeline names in `$lookup`/`$graphLookup`/`$unionWith`, at any depth."""
    out: set[str] = set()
    if not isinstance(pipeline, list):
        return out
    for stage in pipeline:
        if not isinstance(stage, dict) or len(stage) != 1:
            continue
        (op, spec), = stage.items()
        if op in CROSS_STAGES:
            target, sub = _cross(op, spec)
            if isinstance(target, str):
                out.add(target)
            out |= lookup_targets(sub)
        elif op == "$facet" and isinstance(spec, dict):
            for branch in spec.values():
                out |= lookup_targets(branch)
    return out


def capped(pipeline: list[dict[str, Any]], row_cap: int) -> list[dict[str, Any]]:
    """Append `$limit row_cap + 1`, so `check_rows` can tell a capped result from a complete one."""
    return [*pipeline, {"$limit": row_cap + 1}]


def check_rows(n_rows: int, row_cap: int) -> None:
    if n_rows > row_cap:
        raise PipelineRefused(f"result exceeds the row cap ({row_cap})")


# --- internals ------------------------------------------------------------------------------------


def _pipeline(pipeline: Any, targets: frozenset[str], path: str) -> None:
    if not isinstance(pipeline, list):
        raise PipelineRefused(f"{path}: a pipeline is a list of stages")
    for i, stage in enumerate(pipeline):
        where = f"{path}[{i}]"
        if not isinstance(stage, dict) or len(stage) != 1:
            raise PipelineRefused(f"{where}: a stage is an object with exactly one operator")
        (op, spec), = stage.items()
        if op in REFUSED_STAGES:
            raise PipelineRefused(f"{where}: stage {op} is refused (writes or server introspection)")
        if op not in ALLOWED_STAGES:
            raise PipelineRefused(f"{where}: stage {op} is not on the allowlist")
        if op in CROSS_STAGES:
            target, sub = _cross(op, spec)
            if not isinstance(target, str):
                raise PipelineRefused(f"{where}: {op} must name one world collection")
            if target not in targets:
                raise PipelineRefused(f"{where}: {op} into {target!r}, which is not a world collection or view")
            if sub is not None:
                _pipeline(sub, targets, f"{where}.{op}.pipeline")
            _operators({k: v for k, v in spec.items() if k != "pipeline"} if isinstance(spec, dict) else spec,
                       where)
        elif op == "$facet":
            if not isinstance(spec, dict):
                raise PipelineRefused(f"{where}: $facet takes an object of sub-pipelines")
            for name, branch in spec.items():
                _pipeline(branch, targets, f"{where}.$facet.{name}")
        else:
            _operators(spec, where)


def _cross(op: str, spec: Any) -> tuple[Any, Any]:
    """(target, sub-pipeline) of a cross-collection stage."""
    if op == "$unionWith":
        if isinstance(spec, str):
            return spec, None
        if isinstance(spec, dict):
            return spec.get("coll"), spec.get("pipeline")
        return None, None
    if isinstance(spec, dict):
        return spec.get("from"), spec.get("pipeline")
    return None, None


def _operators(node: Any, where: str) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if k in REFUSED_OPERATORS:
                raise PipelineRefused(f"{where}: operator {k} is refused (server-side JavaScript)")
            _operators(v, where)
    elif isinstance(node, list):
        for v in node:
            _operators(v, where)
