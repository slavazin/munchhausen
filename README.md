# Munchhausen

A self-learning agentic workflow, built for the [MongoDB SF Hackathon](https://cerebralvalley.ai/e/mongodb-sftw-hackathon).

> Named after Baron Munchausen, who pulled himself out of a swamp by his own hair: an agent that improves itself by learning from its own runs.

## Overview

Munchhausen is an agentic workflow that learns from experience. Each run's actions, outcomes and feedback go into MongoDB. Later runs pull up that stored experience and use it to plan and act better.

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
