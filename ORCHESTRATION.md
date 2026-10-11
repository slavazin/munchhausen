# Orchestration — surfaces, ownership, sandbox, evidence

Written 2026-10-11 12:45 PDT. Each implementation agent works in its own git worktree on one surface.
`CARRY_FORWARD.md` holds state and binding decisions; `SPEC.md` holds the design; `corpus/LANGUAGE.md` the lexicon.

## North star (every surface serves it)

**Admit only what the authority's figures reproduce out of sample.** Every learned decision passes a paired
out-of-sample backtest against confirmed figures, reaches the agent only through its hook, and carries a
revisit trigger. The backtest reads the authority, not the world (SPEC § 7.4 residue). The demo's one complete
story (SPEC § 13): Q1 learned → applied on an unseen template → D1 fires → superseded with tombstone → recovery
on the paired curve, plus the floor-view beat. Anything that does not move that story or its evidence is cut.

## Surfaces and file ownership

A surface edits only files it owns. Shared files take **additive** edits only (new methods/knobs/tests appended
at the end of the relevant class or section, never reordering or renaming). The orchestrator resolves merges.

| Surface | Milestone | Owns | Additive-only in |
|---|---|---|---|
| S1 world | M1 | `world/**`, `truth/**`, `engine/packs/**`, `commands/world.py`, `tests/test_world*.py`, `tests/test_gold*.py` | `config.py`, `ports/world.py`, `domain/question.py` |
| S2 forward + runtime sandbox | M2 | `agent/**`, `loop/episode.py`, `loop/runner.py`, `loop/residuals.py`, `impl/parties/proposer.py`, `impl/representation.py`, `impl/reranker.py`, `impl/similarity.py`, `bootstrap.py`, `commands/forward.py`, `domain/pipeline_guard.py`, `tests/test_forward*.py`, `tests/test_sandbox*.py` | `config.py`, `ports/store.py`, `store/repositories.py`, `store/atlas.py`, `ports/registry.py` |
| S3 shaping | M3a | `learn/observe.py`, `learn/episodic.py`, `learn/nominate.py`, `impl/parties/observer.py`, `impl/parties/nominator.py`, `impl/grouper.py`, `lint_language.py`, `tests/test_shaping*.py` | `config.py`, `ports/store.py`, `store/repositories.py`, `ports/registry.py` |
| S4 adjudication | M3b | `learn/layers.py`, `learn/backtest.py`, `learn/lifecycle.py`, `learn/curators.py`, `learn/direct.py`, `learn/adjudicate.py`, `impl/parties/lesson.py`, `impl/parties/self_grade.py`, `impl/lens_panel.py`, `bootstrap_learn.py`, `commands/learn.py`, `tests/test_adjudication*.py` | `config.py`, `ports/store.py`, `store/repositories.py`, `store/decisions.py`, `ports/registry.py`, `domain/admission.py` |
| S5 telemetry + evidence | M4 metrics | `metrics/**`, `evidence.py`, `impl/models_anthropic.py` (shared call path), `impl/sinks.py`, `impl/parties/planted_map.py`, `conf/forecasts.yaml`, `commands/telemetry.py`, `corpus/EVIDENCE.md`, `tests/test_telemetry*.py` | `config.py`, `ports/store.py`, `store/repositories.py`, `domain/registers.py`, `ports/registry.py` |
| S6 viewer | M4 viewer | `viewer/**`, `loop/inject.py`, `store/read_models.py` (new), `commands/viewer.py`, `tests/test_viewer*.py` | `config.py`, `ports/store.py`, `store/repositories.py` |

Seams laid by the orchestrator (commit "orchestration seams"):
- `impl/parties/<party>.py`: one module per LLM party, `async def run(llm: LLM, settings, ...)`. `AnthropicModels`
  owns only the shared call path (`parse`, `client`, `record_call`) and delegates each port method.
- `bootstrap_learn.backward_for(h, arm) -> RoundHook`: S4 builds it; S2's `bootstrap` calls it for `on_round_close`.
- `commands/<surface>.py: register(app)`: CLI commands per surface; `cli.py` is not edited.
- `ports/curation.Adjudicator.adjudicate(draft, ctx)`: S4 implements (`learn/adjudicate.py`); S3's episodic pass and
  S6's injection hand drafts to it.
- `evidence.start_run(h)` / `evidence.close_round(h, arm, round, idx_range)`: S5 implements; S2's `run` command
  and runner call them (start before the first episode; close after the backward hook of each round).

## Sandbox

**Build agents (this session):**
- One git worktree per surface. Commit on the worktree branch; never push, never merge, never touch `main`.
- `.env` is not in a worktree. To reach Atlas, load it into the process only:
  `set -a; source <repo>/.env; set +a; uv run ...`. Never print, log, commit
  or copy a secret value. `doctor` reports presence only.
- Atlas writes: S1 may rebuild databases `world` and `truth`. Every other surface writes to `munchhausen` only
  under `RUN_ID=wt-<surface>-<anything>` and may delete only its own `run_id` rows. Never drop a collection,
  index or database in `munchhausen`; never touch `sample_analytics`.
- Unit tests run offline (fakes for `Models`, `Store`, `World`). Live model calls only when a key is present,
  behind an explicit `-m live` marker or a CLI command, never in the default `uv run pytest`.

**Runtime parties (the harness's own agents), enforced in code:**
- Proposer and nominator pipelines run through `domain/pipeline_guard.py` at the store boundary (every
  `DocumentReader.aggregate` on `world`): stage allowlist; refuse `$out`, `$merge`, `$function`,
  `$accumulator`, `$where`, `$currentOp`, `$listSessions`, `$collStats`/`$indexStats`; `$lookup`,
  `$graphLookup`, `$unionWith` only into `world` collections/views; `maxTimeMS`; row cap.
- Learner code (`learn/ agent/ loop/`) never imports `truth`/`world` (architecture test); arms without an
  authority read episodes through `EpisodeRepository.for_learner`. The `truth` DB handle exists only on the
  evaluation side (`bootstrap.Harness.world()`).
- Per-role Atlas users (learner/evaluator/executor, SPEC § 20.2) are created by the user in Atlas; until they
  exist, `doctor` reports `isolation: convention` and the run record says so.

## Evidence (telemetry design, owned by S5; every surface emits into it)

Every number on a slide must be re-derivable from Atlas by a named query, with unit, population and n.
- `runs`: run id, git sha + dirty flag, every knob, port selection per arm, capabilities, isolation mode,
  model ids, a hash of every party's system prompt, pack hash, world build counts, forecasts (written before
  the first episode, never edited), start/end.
- `spend` (time series): one row per model call: arm, stage, model, tokens in/out/cache, latency, usd,
  prompt hash, request id.
- `episodes`, `observations`, `drafts` (per-layer adjudication), `backtests` (per-sample paired outcomes and
  context), `fires`, `decisions` (lifecycle, amendments), `tool_access` (view rewires, pre/post images).
- `rounds`: `$merge` at each round close: accuracy, self-assessed accuracy, calibration gap, store sizes,
  lifecycle counts, fires, tokens and usd per episode, per arm.
- `events` (Trace port `jsonl` → `var/runs/<run_id>/events.jsonl`): one line per state change, for the
  replay scrubber and the timeline.
- `munchhausen report <run_id>` → `var/reports/<run_id>/`: `readings.json` (each forecast beside its reading:
  paired difference, interval, n, verdict), `report.md`, a self-contained `report.html` with the curves, and
  `manifest.json` mapping each figure to the query that produced it.
