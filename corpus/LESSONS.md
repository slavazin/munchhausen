# LESSONS — build errors and the rules that prevent them

Population: the six-surface build of 2026-10-11 (S1–S6, the pilot gate), merged on `integration` at 0158818.
Each instance cites a commit, a file:line at 0158818, or the orchestrator's error log; an entry the git
history does not show is marked *(log only)*. Each rule is a Do plus the overshoot it guards against (LANGUAGE.md L3).

## 1. Orchestration setup is rediscovered by every surface

- Worktrees are cut from `main` (ab6a596), six commits behind the seam base 5e5ede3; each build agent resets itself *(resets: log only)*.
- The sandbox blocks the `source .env` that ORCHESTRATION.md:43 prescribes; agents improvise `Settings(_env_file=…)` (scratchpad `live.py:7`, `s3_live.py:22`, `s5_live.py:16`).
- `.env` names differ from config names: three alias commits (a8ab111, 59a836e, de2dc36); an org key needs a workspace id (59a836e); the OAuth token serves only haiku-4-5 *(log only)*.
- One shared scratchpad: agents overwrite each other's `live.py`; credential probing trips the safety classifier *(both log only)*. The `live` marker needs a root `pyproject.toml` edit no surface owns (d967452).

**Caught:** first live call per agent. **Cost:** each agent spends its first minutes on the same repair; an un-reset worktree builds without the seams.
**Rule:** Do state base sha, env loading, key names and scratch prefix in the brief; Don't leave each agent to find them (six private `_env_file=` workarounds).
**Mechanism:** brief lines below; `engine/tests/test_config.py::test_env_example_names_resolve` asserts every key in `.env.example` maps to a `Settings` field or alias.

## 2. Seam contracts are left implicit

- `idx_range`: the runner emits half-open, S5 reads inclusive, S3 switches to inclusive after review; integration fixes all to half-open (b48293e, 1890a68; `store/repositories.py:421`).
- V and injection share negative idx: S5 reads `v_at` (absent), S6 groups V by idx and injects at the next free negative idx (67eab3f). Fixed by `Episode.v_at` (b48293e) and `INJECT_IDX_BASE` (08bc2c2; `config.py:265`).
- Seams called, never assigned: S6 calls `bootstrap.forward_pass`, `nominator_for`, `owner_port` (d110094 `commands/viewer.py:6-9`); none exists until 08bc2c2.
- Stringly-typed seams: S5 finds the episode id by ContextVar *name* `current_episode_id`, S2 names its var otherwise; integration adds a second var (92fd025; `agent/usage.py:26-28`). Event names diverge until `TRACE_EVENTS` exists (06f9094; `domain/registers.py:152`).
- Fields read, never written: `episodes.tokens` (written in f56437c); admission index overwritten on supersede, approximated two ways (89c5af8 M6, 08bc2c2).

**Caught:** integration merge; S6 review. **Cost:** an inclusive bound counts the boundary episode in two rounds, shifting every round record; injected episodes land in V accuracy, the demo's curve.
**Rule:** Do declare every cross-surface convention (range bounds, id namespaces, event names, context keys) as a typed constant or stub before launch; Don't let a consumer infer it from a docstring (`ports/store.py` said "(first, last), both inclusive" before b48293e).
**Mechanism:** `engine/tests/test_seams.py` imports every seam ORCHESTRATION.md names and checks `inspect.signature` against the declared one, so an unassigned seam fails at M0.

## 3. A dispositive path fails silently

- `bootstrap_learn` calls `consulter_for(spec.consultation, …, settings=, store=)` (add1eca) against `consulter_for(spec: ArmSpec, *, …)` (12d0689 `agent/consultation.py:106`). `Backtester._pair` catches `Exception` (`learn/backtest.py:253`): every pair drops, `governed` never admits, nothing raises. Fixed by `Harness.consulter` (f56437c; `bootstrap_learn.py:74-77`) and INSUFFICIENT holding (89c5af8 B1).
- Proxy readings print "agrees" with no planted map; fixed to `unread (proxy)` (06f9094; `metrics/readings.py:218-224`).
- Tokens per episode a fabricated 0; error episodes count as misses; `finish_run` never called (06f9094 M2, M4, M5).

**Caught:** second-round review, not unit tests (each surface fakes the other). Two reviewers find the same bug (S2 B1, S4 B1, log), and S2's fix edits S4-owned `bootstrap_learn.py` (f56437c).
**Cost:** the story's first beat (Q1 admitted) never happens, and the run reads as a cautious adjudicator.
**Rule:** Do let programming errors (`TypeError`, `AttributeError`) raise out of admission, retirement and verdict paths, and print `unread` for absent data; Don't map an exception or an empty population to a refusal, a 0 or "agrees".
**Mechanism:** add `"BLE"` to ruff `select` in `pyproject.toml` (9 of 23 broad excepts carry a `noqa: BLE001` that nothing enforces); `engine/tests/test_dispositive_errors.py` injects a `TypeError` into the consulter fake and asserts `Backtester.run` raises.

