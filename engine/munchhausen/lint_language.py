"""Mechanical language checks (SPEC § 22.8), run at L0 on every draft and every observation write.

`TELLS` is the authority for L1 run-invariance: no payload, hook, observation or lens names a run, an
arm, an episode index, a party or a moment. Residue, disclosed: the lint does not check that a payload is
true, that a hook is a good net, or that a counterfactual names a real overshoot.
"""

from __future__ import annotations

import re

from munchhausen.domain.decision import EntryContract

# tell → legal replacement (corpus/LANGUAGE.md § banned tells)
TELLS: dict[str, str] = {
    r"\bthe agent\b": "name the field or the population",
    r"\b(I|we|our|us)\b": "impersonal present tense",
    r"\b(now|currently|recently|this round|so far|again)\b": "a dated fact (at_idx) or a premise",
    r"\b(arm|episode|run)\s*#?\d+\b": "anchor through warrant ids, not prose",
    r"\b(governed|naive|self_ref|frozen)\b": "never name an arm in a record",
}
VACUOUS_COUNTERFACTUAL = re.compile(r"or (was|is) it (fine|ok|correct)\??$", re.IGNORECASE)
MAX_TITLE_WORDS, MAX_PAYLOAD_WORDS = 12, 60


def tells(text: str) -> list[str]:
    return [f"tell {pat!r}: use {fix}" for pat, fix in TELLS.items() if re.search(pat, text, re.IGNORECASE)]


def lint_entry(entry: EntryContract) -> list[str]:
    out = []
    if len(entry.title.split()) > MAX_TITLE_WORDS:
        out.append(f"title exceeds {MAX_TITLE_WORDS} words")
    if len(entry.payload.split()) > MAX_PAYLOAD_WORDS:
        out.append(f"payload exceeds {MAX_PAYLOAD_WORDS} words")
    for field, text in (("title", entry.title), ("payload", entry.payload), ("residue", entry.residue)):
        out += [f"{field}: {t}" for t in tells(text)]
    return out


def lint_noticed(noticed: str) -> list[str]:
    out = tells(noticed)
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", noticed.strip()) if s]
    if not 1 <= len(sentences) <= 3:
        out.append("noticed must be 1–3 sentences")
    return out


def lint_counterfactual(text: str) -> list[str]:
    return ["vacuous counterfactual"] if VACUOUS_COUNTERFACTUAL.search(text.strip()) else []
