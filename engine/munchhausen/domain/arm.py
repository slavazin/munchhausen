"""Arm specifications (SPEC § 5). Loaded from `conf/arms.yaml`; the engine branches on these fields,
never on an arm's name."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from munchhausen.domain.common import Value


class WritePath(StrEnum):
    NONE = "none"
    SELF_GRADE = "self_grade"   # self_ref: the proposer grades itself and writes lessons
    DIRECT = "direct"           # naive: each observation's lesson admitted directly
    EPISODIC = "episodic"       # governed: episodic pass → adjudicator → backtest


class ConsultationMode(StrEnum):
    NONE = "none"
    SEMANTIC = "semantic"       # top-k retrieval (the off-the-shelf memory shape)
    HOOKS = "hooks"             # hook-keyed consultation


class ArmSpec(Value):
    name: str
    authority: bool
    write_path: WritePath
    consultation: ConsultationMode
    curator: str | None = None
    stream: bool = True                      # false: V set only (frozen follows FROZEN_STREAM)
    claim: str = ""
    ports: dict[str, str] = Field(default_factory=dict)   # port → implementation name overrides