## 4. A recorded value differs from the behaviour

- `runs.knobs` records proposer temperature 0.0; `messages.parse` takes no `temperature`, so none is sent. Fixed via `extra_body` (06f9094; `impl/models_anthropic.py:109-110`). haiku-5-5 then refuses it with a 400; the knob defaults to None (14fc0b8; `config.py:113-115`).
- `pack_file_hash` versus `World.pack_hash` writes a false pack-mismatch note (5b049ca). Served model is recorded beside the registered one (1bc9678, 4b3e28a).
- Doc drift: `SPEC.md:90`, `SPEC.md:553` and `CARRY_FORWARD.md:156` name `claude-haiku-4-5` as proposer; `config.py:225` is `claude-haiku-5-5`.

**Caught:** S5 review; the pilot (400); this review (docs). **Cost:** the run record claims a determinism the proposer never had, and replay noise reads as a draft's effect (hence applied-gated fixes, 89c5af8 M1).
**Rule:** Do record the request body sent and `msg.model` served; Don't record a configured knob as evidence of behaviour, or move a default without the SPEC row.
**Mechanism:** `engine/tests/test_telemetry.py::test_recorded_knobs_are_sent` captures fake-client kwargs; `engine/tests/test_docs_knobs.py` compares model ids in SPEC § 16 and CARRY_FORWARD with `Settings()` defaults.

## 5. Learning validity leaks past unit tests

- Held-out not held out: neighbour residuals show the nominator backtest-population figures (b380be0); `Draft.nominator_seen_episode_ids` (`domain/draft.py:89`) leaves the population (89c5af8 B3).
- V not sealed: persona in the key, 31/40 V questions also in the stream *(count: log only)*; fixed with stratification (91de0ed `world/questions.py`).
- Poison variants equal the convention; one Q1 template moves against D1 (91de0ed).
- Retirement counts corroborating fires, so Q1 retires before supersession (89c5af8 B2; `learn/lifecycle.py:106`).
- Injected false figures reach the organic pass, and the owner can admit them (08bc2c2; `bootstrap_learn.py:295`). The coherence guard dissolves P1/Q3 shapes; a cumulative direction read refuses D1's supersede (b380be0).

**Caught:** adversarial review only; each passed its surface's tests. **Cost:** leaks inflate the backtest and V; retirement and the direction read kill the D1 → supersede beat.
**Rule:** Do encode each SPEC learning invariant (§ 6.3, § 7.4) as a test that builds the adversarial case; Don't accept a test that only shows the happy path admits.
**Mechanism:** `engine/tests/test_learning_design.py` gains one test per item of review-rubric point 4; the brief names the invariant tests each surface owns.

## 6. Sandbox gaps at second-order surfaces

- LLM-written floor predicates become views without the pipeline guard; fixed by `check_floor` (f56437c; `domain/pipeline_guard.py:72`) and an L0 gate (89c5af8 M4).
- `$lookup`/`$unionWith` from another collection bypass a floor view; fixed by `rewrite_targets` (`pipeline_guard.py:83`). Lifecycle drops any view a register row names; fixed to floor-view names (89c5af8 M4).
- Open: the vendor-import rule matches `typesafe` and `typesafe.*` (`tests/test_architecture.py:33,45`); `impl/lens_panel.py:87` imports `typesafe_sdk`, which no rule checks.

**Caught:** S2 and S4 review, independently. **Cost:** model text reaches Atlas as code; the floor-view beat binds only pipelines that name the collection.
**Rule:** Do pass every LLM-written artifact bound for Atlas (pipeline, view, match, sub-pipeline) through one guard; Don't guard only the first-order `aggregate`.
**Mechanism:** `engine/tests/test_sandbox.py::test_every_world_write_passes_the_guard` over `WorldWriter` methods; the architecture rule lists import names (`typesafe_sdk`), not package names.

## 7. Model-written data is decoded wrong, and the gate that finds it runs late

- `json.loads` leaves `{"$date": …}` an object: 24/40 pilot answers empty *(count: log only)*; fixed in `domain/pipeline_json.py:31,53` (af5afda); latent in the nominator's tool and floor matches (1ac90ce).
- Shell syntax (`ISODate(…)`), trailing commas, `$toInt` on decimal text, value casing: repaired and recorded (`Proposal.repairs`), schema notes (`world/adapters/sample_analytics.py:100`).
- S1's V seal changes the stream: controls move to 0.65 on haiku-4-5 (14fc0b8; prior 0.85 log only).

