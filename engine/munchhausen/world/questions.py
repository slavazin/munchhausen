"""Question templates and the seeded stream (SPEC § 4.3).

Templates are pack data (`packs/*.yaml: templates`) × parameters (year, symbol, product, …) × persona.
`QUIRK_SHARE` of the stream touches exactly one quirk, the rest are controls. Hidden tags (quirk ids) stay
in `QuestionBank`; only `Question` crosses the World port.

**One quirk per question.** A quirk-bearing template touches exactly one quirk; a preference persona (P1,
Claire) is drawn on control templates only. With binary scoring, a question touching two quirks rewards a
correct decision for one of them with nothing until the other is admitted too, so the backtest can't
credit it, the nominator can't reproduce its figures, and the authority's phrasing can name the quirk the
answer got right. The pack's materialization places overlapping populations where the other quirks'
definitions already exclude them; a gold test asserts each quirk template's gold is unchanged by every
other quirk's gold transform.

Determinism: the question at stream index i is a pure function of (seed, i), so ids are stable across
processes and resumes, and `hidden(question_id)` regenerates tags for a question this process never drew.
The sealed V set is drawn from its own seed, stratified by group; the stream redraws any (template, params,
preference persona) that V holds.
"""

from __future__ import annotations

import calendar
import random
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from munchhausen.domain.question import Question

STREAM, SEALED, INSTANCE, POSED = "s", "v", "t", "p"
_MAX_REDRAWS = 1000


@dataclass(frozen=True)
class Template:
    id: str
    text: str                                  # format string over params
    collections: tuple[str, ...]
    quirks: tuple[str, ...]                    # hidden tags
    params: dict[str, tuple[Any, ...]] = field(default_factory=dict)
    measure: str = ""                          # gold: `transforms.MEASURE[measure]`
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Hidden:
    quirks: tuple[str, ...]
    params: dict[str, Any]


def hidden_quirks(template: Template, persona: str, persona_quirks: dict[str, str]) -> tuple[str, ...]:
    """The quirk ids a (template, persona) question touches; refuses any pairing that touches two."""
    quirks = (*template.quirks, *((persona_quirks[persona],) if persona in persona_quirks else ()))
    if len(quirks) > 1:
        raise ValueError(f"{template.id} as {persona} touches {quirks}: one quirk per question")
    return quirks


def render(template: Template, params: dict[str, Any]) -> str:
    extra = {"month_name": calendar.month_name[params["month"]]} if "month" in params else {}
    return template.text.format(**params, **extra)


