"""The port registry: implementation name → import path, per port (SPEC § 21).

This is the one place allowed to know implementation names. Nothing else branches on a dataset name, an
embedder name or a vendor key. Entries are import paths resolved lazily, so an optional SDK that is not
installed fails only when its implementation is selected.
"""

from __future__ import annotations

import importlib
from typing import Any

REGISTRY: dict[str, dict[str, str]] = {
    "world": {
        "pack": "munchhausen.world.pack_world:PackWorld",   # adapter + quirk pack; composes Truth=pack_gold
    },
    "adapter": {
        "sample_analytics": "munchhausen.world.adapters.sample_analytics:SampleAnalyticsAdapter",
    },
    "representation": {
        "voyage-4": "munchhausen.impl.representation:VoyageRepresentation",
        "voyage-4-lite": "munchhausen.impl.representation:VoyageRepresentation",
        "none": "munchhausen.impl.representation:NoRepresentation",
    },
    "reranker": {
        "rerank-3": "munchhausen.impl.reranker:VoyageReranker",
        "rerank-3-lite": "munchhausen.impl.reranker:VoyageReranker",
        "identity": "munchhausen.impl.reranker:IdentityReranker",
    },
    "similarity": {
        "atlas-vector": "munchhausen.impl.similarity:AtlasVectorSimilarity",
        "atlas-exact": "munchhausen.impl.similarity:AtlasVectorSimilarity",
        "numpy": "munchhausen.impl.similarity:NumpySimilarity",
    },
    "grouper": {
        "agglomerative": "munchhausen.impl.grouper:AgglomerativeGrouper",
    },
    "lens_panel": {
        "jev": "munchhausen.impl.lens_panel:JevLensPanel",
        "none": "munchhausen.impl.lens_panel:NoLensPanel",
    },
    "curator": {
        "governed": "munchhausen.learn.curators:governed",
        "naive": "munchhausen.learn.curators:naive",
        "self_ref": "munchhausen.learn.curators:self_ref",
        "hitl": "munchhausen.learn.curators:hitl",
    },
    "memory_sink": {
        "null": "munchhausen.impl.sinks:NullMemorySink",
    },
    "trace": {
        "null": "munchhausen.impl.sinks:NullTrace",
        "jsonl": "munchhausen.impl.sinks:JsonlTrace",
    },
    "signal_source": {
        "none": "munchhausen.impl.sinks:NoSignalSource",
    },
    "models": {
        "anthropic": "munchhausen.impl.models_anthropic:AnthropicModels",
    },
    "store": {
        "atlas": "munchhausen.store.atlas:AtlasStore",
    },
}

# Offline or null implementation per port: every port has one (SPEC § 21 port invariants).
NULL_IMPLEMENTATION: dict[str, str] = {
    "representation": "none",
    "reranker": "identity",
    "similarity": "numpy",
    "lens_panel": "none",
    "memory_sink": "null",
    "trace": "null",
    "signal_source": "none",
}


class UnknownImplementation(KeyError):
    pass


def resolve(port: str, name: str) -> Any:
    """Return the class or factory registered for (port, name)."""
    try:
        path = REGISTRY[port][name]
    except KeyError as e:
        known = sorted(REGISTRY.get(port, {}))
        raise UnknownImplementation(f"no {port!r} implementation named {name!r}; known: {known}") from e
    module, _, attr = path.partition(":")
    return getattr(importlib.import_module(module), attr)


def names(port: str) -> list[str]:
    return sorted(REGISTRY[port])
