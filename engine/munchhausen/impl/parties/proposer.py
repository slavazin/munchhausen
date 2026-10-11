"""Proposer party (SPEC § 6.1; consultation language, LANGUAGE.md § 6). Owner: forward-pass surface (M2)."""

from __future__ import annotations

from munchhausen.config import Settings
from munchhausen.domain.episode import Proposal
from munchhausen.impl.parties import LLM
from munchhausen.ports.models import ProposerInput


async def run(llm: LLM, settings: Settings, inp: ProposerInput) -> Proposal:
    raise NotImplementedError("M2: proposer prompt (consultation language, § 22.6) → ProposalWire → Proposal")
