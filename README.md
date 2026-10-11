# Munchhausen

A self-learning agentic workflow, built for the [MongoDB SF Hackathon](https://cerebralvalley.ai/e/mongodb-sftw-hackathon).

> Named after Baron Munchausen, who swore he pulled himself out of a swamp by his own hair. An agent that grades itself is the Baron; this harness checks his story against an outside authority.

## Overview

Munchhausen is a governance layer for an agent's stored decisions, over MongoDB Atlas. A data agent answers business questions; when it misses, a stakeholder authority returns the figure it expected. The harness groups those misses, drafts a decision that would settle them, and admits it only if a paired, out-of-sample backtest shows it fixes other questions the authority already answered without breaking ones that were right. Each admitted decision reaches the agent only through its own hook and carries a revisit trigger that supersedes it when the authority's figures move.

What the claim covers: a decision is admitted only when the authority's figures reproduce its effect out of sample. The backtest reads the authority, not the world, so an authority that is wrong the same way every time would pass it. Readings compare arms on the same questions as paired differences with intervals; `governed − ungated` isolates the effect of the gate.

## Status

🚧 Work in progress, built during the hackathon.

## Getting Started

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env          # set MONGODB_URI (+ model keys)
uv sync --all-packages
uv run pytest
uv run munchhausen doctor     # which knobs/keys are configured (no secret values)
uv run munchhausen ping       # Atlas connectivity + capabilities
uv run munchhausen setup      # collections, validators, indexes in `munchhausen`
```

Design: [`SPEC.md`](SPEC.md). Lexicon: [`corpus/LANGUAGE.md`](corpus/LANGUAGE.md).
Concepts are drawn from the GCE doctrine ([`gce/GCE-DOCTRINE.md`](gce/GCE-DOCTRINE.md)), cited as ideas, not shipped code.

## Provenance

Schemas imported from prior projects live under [`prior/`](prior/) in a single commit, "import prior schemas".
Everything under `engine/` and `viewer/` was written on the day.

## License

MIT
