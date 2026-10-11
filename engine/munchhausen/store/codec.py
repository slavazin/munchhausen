"""Domain model ⇄ BSON document. Python-mode dumps keep datetimes as BSON dates (TTL, time series)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def to_doc(model: BaseModel) -> dict[str, Any]:
    return _bsonable(model.model_dump(by_alias=True, mode="python"))


def from_doc[M: BaseModel](cls: type[M], doc: dict[str, Any] | None) -> M | None:
    return None if doc is None else cls.model_validate(doc)


def _bsonable(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: _bsonable(v) for k, v in x.items()}
    if isinstance(x, (set, frozenset)):
        return sorted(_bsonable(v) for v in x)
    if isinstance(x, (list, tuple)):
        return [_bsonable(v) for v in x]
    return x
