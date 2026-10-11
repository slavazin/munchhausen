"""Mechanical language checks (SPEC § 22.8), run at L0 on every draft and every observation write.

`TELLS` is the authority for L1 run-invariance: no payload, hook, observation or lens names a run, an
arm, an episode index, a party or a moment. Residue, disclosed: the lint does not check that a payload is
true, that a hook is a good net, that a `noticed` names a real surface, or that a counterfactual names a
real overshoot.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from munchhausen.domain.decision import EntryContract
from munchhausen.domain.latches import HookLatch

_I = re.IGNORECASE

# (pattern, flags, legal replacement) — corpus/LANGUAGE.md § banned tells; where the two differ, this holds.
# Party pronouns are case-sensitive: "I" only as a capital word, and "US" (a country, a unit) is not "us".
_TELL_TABLE: tuple[tuple[str, int, str], ...] = (
    (r"\bthe agent\b", _I, "name the field or the population"),
    (r"\bI\b|\b[Ww]e\b|\b[Oo]ur\b|\b[Uu]s\b", 0, "impersonal present tense"),
    (r"\b(now|currently|recently|this round|so far|again)\b", _I, "a dated fact (at_idx) or a premise"),
    (r"\b(arm|episode|run|round)\s*#?\d+\b", _I, "anchor through warrant ids, not prose"),
    (r"\b(governed|ungated|naive|self_ref|frozen)\b", _I, "never name an arm in a record"),
)
TELLS: dict[str, str] = {pat: fix for pat, _, fix in _TELL_TABLE}
_COMPILED = tuple((re.compile(pat, flags), pat, fix) for pat, flags, fix in _TELL_TABLE)

# An observation notices; it never prescribes (SPEC § 23.1 "Noticing only").
FIX_TELLS = re.compile(r"\b(should|must|ought to|needs? to|has to|have to|instead of|the fix)\b", _I)
# A `not_this.contrast` names one instantiated case, never a bare negation (§ 22.5).
BARE_NEGATION = re.compile(r"^\s*(anything|everything|all|any)\s+(else|other)\b", _I)
MIN_CONTRAST_WORDS = 4
# The vocabulary escape (§ 22.4): `other(<term>): <presentation gloss>`.
ESCAPE = re.compile(r"^\s*other\(\s*(?P<term>[^()]+?)\s*\)\s*:\s*(?P<gloss>\S.*)$")

VACUOUS_COUNTERFACTUAL = re.compile(r"or (was|is) it (fine|ok|correct)\??$", re.IGNORECASE)
MAX_TITLE_WORDS, MAX_PAYLOAD_WORDS = 12, 60
MAX_NOTICED_SENTENCES = 3


def tells(text: str) -> list[str]:
    return [f"tell {pat!r}: use {fix}" for rx, pat, fix in _COMPILED if rx.search(text)]


def parse_escape(item: str) -> tuple[str, str] | None:
    """`other(fiscal quarter): how a question names a reporting period` → (term, gloss); else None."""
    m = ESCAPE.match(item)
    return (m.group("term").strip().lower(), m.group("gloss").strip()) if m else None


def escaped_terms(items: Iterable[str]) -> set[str]:
    return {p[0] for p in map(parse_escape, items) if p}


def lint_entry(entry: EntryContract) -> list[str]:
    out = []
    if len(entry.title.split()) > MAX_TITLE_WORDS:
        out.append(f"title exceeds {MAX_TITLE_WORDS} words")
    if len(entry.payload.split()) > MAX_PAYLOAD_WORDS:
        out.append(f"payload exceeds {MAX_PAYLOAD_WORDS} words")
    for field, text in (("title", entry.title), ("payload", entry.payload), ("residue", entry.residue)):
        out += [f"{field}: {t}" for t in tells(text)]
    return out


def lint_draft_language(entry: EntryContract, vocabulary: Iterable[str], new_terms: Iterable[str]) -> list[str]:
    """The nominator-side checks beyond `lint_entry`: hook terms in the vocabulary or the escape, each
    `contrast` instantiated, and no tells in the prose slots a nominated entry fills."""
    out = lint_entry(entry)
    for field, text in (("forecloses", entry.forecloses), ("falsifier", entry.warrant.falsifier)):
        out += [f"{field}: {t}" for t in tells(text)]
    malformed = [t for t in new_terms if parse_escape(t) is None]
    if malformed:
        out.append(f"new terms must read other(<term>): <gloss>: {malformed}")
    known = {v.lower() for v in vocabulary} | escaped_terms(new_terms)
    hooks = [lt for lt in entry.latches if isinstance(lt, HookLatch)]
    for h in hooks:
        unknown = sorted({t.lower() for t in h.fires_when.terms} - known)
        if unknown:
            out.append(f"hook terms outside the vocabulary and the escape: {unknown}")
        for row in h.not_this:
            if BARE_NEGATION.search(row.contrast) or len(row.contrast.split()) < MIN_CONTRAST_WORDS:
                out.append(f"not_this contrast must instantiate one case: {row.contrast!r}")
            out += [f"contrast: {t}" for t in tells(row.contrast)]
    return out


def lint_noticed(noticed: str) -> list[str]:
    out = tells(noticed)
    if FIX_TELLS.search(noticed):
        out.append("noticed states the surface and the gap, never a fix")
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", noticed.strip()) if s]
    if not 1 <= len(sentences) <= MAX_NOTICED_SENTENCES:
        out.append(f"noticed must be 1–{MAX_NOTICED_SENTENCES} sentences")
    return out


def lint_counterfactual(text: str) -> list[str]:
    return ["vacuous counterfactual"] if VACUOUS_COUNTERFACTUAL.search(text.strip()) else []
