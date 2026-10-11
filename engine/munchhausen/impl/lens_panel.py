"""LensPanel implementations: TypeSafe Jev (corroborating), and `none`.

Jev answers each lens as a `system_one` question over a state holding only the fields the lens's `pointer`
names (§ 23.2: never another lens's score, never the draft's `lens_score`). `LENS_CALL_MODE=isolated` (the
default) asks one lens per call, so lenses do not share a wording prior (§ 24.2 L4); `joint` asks all in one.
With `LENS_PHRASINGS` > 1 each lens is asked in that many of its phrasings; the score is their mean and the
hedging read, mean 4p(1−p), is returned beside it as `hedge:<lens>` (§ 24.2 L6). Weights read lens ids only,
so the hedging keys never move the score.

`noul` lenses return P(yes); a yes is the reading the angle asks about (e.g. `case_leak` yes = the payload is
an answer sheet, which its −2 seed weight penalizes). `choice` lenses return P(first level).
With no TypeSafe key, or a failed call, a lens records nothing and L3 (record mode) passes: the panel is
corroborating and never blocks the dispositive backtest.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Sequence
from typing import Any, Self

from munchhausen.config import Settings
from munchhausen.domain.decision import Decision
from munchhausen.domain.draft import Draft
from munchhausen.domain.lens import LensEntry
from munchhausen.domain.observation import Observation
from munchhausen.impl._base import NoDeps, key


def lens_state(lens: LensEntry, draft: Draft, sources: Sequence[Observation],
               neighbours: Sequence[Decision]) -> dict[str, Any]:
    """Only the fields the lens's `pointer` names."""
    out: dict[str, Any] = {}
    for ptr in lens.pointer:
        if ptr == "draft.payload":
            out.setdefault("draft", {})["payload"] = draft.payload
        elif ptr == "draft.kind":
            out.setdefault("draft", {})["kind"] = draft.kind.value
        elif ptr == "draft.latches.hook":
            out.setdefault("draft", {})["hook"] = draft.hook.model_dump(mode="json")
        elif ptr == "sources.noticed":
            out["sources"] = [{"noticed": o.noticed, "persona": o.persona, "template": o.template} for o in sources]
        elif ptr == "neighbours.payload":
            out["neighbours"] = [{"title": d.title, "payload": d.payload,
                                  "hook": d.hook.model_dump(mode="json")} for d in neighbours]
    return out


def lens_question(lens: LensEntry, phrasing: str) -> dict[str, Any]:
    if lens.product == "choice":
        return {"type": "choice", "instructions": phrasing, "criteria": {lv: None for lv in lens.levels}}
    return {"type": "noul", "instructions": phrasing, "criteria": {"false": lens.counterfactual}}


def lens_p(lens: LensEntry, answer: Any) -> float | None:
    if answer is None:
        return None
    if lens.product == "choice":
        probs = getattr(answer, "probabilities", None) or {}
        return float(probs.get(lens.levels[0], 0.0)) if lens.levels else None
    p = getattr(answer, "noul", None)
    return None if p is None else float(p)


class JevLensPanel:
    id = "jev"

    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls(settings.lenses(), key(settings, "typesafe_api_key"), call_mode=settings.lens_call_mode,
                   phrasings=settings.lens_phrasings, concurrency=settings.lens_max_concurrency,
                   model=settings.lens_model, timeout_s=settings.lens_timeout_s)

    def __init__(self, lenses: Sequence[LensEntry], api_key: str | None = None, *, call_mode: str = "isolated",
                 phrasings: int = 1, concurrency: int = 5, model: str | None = None, timeout_s: float = 20.0,
                 client: Any = None) -> None:
        self._lenses = [lens for lens in lenses if lens.status == "active"]
        self._api_key, self._mode, self._model, self._timeout = api_key, call_mode, model, timeout_s
        self._k = max(1, min(3, phrasings))
        self._concurrency = max(1, concurrency)
        self._client = client
        self.errors: list[str] = []

    def _get_client(self) -> Any:
        if self._client is None and self._api_key:
            from typesafe_sdk import AsyncTypeSafeClient

            self._client = AsyncTypeSafeClient(api_key=self._api_key, model=self._model, timeout=self._timeout)
        return self._client

    async def score(self, draft: Draft, sources: Sequence[Observation],
                    neighbours: Sequence[Decision]) -> dict[str, float]:
        client = self._get_client()
        if client is None:
            return {}
        sem = asyncio.Semaphore(self._concurrency)
        answers: dict[tuple[str, int], Any] = {}
        if self._mode == "joint":
            state = {k: v for lens in self._lenses for k, v in lens_state(lens, draft, sources, neighbours).items()}
            for j in range(self._k):
                res = await self._call(client, sem, state,
                                       {lens.id: lens_question(lens, lens.phrasings[j]) for lens in self._lenses})
                for lens in self._lenses:
                    answers[(lens.id, j)] = res.get(lens.id) if res else None
        else:
            asks = [(lens, j) for lens in self._lenses for j in range(self._k)]
            results = await asyncio.gather(*(self._call(client, sem, lens_state(lens, draft, sources, neighbours),
                                                        {lens.id: lens_question(lens, lens.phrasings[j])})
                                             for lens, j in asks))
            for (lens, j), r in zip(asks, results, strict=True):
                answers[(lens.id, j)] = r.get(lens.id) if r else None
        out: dict[str, float] = {}
        for lens in self._lenses:
            ps = [p for j in range(self._k) if (p := lens_p(lens, answers.get((lens.id, j)))) is not None]
            if ps:
                out[lens.id] = sum(ps) / len(ps)
                if len(ps) > 1:
                    out[f"hedge:{lens.id}"] = sum(4 * p * (1 - p) for p in ps) / len(ps)
        return out

    async def _call(self, client: Any, sem: asyncio.Semaphore, state: dict[str, Any],
                    questions: dict[str, Any]) -> dict[str, Any] | None:
        async with sem:
            try:
                res = await client.system_one(state, questions)
            except Exception as e:  # a lens that fails records nothing; the panel is corroborating
                msg = f"{type(e).__name__}: {e}"
                self.errors.append(msg)
                print(f"[lens_panel] jev call failed: {msg}", file=sys.stderr)
                return None
        return dict(res.answers)


class NoLensPanel(NoDeps):
    """No corroborating panel: L3 passes every draft through to the dispositive backtest."""

    id = "none"

    async def score(self, draft: Draft, sources: Sequence[Observation],
                    neighbours: Sequence[Decision]) -> dict[str, float]:
        return {}
