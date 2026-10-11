"""Quirk packs as data (SPEC § 4.1). A pack names registered transforms; it never carries code."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from munchhausen.domain.common import Signature


class TransformRef(BaseModel):
    model_config = ConfigDict(frozen=True)
    transform: str
    params: dict[str, Any] = Field(default_factory=dict)


class Drift(BaseModel):
    model_config = ConfigDict(frozen=True)
    at_idx: int | str                   # an index, or a knob name such as "D1_AT"
    gold_params: dict[str, Any]


class Quirk(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    kind: Literal["taxonomic", "procedural", "floor", "preference", "poison"]
    prior_trap: str = ""
    materialize: TransformRef | None = None
    gold: TransformRef | None = None
    signature: Signature | None = None
    templates: tuple[str, ...] = ()
    authority_phrasings: tuple[str, ...] = ()
    drift: tuple[Drift, ...] = ()


class Pack(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    adapter: str
    drift_schedule: dict[str, dict[str, Any]] = Field(default_factory=dict)
    quirks: tuple[Quirk, ...] = ()
    poison_bank: tuple[TransformRef, ...] = ()

    def validate_coverage(self) -> list[str]:
        """Pack-level checks (SPEC § 4.1 Do/Don't): ≥ 4 templates and ≥ 3 phrasings per learnable quirk."""
        out = []
        for q in self.quirks:
            if q.kind == "poison":
                continue
            if len(q.templates) < 4:
                out.append(f"{q.id}: needs ≥ 4 templates")
            if len(q.authority_phrasings) < 3:
                out.append(f"{q.id}: needs ≥ 3 authority phrasings")
            if q.signature is None:
                out.append(f"{q.id}: needs a signature (an unsigned quirk is unlearnable from a figure)")
        return out


def load_pack(path: Path) -> Pack:
    with path.open() as f:
        return Pack.model_validate(yaml.safe_load(f))
