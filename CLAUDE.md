# Munchhausen — working notes for Claude sessions

Start with `CARRY_FORWARD.md` (current state, binding decisions, next steps). `SPEC.md` is the design; `corpus/LANGUAGE.md` is the lexicon (one meaning per term — use it in code and prose).
North star: **admit only what the authority's figures reproduce out of sample.** Every learned decision passes a
paired out-of-sample backtest against confirmed figures, reaches the agent only through its hook, and carries a
revisit trigger. The backtest reads the authority, not the world: a consistently wrong authority passes it (SPEC § 7.4).

## Commands
- `uv sync --all-packages` — install the workspace (engine + viewer)
- `uv run pytest` — tests, including the architecture rules
- `uv run ruff check engine viewer`
- `uv run munchhausen doctor | ping | setup | arms`

## Layout (engine/munchhausen)
- `domain/` pure models + invariants (entry contract, lifecycle, latches, backtest read, admission plan)
- `ports/` Protocols for every seam; `ports/registry.py` maps implementation names → import paths
- `agent/` `loop/` `learn/` `metrics/` application services; depend on domain + ports only
- `world/` `truth/` evaluation side (hidden tags, gold); reached only through the World port
- `store/` Atlas (only `pymongo` importer); `store/decisions.py` is the only writer of `decisions`
- `impl/` vendor implementations (only importer of anthropic/voyageai/typesafe/raindrop)
- `bootstrap.py` composition root; `config.py` every knob; `conf/*.yaml`, `packs/*.yaml` registers

## Rules (tests/test_architecture.py enforces the mechanical ones)
- Never read gold from `learn/`, `agent/`, `loop/`. Replays score against `episodes.confirmed_figure`.
- Arms without an authority never read `EVALUATION_ONLY_FIELDS` (use `EpisodeRepository.for_learner`).
- Decisions are frozen at admission; only `lifecycle`, `evidence_state`, `amendments` change, via the
  six lifecycle functions. Atomic changes are domain plans (`domain/admission.py`) committed by the store.
- No literals: add a knob to `config.py` first. No branching on dataset/embedder/vendor names outside
  the registry. New implementation = registry entry + class with `create(name, settings, store)`.
- Schemas are additive after M0: never rename or drop a field. Validators derive from domain models.
- Unimplemented pieces raise `NotImplementedError("M<n>: …")` naming their milestone.
