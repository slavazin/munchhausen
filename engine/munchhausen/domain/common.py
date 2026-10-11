"""Shared domain vocabulary: base models and the closed enums of the lexicon (corpus/LANGUAGE.md).

The domain layer is pure: no I/O, no SDKs, no config. Everything outside it depends inward.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1

# An answer or figure is a number or a set of names (SPEC § 4.4). None means no answer was read.
Answer: TypeAlias = float | int | list[str] | None
Pipeline: TypeAlias = list[dict[str, Any]]


def emb_key(embedder_id: str) -> str:
    """Field-safe key for `emb.<embedder_id>` (Atlas paths treat '.' as nesting)."""
    return embedder_id.replace(".", "_").replace("-", "_")


class Value(BaseModel):
    """Immutable value object. Unknown fields are ignored so additive schema changes stay readable."""

    model_config = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)


class Record(Value):
    """A persisted record: one document in one store. Every record carries run, arm and schema version."""

    id: str = Field(alias="_id")
    schema_version: int = SCHEMA_VERSION
    run_id: str
    arm: str


# --- closed enums (one meaning each; SPEC § 2) ------------------------------------------------------


class DecisionKind(StrEnum):
    TAXONOMIC = "taxonomic"
    PROCEDURAL = "procedural"
    FLOOR = "floor"
    PREFERENCE = "preference"
    CONTEXT_POLICY = "context_policy"


class Signature(StrEnum):
    SET_MEMBER = "set_member"
    RATIO = "ratio"
    DATE_OFFSET = "date_offset"
    EXCLUSION = "exclusion"
    THRESHOLD = "threshold"
    ROUNDING = "rounding"


class Disposition(StrEnum):
    """The proposer's disposition toward one consulted decision (SPEC § 2, consultation)."""

    APPLIED = "applied"
    CONSIDERED_NOT_APPLICABLE = "considered-not-applicable"


class LifecycleStatus(StrEnum):
    ADMITTED = "admitted"
    SUPERSEDED = "superseded"
    CONVERGED = "converged"
    MOOT = "moot"
    RETIRED = "retired"


class EvidenceState(StrEnum):
    CLEAR = "clear"
    CONTESTED = "contested"


class FireRole(StrEnum):
    DISPOSITIVE = "dispositive"
    CORROBORATING = "corroborating"


class FireDisposition(StrEnum):
    OPEN = "open"
    APPLIED = "applied"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class Disposer(StrEnum):
    ADJUDICATOR = "adjudicator"   # the stand-in adjudicator (L0–L4)
    LIFECYCLE = "lifecycle"       # a lifecycle function (supersede, retire, …)
    OWNER = "owner"               # the owner port (L5)


class LayerRole(StrEnum):
    ROUTING = "routing"
    CORROBORATING = "corroborating"
    DISPOSITIVE = "dispositive"


class AuthorityLevel(StrEnum):
    TERSE = "terse"
    TERM = "term"
    RULE = "rule"   # control setting only; never the reported configuration
