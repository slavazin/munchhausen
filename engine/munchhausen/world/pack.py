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
    persona: str | None = None          # preference quirks: the persona whose questions carry it (P1: dana)
    definition: str = ""                # hidden; spoken only at AUTHORITY_LEVEL=rule (a control setting)
    weight: float = 1.0                 # relative draw weight among quirk-bearing stream questions


class TemplateSpec(BaseModel):
    """A question template as data: text over params, the measure that computes its gold, its collections."""

    model_config = ConfigDict(frozen=True)
    id: str
    text: str
    collections: tuple[str, ...]
    measure: str
    args: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, tuple[Any, ...]] = Field(default_factory=dict)


class Pack(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    adapter: str
    drift_schedule: dict[str, dict[str, Any]] = Field(default_factory=dict)
    quirks: tuple[Quirk, ...] = ()
    poison_bank: tuple[TransformRef, ...] = ()
    personas: tuple[str, ...] = ()
    templates: tuple[TemplateSpec, ...] = ()

    def quirk(self, quirk_id: str) -> Quirk:
        return next(q for q in self.quirks if q.id == quirk_id)

    def persona_quirks(self) -> dict[str, str]:
        return {q.persona: q.id for q in self.quirks if q.persona}

    def content_hash(self) -> str:
        """sha256 over the pack's canonical JSON: the run record names the exact pack it ran under."""
        import hashlib
        import json

        blob = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()

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
        known = {t.id for t in self.templates}
        owner: dict[str, str] = {}
        for q in self.quirks:
            for t in q.templates:
                if t not in known:
                    out.append(f"{q.id}: unknown template {t}")
                if q.persona is None:
                    if t in owner:
                        out.append(f"{t}: touches {owner[t]} and {q.id} (one quirk per template)")
                    owner[t] = q.id
        for q in self.quirks:
            if q.persona is not None:
                out += [f"{q.id}: persona template {t} is not a control" for t in q.templates if t in owner]
        return out


def load_pack(path: Path) -> Pack:
    with path.open() as f:
        return Pack.model_validate(yaml.safe_load(f))
