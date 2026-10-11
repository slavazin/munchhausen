"""Planted-truth judge party (SPEC § 11), evaluation only: never called on the learning path.

Given the pack's quirk definitions and one admitted decision, name the one quirk id the decision encodes, or
none. The judge sees the definitions (evaluation side) and the decision's entry contract; it never sees the
arm, run or any reading, so its map cannot lean on the outcome it is used to read.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from munchhausen.config import Settings
from munchhausen.impl.parties import LLM

STAGE = "planted_map"
NONE = "none"

SYSTEM = """You map one admitted decision from a data agent's decision store to the planted quirk it encodes.

You receive the quirk definitions of a synthetic analytics world (each with an id, a kind and its definition)
and one decision (title, kind, payload, hook keys). Answer with the single quirk id whose definition the
decision's payload states or applies, or "none" when it encodes no listed quirk, encodes a quirk only in
part so that applying it would not reproduce the quirk's figures, or contradicts every definition.

A decision matches a poison quirk (an N id) when its payload states the poisoned definition, not the true one.
A decision matches a preference quirk (a P id) whatever its hook's scope; scope is read elsewhere.
Name one id from the list exactly, or "none"."""


class PlantedWire(BaseModel):
    quirk: str = Field(description='one quirk id from the list, or "none"')
    rationale: str = Field(description="one sentence: which clause of the payload matches which definition")


def user_prompt(decision: Any, pack_definitions: str) -> str:
    hook = decision.hook.fires_when
    return (f"<quirks>\n{pack_definitions}\n</quirks>\n\n<decision>\n"
            f"title: {decision.title}\nkind: {decision.kind.value}\npayload: {decision.payload}\n"
            f"hook terms: {', '.join(hook.terms)}\nhook collections: {', '.join(hook.collections)}\n"
            f"hook persona: {hook.persona or '-'}\n</decision>")


async def run(llm: LLM, settings: Settings, decision: Any, pack_definitions: str, *,
              model: str | None = None) -> str | None:
    """`decision` is any entry contract with `arm`, `title`, `kind`, `payload`, `hook` (a decision or a draft).
    Spend is tagged arm `EVALUATION_SPEND_ARM`, never the decision's arm: the judge is not that arm's cost."""
    out = await llm.parse(stage=STAGE, arm=settings.evaluation_spend_arm, model=model or settings.planted_map_model,
                          system=SYSTEM, user=user_prompt(decision, pack_definitions), wire=PlantedWire,
                          max_tokens=settings.planted_map_max_tokens)
    q = out.quirk.strip()
    return None if not q or q.lower() == NONE else q