**Caught:** the pilot gate, run after all merges although `CARRY_FORWARD.md:168-180` orders it first. **Cost:** controls read 5/14 *(log only)*, which first points at the model, not the decoder.
**Rule:** Do decode model JSON through `parse_pipeline` and run the pilot before surfaces build on the proposer; Don't call `json.loads` on model output bound for Atlas, or reuse a pilot reading after the stream moves.
**Mechanism:** `tests/test_architecture.py::test_no_raw_json_loads_in_parties` (allow `domain/pipeline_json.py` only); the pilot reading stores a stream hash that `report` checks.

## 8. Tests pin stubs; fakes drift from ports

- `test_round_hook_tolerates_unbuilt_seams` relies on live `NotImplementedError`; it breaks once seams exist and needs monkeypatches (b48293e, 9164e1c).
- Fakes lack new port methods: `_Stub.observe` (9164e1c), `Terms.all(run_id=)` (0158818), `FakeStore.runs`, `FakeEpisodes.for_learner` *(log only)*.
- Per-surface fakes hide § 3's signature bug.

**Caught:** integration merge. **Cost:** a red suite per merge; green fakes conceal wiring.
**Rule:** Do simulate "unbuilt" by monkeypatching the seam to raise, and check fakes against their Protocol; Don't assert on today's stub, or hand-write a fake per surface.
**Mechanism:** `engine/tests/test_fakes_conform.py` compares each fake's methods with its `ports/` Protocol by `inspect.signature`; one shared `engine/tests/fakes.py`.

## Brief template additions

- "Your worktree may be cut from `main`. Run `git log -1 --format=%h` and `git merge-base --is-ancestor <seam-sha> HEAD`; on failure, `git reset --hard <seam-sha>`."
- "Load secrets with `uv run --env-file <path>/.env …`. Never `source`, read or print a value; verify credentials only with `munchhausen doctor` / `ping`."
- "Prefix every scratch file with your surface id (`s3_live.py`, never `live.py`)."
- "Every seam you call exists as a stub with its final signature in `<seam-sha>`. A missing one: stop and report; don't invent it."
- "Conventions: `idx_range` is `[lo, hi)`; V episodes carry `v_at`; injection idx ≤ `INJECT_IDX_BASE`; event names come from `TRACE_EVENTS`."
- "Add one integration test per composition seam you build or call, composing the real `Harness` with fakes only at vendor ports."
- "No broad `except` in admission, retirement or verdict paths; absent data reads `unread`, never 0."
- "A knob you record is the value you send."
- "Decode model-written JSON through `domain/pipeline_json.parse_pipeline`."
- "A defect in a file you don't own goes into your report with file:line; don't patch it."

## Integration checklist (every merge)

1. `git merge-base --is-ancestor <seam-sha> <branch>`.
2. Merge one branch; run `uv run pytest` and `uv run ruff check engine viewer` before the next.
3. Grep the merged diff: `$lte` beside `idx`, negative idx literals, event names outside `TRACE_EVENTS`, `json.loads` in `impl/parties/`, new `except Exception`.
4. Composition tests green: `test_adjudication_bootstrap.py`, `test_forward_runner.py`, `test_viewer.py::test_injector_for_builds_against_a_real_harness`.
5. A defect two surfaces report is fixed once at its source and broadcast (two copies of the `lineage` flatten remain: `store/decisions.py:70`, `:124`).
6. Assign each review finding one owner before fix rounds start.
7. After a merge touching `world/questions.py`, the proposer prompt or the decoder: rerun the pilot gate and record the stream hash.
8. A moved default updates SPEC § 16 and CARRY_FORWARD in the same commit.

## What worked

- Adversarial reviewers find every § 5 defect; no implementer test finds one (91de0ed, b380be0, 89c5af8, 08bc2c2).
- File ownership keeps integration fixes small: b48293e is 15 lines over 6 files, 0158818 is 4 lines.
- Seam stubs raising `NotImplementedError("M<n>: …")` (66ec1ba, 5e5ede3) let six surfaces build and test in parallel.
- Each review fix ships a regression test named for its finding (`test_b2_corroborating_fires_never_retire`).
- Additive-only schemas keep merges clean: fixes add fields (`Episode.v_at`, `Backtest.errors`, `Draft.source`), none renames one.
- The pilot fixes mechanics before raising the model, with readings in the commit message (af5afda, then 14fc0b8).
