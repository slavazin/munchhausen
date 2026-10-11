"""World checks shared by the tests and `munchhausen build-world` (evaluation side).

- `isolation_violations`: for every template (controls included) and parameter combination, applying any
  other learnable quirk's gold transform leaves its gold unchanged, at every world version (SPEC § 4.2).
  Preference quirks are scoped by persona, not population (Dana is drawn on controls only), and poison is
  the authority's, so neither is applied.
- `quirk_effects`: per quirk template, the share of combinations whose gold differs from the poison
  variant's figure: a quirk whose figure equals the conventional one everywhere leaves no residual.
"""

from __future__ import annotations

import itertools
from typing import Any

from munchhausen.domain.question import Question
from munchhausen.truth.gold import PackGold
from munchhausen.world.pack import Pack
from munchhausen.world.questions import QuestionBank, Template
from munchhausen.world.transforms import Data


def combos(template: Template, limit: int) -> list[dict[str, Any]]:
    names = sorted(template.params)
    out = [dict(zip(names, values, strict=True))
           for values in itertools.product(*(template.params[n] for n in names))]
    if len(out) <= limit:
        return out
    step = len(out) / limit
    return [out[int(k * step)] for k in range(limit)]


def world_versions(pack: Pack) -> list[str]:
    out, acc = ["v0"], "v0"
    for d in pack.drift_schedule:
        acc = f"{acc}+{d}"
        out.append(acc)
    return out


def _questions(bank: QuestionBank, pack: Pack, template: Template, limit: int) -> list[Question]:
    plain = [p for p in pack.personas if p not in pack.persona_quirks()]
    return [bank.pose(template.id, plain[0], params) for params in combos(template, limit)]


def isolation_violations(gold: PackGold, bank: QuestionBank, pack: Pack, data: Data,
                         limit: int) -> list[str]:
    learnable = [q.id for q in pack.quirks if q.persona is None and q.kind != "poison" and q.gold is not None]
    out = []
    for template in bank.templates:
        for q in _questions(bank, pack, template, limit):
            for version in world_versions(pack):
                own = gold.compute(q, version, data)
                for other in learnable:
                    if other in template.quirks:
                        continue
                    if gold.compute(q, version, data, extra_quirks=(other,)) != own:
                        out.append(f"{template.id} {bank.hidden(q.id).params} @ {version}: changed by {other}")
    return out


def quirk_effects(gold: PackGold, bank: QuestionBank, pack: Pack, data: Data, limit: int) -> dict[str, float]:
    """template id → share of combinations whose gold differs from the poison variant (v0)."""
    variants = {v.params["quirk"]: {k: x for k, x in v.params.items() if k != "quirk"} for v in pack.poison_bank}
    out = {}
    for template in bank.templates:
        quirk = template.quirks[0] if template.quirks else None
        if quirk not in variants:
            continue
        qs = _questions(bank, pack, template, limit)
        differs = sum(gold.compute(q, "v0", data) != gold.compute(q, "v0", data, variant=(quirk, variants[quirk]))
                      for q in qs)
        out[template.id] = differs / len(qs) if qs else 0.0
    return out
