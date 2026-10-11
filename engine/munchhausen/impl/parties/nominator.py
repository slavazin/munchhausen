"""Nominator party (SPEC § 7.2 step 4, § 10.2). Owner: backward-pass shaping surface (M3)."""

from __future__ import annotations

from munchhausen.config import Settings
from munchhausen.domain.decision import EntryContract
from munchhausen.impl.parties import LLM
from munchhausen.ports.models import NominatorInput


async def run(llm: LLM, settings: Settings, inp: NominatorInput) -> tuple[EntryContract, tuple[str, ...]]:
    raise NotImplementedError("M3: nominator with the read-only world tool; runs the prior option first")