class QuestionBank:
    """Generates questions and remembers each one's hidden tags for gold and the authority.

    `persona_quirks` maps a preference persona to its quirk (Claire → P1); such a persona is drawn only on
    control templates, and only on the controls its quirk lists (`quirk_templates`)."""

    def __init__(self, templates: tuple[Template, ...], personas: tuple[str, ...], quirk_share: float,
                 persona_quirks: dict[str, str] | None = None, *,
                 quirk_templates: dict[str, tuple[str, ...]] | None = None,
                 sealed: tuple[int, int] | None = None, weights: dict[str, float] | None = None) -> None:
        self._templates, self._personas, self._share = templates, personas, quirk_share
        self._persona_quirks = dict(persona_quirks or {})
        bad = [t.id for t in templates if len(t.quirks) > 1]
        if bad:
            raise ValueError(f"templates touching more than one quirk: {bad}")
        self._by_id = {t.id: t for t in templates}
        self._controls = tuple(sorted(t.id for t in templates if not t.quirks))
        groups: dict[str, list[str]] = {}
        for t in templates:
            for q in t.quirks:
                groups.setdefault(q, []).append(t.id)
        for q, ts in (quirk_templates or {}).items():
            if q in self._persona_quirks.values():
                touched = [t for t in ts if self._by_id[t].quirks]
                if touched:
                    raise ValueError(f"{q}: preference persona drawn on quirk templates {touched}")
                groups[q] = list(ts)
        self._groups = {q: tuple(sorted(ts)) for q, ts in sorted(groups.items())}
        self._weights = [float((weights or {}).get(q, 1.0)) for q in self._groups]
        self._persona_of = {q: p for p, q in self._persona_quirks.items()}
        self._plain = tuple(p for p in personas if p not in self._persona_quirks) or personas
        self._hidden: dict[str, Hidden] = {}
        self._sealed_keys: frozenset[tuple[Any, ...]] = frozenset()
        if sealed is not None:
            self._sealed_keys = frozenset(self._key(q) for q in self.v_set(*sealed))

    # --- the stream and the sealed set ---------------------------------------------------------------

    def stream(self, seed: int) -> Iterator[Question]:
        i = 0
        while True:
            yield self.question_at(seed, i)
            i += 1

    def question_at(self, seed: int, i: int) -> Question:
        """The group (a quirk, or controls) is drawn once; a draw that V holds is redrawn within the group,
        so sealing V does not move the stream's quirk mix."""
        rng = random.Random(f"{STREAM}:{seed}:{i}")
        group = self._group(rng)
        for _ in range(_MAX_REDRAWS):
            tpl, persona, params = self._pick(rng, group)
            if self._key_of(tpl.id, persona, params) not in self._sealed_keys:
                return self._make(f"{STREAM}{seed}-{i}", tpl, persona, params)
        raise RuntimeError(f"stream index {i}: every draw in {group or 'controls'} collides with the sealed V set")

    def v_set(self, seed: int, size: int) -> tuple[Question, ...]:
        """`size` distinct questions, stratified by group at the stream's expected mix (largest remainder),
        so each quirk (Q1 across D1 included) has its expected count. Ids `v<seed>x<size>-<i>`."""
        out: list[Question] = []
        seen: set[tuple[Any, ...]] = set()
        for group, n in self._allocation(size):
            rng = random.Random(f"{SEALED}:{seed}:{group}")
            tries = 0
            while n and tries < n * _MAX_REDRAWS:
                tries += 1
                tpl, persona, params = self._pick(rng, group)
                key = self._key_of(tpl.id, persona, params)
                if key in seen:
                    continue
                seen.add(key)
                out.append(self._make(f"{SEALED}{seed}x{size}-{len(out)}", tpl, persona, params))
                n -= 1
            if n:
                raise RuntimeError(f"V set: {group or 'controls'} has too few distinct questions")
        return tuple(out)

    def instances(self, template_id: str, seed: int, n: int) -> tuple[Question, ...]:
        """n questions of one template (S6's injection beat), plain persona, ids `t-<template>-<seed>-<k>`."""
        return tuple(self._instance(template_id, seed, k) for k in range(n))

    def pose(self, template_id: str, persona: str, params: dict[str, Any]) -> Question:
        """One question with chosen params, for gold checks and tests only. Process-local: the id
        `p-<template>-<persona>-<params>` is not regenerated by `hidden` in another process, so never hand a
        posed question to the loop. The injection beat uses `instances()`."""
        tpl = self._by_id[template_id]
        tag = ",".join(f"{k}={params[k]}" for k in sorted(params))
        return self._make(f"{POSED}-{template_id}-{persona}-{tag}", tpl, persona, dict(params))

    # --- hidden tags (evaluation side) ---------------------------------------------------------------

    def hidden(self, question_id: str) -> Hidden:
        if question_id not in self._hidden:
            self._regenerate(question_id)
        return self._hidden[question_id]

    def template(self, template_id: str) -> Template:
        return self._by_id[template_id]

    @property
    def templates(self) -> tuple[Template, ...]:
        return self._templates

    @property
    def quirk_groups(self) -> dict[str, tuple[str, ...]]:
        return dict(self._groups)

    # --- internals -----------------------------------------------------------------------------------

    def _group(self, rng: random.Random) -> str:
        """A quirk id, or "" for controls."""
        if self._groups and (not self._controls or rng.random() < self._share):
            return rng.choices(list(self._groups), weights=self._weights)[0]
        return ""

    def _pick(self, rng: random.Random, group: str) -> tuple[Template, str, dict[str, Any]]:
        if group:
            tpl = self._by_id[rng.choice(self._groups[group])]
            persona = self._persona_of.get(group) or rng.choice(self._plain)
        else:
            tpl = self._by_id[rng.choice(self._controls)]
            persona = rng.choice(self._plain)
        params = {name: rng.choice(values) for name, values in sorted(tpl.params.items())}
        return tpl, persona, params

    def _allocation(self, size: int) -> list[tuple[str, int]]:
        """Expected count per group (controls 1 − share; quirks share × weight / Σ weight), largest remainder."""
        total_w = sum(self._weights) or 1.0
        expected = {"": (1 - self._share) * size if self._controls else 0.0}
        expected |= {q: self._share * size * w / total_w for q, w in zip(self._groups, self._weights, strict=True)}
        counts = {g: int(e) for g, e in expected.items()}
        rest = size - sum(counts.values())
        for g in sorted(expected, key=lambda g: (-(expected[g] - counts[g]), g))[:rest]:
            counts[g] += 1
        return sorted(counts.items())

    def _instance(self, template_id: str, seed: int, k: int) -> Question:
        tpl = self._by_id[template_id]
        rng = random.Random(f"{INSTANCE}:{template_id}:{seed}:{k}")
        persona = rng.choice(self._plain)
        params = {name: rng.choice(values) for name, values in sorted(tpl.params.items())}
        return self._make(f"{INSTANCE}-{template_id}-{seed}-{k}", tpl, persona, params)

    def _make(self, qid: str, tpl: Template, persona: str, params: dict[str, Any]) -> Question:
        quirks = hidden_quirks(tpl, persona, self._persona_quirks)
        self._hidden[qid] = Hidden(quirks=quirks, params=params)
        return Question(id=qid, text=render(tpl, params), template=tpl.id, persona=persona,
                        collections=tpl.collections)

    def _regenerate(self, qid: str) -> None:
        if qid.startswith(f"{INSTANCE}-"):
            _, rest = qid.split("-", 1)
            template_id, seed, k = rest.rsplit("-", 2)
            self._instance(template_id, int(seed), int(k))
            return
        kind, rest = qid[:1], qid[1:]
        try:
            head, i = rest.split("-")
            seed_s, _, size_s = head.partition("x")
            seed, size, idx = int(seed_s), int(size_s or 0), int(i)
        except ValueError:
            raise KeyError(question_id_error(qid)) from None
        if kind == STREAM:
            self.question_at(seed, idx)
        elif kind == SEALED:
            self.v_set(seed, size)
        else:
            raise KeyError(question_id_error(qid))

    def _key(self, q: Question) -> tuple[Any, ...]:
        return self._key_of(q.template, q.persona, self.hidden(q.id).params)

    def _key_of(self, template_id: str, persona: str, params: dict[str, Any]) -> tuple[Any, ...]:
        """A question's identity for sealing: template + params (the text) and a preference persona (which
        changes gold). A plain persona changes neither the text's meaning nor gold."""
        return (template_id, tuple(sorted(params.items())), persona if persona in self._persona_quirks else None)


def question_id_error(qid: str) -> str:
    return f"unknown question id {qid!r}"


def bank_from_pack(pack: Any, quirk_share: float, sealed: tuple[int, int] | None = None) -> QuestionBank:
    """Templates from the pack's data; each template's hidden quirk = the non-preference quirk listing it."""
    owners: dict[str, list[str]] = {}
    for q in pack.quirks:
        if q.persona is None and q.kind != "poison":
            for t in q.templates:
                owners.setdefault(t, []).append(q.id)
    templates = tuple(Template(id=t.id, text=t.text, collections=t.collections,
                               quirks=tuple(owners.get(t.id, ())), params=dict(t.params),
                               measure=t.measure, args=dict(t.args)) for t in pack.templates)
    persona_quirks = pack.persona_quirks()
    quirk_templates = {q.id: q.templates for q in pack.quirks if q.persona}
    return QuestionBank(templates, pack.personas, quirk_share, persona_quirks,
                        quirk_templates=quirk_templates, sealed=sealed,
                        weights={q.id: q.weight for q in pack.quirks})
