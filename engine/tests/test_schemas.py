from __future__ import annotations

from typing import Any

import pytest

from munchhausen.store.schemas import MODELS, validator

FORBIDDEN = {"$ref", "$defs", "type", "title", "default", "format", "discriminator", "prefixItems", "const"}


def _keywords(node: Any, in_properties: bool = False) -> set[str]:
    """Schema keywords used anywhere (property *names* are not keywords)."""
    if isinstance(node, list):
        return set().union(*(_keywords(n) for n in node)) if node else set()
    if not isinstance(node, dict):
        return set()
    if in_properties:
        return set().union(*(_keywords(v) for v in node.values())) if node else set()
    out = set(node)
    for k, v in node.items():
        out |= _keywords(v, in_properties=(k == "properties"))
    return out


@pytest.mark.parametrize("coll", list(MODELS))
def test_validator_is_mongo_jsonschema(coll) -> None:  # noqa: ANN001
    v = validator(MODELS[coll])["$jsonSchema"]
    assert v["bsonType"] == "object"
    assert not _keywords(v) & FORBIDDEN, _keywords(v) & FORBIDDEN


def test_records_require_run_and_arm() -> None:
    for coll in ("episodes", "observations", "decisions", "fires", "drafts", "backtests"):
        model = next(m for c, m in MODELS.items() if c.value == coll)
        req = set(validator(model)["$jsonSchema"]["required"])
        assert {"_id", "run_id", "arm"} <= req, coll
