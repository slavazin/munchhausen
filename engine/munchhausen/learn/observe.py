"""Observer (SPEC § 7.1, § 23.1): one observation per noticing on each miss, written blind.

The noise filter classifies each miss as reducible or irreducible; irreducible observations are stored
with disposition `noise` and never join a shape. A miss whose execution failed or read no answer is
irreducible by construction and is classified mechanically, with no model call.

Every note is linted at write (`lint_noticed`); a note that names a party or a moment, prescribes a fix or
runs past three sentences is refused, never stored, and the refusal is traced. The authority's phrasing
goes verbatim into `surfaces.phrasing` (the harness copies it; the model never rewrites it).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from munchhausen.domain.common import emb_key
from munchhausen.domain.episode import Episode
from munchhausen.domain.ids import observation_id
from munchhausen.domain.observation import (
    Observation,
    ObservationClass,
    ObservationDisposition,
    ObservationNote,
    Surfaces,
    Via,
)
from munchhausen.domain.scoring import ratio_delta
from munchhausen.lint_language import lint_noticed
from munchhausen.ports.models import Models
from munchhausen.ports.representation import Representation
from munchhausen.ports.sinks import Trace
from munchhausen.ports.store import ObservationRepository

MASK_TOKEN = "_"
NOISE_FILTER = "noise_filter"   # disposed_by: mechanical noise (execution error, no answer read)
OBSERVER = "observer"           # disposed_by: noise the observer model classed irreducible


def mechanical_noise(episode: Episode) -> ObservationNote | None:
    """Execution error or no answer read: irreducible without asking a model (§ 7.1 noise filter)."""
    if episode.error is None and episode.answer is not None:
        return None
    gap = f"fails with {episode.error.split(':')[0]}" if episode.error else "reads no answer"
    noticed = f"The pipeline on {episode.collection} {gap} at answer path {episode.answer_path}."
    return ObservationNote(cls=ObservationClass.IRREDUCIBLE, noticed=noticed,
                           surfaces=Surfaces(terms=tuple(episode.terms), collection=episode.collection,
                                             phrasing=episode.phrasing))


def masked(text: str, note: ObservationNote, template: str) -> str:
    """E1 (`EMBED_MASK=surfaces`): mask collection, field and template tokens so clusters track the concept
    rather than the identity of the template."""
    tokens = [t for t in (note.surfaces.collection, *note.surfaces.fields, template) if t]
    for tok in sorted(tokens, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(tok)}\b", MASK_TOKEN, text)
    return text


@dataclass
class Observer:
    models: Models
    representation: Representation
    observations: ObservationRepository
    embed_mask: Literal["none", "surfaces"] = "none"
    trace: Trace | None = None
    refused: list[tuple[str, list[str]]] = field(default_factory=list)   # (episode id, lint problems)

    async def observe(self, episode: Episode, round_: int) -> list[Observation]:
        """Idempotent per episode: a re-run after the first observation landed writes nothing new."""
        if await self.observations.get(observation_id(episode.id, 0)) is not None:
            return []
        noise = mechanical_noise(episode)
        notes = [noise] if noise is not None else list(await self.models.observe(episode))
        if not notes:
            self._event("observation.none", {"episode_id": episode.id})
        kept: list[ObservationNote] = []
        for note in notes:
            problems = lint_noticed(note.noticed)
            if problems:
                self.refused.append((episode.id, problems))
                self._event("observation.refused", {"episode_id": episode.id, "problems": problems,
                                                    "class": note.cls.value})
                continue
            kept.append(note)
        texts = [masked(n.noticed, n, episode.template) if self.embed_mask == "surfaces" else n.noticed
                 for n in kept]
        vectors = await self.representation.embed(texts, "observation") if kept else None
        ratio, delta = ratio_delta(episode.answer, episode.figure)
        out: list[Observation] = []
        for k, note in enumerate(kept):
            noise_class = note.cls is ObservationClass.IRREDUCIBLE
            emb = {emb_key(self.representation.id): vectors[k].tolist()} if vectors is not None else {}
            obs = Observation(
                _id=observation_id(episode.id, k), run_id=episode.run_id, arm=episode.arm,
                episode_id=episode.id, via=Via.OBSERVER, cls=note.cls, noticed=note.noticed,
                surfaces=note.surfaces.model_copy(update={"phrasing": episode.phrasing}),
                template=episode.template, persona=episode.persona, answer=episode.answer,
                figure=episode.figure, ratio=ratio, delta=delta, pipeline=episode.pipeline,
                retry_pipeline=episode.retry_pipeline, retry_correct=episode.retry_correct,
                signature_guess=note.signature_guess, re_check_when=note.re_check_when,
                disposition=ObservationDisposition.NOISE if noise_class else ObservationDisposition.OPEN,
                disposed_by=(NOISE_FILTER if note is noise else OBSERVER) if noise_class else None, round=round_,
                rep={"embedder_id": self.representation.id} if emb else {}, emb=emb)
            await self.observations.put(obs)
            self._event("observation.written", {"id": obs.id, "episode_id": episode.id,
                                                "class": obs.cls.value, "disposition": obs.disposition.value,
                                                "terms": list(obs.surfaces.terms), "embedded": bool(emb)})
            out.append(obs)
        return out

    def _event(self, name: str, payload: dict[str, object]) -> None:
        if self.trace is not None:
            self.trace.event(name, payload)
