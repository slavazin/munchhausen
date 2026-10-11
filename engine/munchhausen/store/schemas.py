"""`$jsonSchema` validators, derived from the domain models (one source of truth).

Applied with `collMod` at setup, `validationAction: "warn"` (SPEC § 10.1). Schemas are additive only
after M0: never rename or drop a field; add the replacement and leave the original.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from munchhausen.domain.backtest import Backtest
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Draft
from munchhausen.domain.episode import Episode
from munchhausen.domain.fire import Fire
from munchhausen.domain.observation import Observation
from munchhausen.domain.registers import (
    Cursor,
    EmbeddingCacheRow,
    Lease,
    RerankCacheRow,
    RoundRecord,
    RunRecord,
    Term,
    ToolAccess,
)
from munchhausen.store.names import C

MODELS: dict[C, type[BaseModel]] = {
    C.EPISODES: Episode,
    C.OBSERVATIONS: Observation,
    C.DECISIONS: Decision,
    C.FIRES: Fire,
    C.DRAFTS: Draft,
    C.BACKTESTS: Backtest,
    C.TOOL_ACCESS: ToolAccess,
    C.CURSORS: Cursor,
    C.ROUNDS: RoundRecord,
    C.RUNS: RunRecord,
    C.TERMS: Term,
    C.LEASES: Lease,
    C.EMBEDDING_CACHE: EmbeddingCacheRow,
    C.RERANK_CACHE: RerankCacheRow,
}

_BSON = {
    "string": "string",
    "integer": ["int", "long"],
    "number": ["double", "int", "long", "decimal"],
    "boolean": "bool",
    "object": "object",
    "array": "array",
    "null": "null",
}
_KEEP = {"properties", "required", "items", "enum", "anyOf", "oneOf", "allOf", "additionalProperties",
         "minimum", "maximum", "minItems", "maxItems", "minLength", "maxLength", "pattern", "uniqueItems"}


def validator(model: type[BaseModel]) -> dict[str, Any]:
    js = model.model_json_schema(by_alias=True, mode="serialization")
    return {"$jsonSchema": _convert(js, js.get("$defs", {}))}


def _convert(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, list):
        return [_convert(n, defs) for n in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        return _convert(defs[node["$ref"].split("/")[-1]], defs)
    out: dict[str, Any] = {}
    t = node.get("type")
    if t is not None:
        out["bsonType"] = "date" if node.get("format") == "date-time" else _BSON[t]
    if "const" in node:
        out["enum"] = [node["const"]]
    if "prefixItems" in node:       # fixed-length tuples: element types are not checked
        out["bsonType"] = "array"
    for k, v in node.items():
        if k not in _KEEP:
            continue
        if k == "properties":
            out[k] = {pk: _convert(pv, defs) for pk, pv in v.items()}
        elif k == "additionalProperties" and isinstance(v, bool):
            out[k] = v
        else:
            out[k] = _convert(v, defs)
    return out
