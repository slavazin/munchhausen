"""Question templates and the seeded stream (SPEC § 4.3).

Templates are pack data (`packs/*.yaml: templates`) × parameters (year, symbol, product, …) × persona.
`QUIRK_SHARE` of the stream touches exactly one quirk, the rest are controls. Hidden tags (quirk ids) stay
in `QuestionBank`; only `Question` crosses the World port.

**One quirk per question.** A quirk-bearing template touches exactly one quirk; a preference persona (P1,
Dana) is drawn on control templates only. With binary scoring, a question touching two quirks rewards a
correct decision for one of them with nothing until the other is admitted too, so the backtest can't
credit it, the nominator can't reproduce its figures, and the authority's phrasing can name the quirk the
answer got right. The pack's materialization places overlapping populations where the other quirks'
definitions already exclude them; a gold test asserts each quirk template's gold is unchanged by every
other quirk's gold transform.

Determinism: the question at stream index i is a pure function of (seed, i), so ids are stable across
processes and resumes, and `hidden(question_id)` regenerates tags for a question this process never drew.
The sealed V set is drawn from its own seed; the stream redraws any (template, persona, params) that V holds.
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

    `persona_quirks` maps a preference persona to its quirk (Dana → P1); such a persona is drawn only on
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
        for k in range(_MAX_REDRAWS):
            q = self._draw(STREAM, seed, i, k)
            if self._key(q) not in self._sealed_keys:
                return q
        raise RuntimeError(f"stream index {i}: every draw collides with the sealed V set")

    def v_set(self, seed: int, size: int) -> tuple[Question, ...]:
        return tuple(self._draw(SEALED, seed, i, 0) for i in range(size))

    def instances(self, template_id: str, seed: int, n: int) -> tuple[Question, ...]:
        """n questions of one template (S6's injection beat), plain persona, ids `t-<template>-<seed>-<k>`."""
        return tuple(self._instance(template_id, seed, k) for k in range(n))

    def pose(self, template_id: str, persona: str, params: dict[str, Any]) -> Question:
        """One question with chosen params (gold checks, the injection beat). Its tags live in this process
        only: the id `p-<template>-<persona>-<params>` is not regenerated by `hidden`."""
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

    def _draw(self, kind: str, seed: int, i: int, k: int) -> Question:
        rng = random.Random(f"{kind}:{seed}:{i}:{k}")
        if self._groups and (not self._controls or rng.random() < self._share):
            quirk = rng.choices(list(self._groups), weights=self._weights)[0]
            tpl = self._by_id[rng.choice(self._groups[quirk])]
            persona = self._persona_of.get(quirk) or rng.choice(self._plain)
        else:
            tpl = self._by_id[rng.choice(self._controls)]
            persona = rng.choice(self._plain)
        params = {name: rng.choice(values) for name, values in sorted(tpl.params.items())}
        return self._make(f"{kind}{seed}-{i}", tpl, persona, params)

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
            seed, i = (int(x) for x in rest.split("-"))
        except ValueError:
            raise KeyError(question_id_error(qid)) from None
        if kind == STREAM:
            self.question_at(seed, i)
        elif kind == SEALED:
            self._draw(SEALED, seed, i, 0)
        else:
            raise KeyError(question_id_error(qid))

    def _key(self, q: Question) -> tuple[Any, ...]:
        return (q.template, q.persona, tuple(sorted(self.hidden(q.id).params.items())))


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
