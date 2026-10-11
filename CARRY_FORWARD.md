# Carry-forward — session state for the next implementer

Written 2026-10-11 11:53 PDT, after M0. Amended 2026-10-11 12:21 PDT after the M0 adversarial review
(`the M0 review (external, not in this repo)`, against `4764f2f`); § 3a lists what changed. Read this,
then `CLAUDE.md`, then the SPEC sections named under **Next**. `SPEC.md` is the design and holds wherever
this file is silent. Where this file records a decision that departs from or resolves the spec, this file
holds. Exception, once: the review changed the design itself, so the SPEC was amended to state the new
shape (§ 0, 4.2–4.4, 5, 6.3, 7.1–7.4, 9, 10.1, 11–14, 16, 18, 21, 24.1). M0 resolutions 9 and 16 below are
now also stated in the SPEC.

**Amended 2026-10-11 13:30 PDT after the orchestrated M1–M4 build (§ 0 below).** § 0 supersedes § 1, § 5 and
§ 6 where they differ; § 3/§ 3a still bind. **Amended again 15:00 PDT: § 00 (Run A in flight) supersedes § 0's
"Open / next" and adds binding decisions 14–22.**

---

## 00. Run A in flight (15:00) — state, decisions 14–22, post-run checklist

**Run A** (`RUN_ID=run-a`, 600 stream episodes, D1_AT=300, V at 75/225/375/525). Each arm runs from its own
pinned detached worktree (sibling dirs `munch-run-a*`), so merges into `m0-scaffold` never swap code under a live
process; every later join is recorded in `runs.resumes[]`. Logs: `var/runs/run-a.<arm|direct>.log`; events:
`var/runs/run-a/events.jsonl` (all arms write to the main repo's `var/` via `VAR_DIR`).

| Arm(s) | Snapshot | Started | Overrides |
|---|---|---|---|
| frozen | `5c17115` (munch-run-a) | 14:40 | defaults, TRACE_IMPL=jsonl,raindrop — **done**: 600/600, 0 failed, 0 V holes |
| naive, self_ref | `9958173` (munch-run-a2) | 14:50 | WORKERS_PER_ARM=10, RAINDROP_DEBUG=false |
| ungated | `93a0bc9` (munch-run-a3) | 14:52 | + BAR_MIN_TEMPLATES_FLOOR=2 BACKTEST_SAMPLE=random BACKTEST_N=16 BACKTEST_CONCURRENCY=8 |
| governed | `a9ff9bf` (munch-run-a4) | 14:53 | same as ungated |

Expected end ≈ 15:45–15:50 (naive bounds wall clock). Watch: `uv run munchhausen status run-a --length 600`.
Evidence so far: `rehearsal-1` (240 eps, D1=120) passed every story beat — governed Q1 `st∈{2,7}` admitted @60 on
held-out fixes, fire @127, successor `st∈{2,4,7}` @180 (latency 60); ungated floor view `rs≠3`; planted map maps
self_ref 0/128 to a quirk, governed 3/3. `confirm-1` (60 eps) clean under Atlas roles + Raindrop + isolation.

**Isolation is enforced by Atlas:** users `munch-learner` (readWrite@munchhausen + custom role `munch_world_views`:
find/listCollections/createCollection/dropCollection on `world`), `munch-executor` (read@world), `munch-evaluator`
(read@truth, read@world); `MONGODB_URI` = admin, offline steps only (`setup`, `build-world`). `munchhausen
verify-roles` → `isolation: roles`, 0/18 mismatches. Personas renamed `anna`, `benny`, `claire` (P1 =
`P1_claire_rounding`).

Binding decisions 14–22 (don't relitigate):
14. **Held-out fold:** a shape spanning ≥ BAR_MIN_TEMPLATES + HOLDOUT_TEMPLATES templates withholds its
    least-observed template from the nominator; that template's episodes stay in the backtest population and the
    sample reserves `BACKTEST_HOLDOUT_SHARE` of slots for them. `Draft.holdout_templates/holdout_observation_ids`.
15. **Hold to accrue (user-approved):** a draft with no fold whose backtest clears all but the held-out fix HOLDs
    (`awaiting_heldout_template`, backtest verdict `awaiting_heldout`); observations stay open; it re-nominates
    only when a NEW template arrives. Wrong/poisoned drafts still refuse.
16. **Floor bar 2** (`BAR_MIN_TEMPLATES_FLOOR`), declared departure from SPEC § 7.3 (user-approved).
17. **A hook must reach every source question** (`domain.latches.hook_reaches`); self-blocking `not_this` refused.
18. **Leak checks match figures by value**, ignore digits inside ISO dates and |x| < `LEAK_MIN_ABS`.
19. **Drift window** applies only when the rank-1 neighbour is contested and about the shape.
20. **Accuracy excludes only harness failures** (`error` starts `episode_failed`); execution errors are misses.
21. **naive/self_ref lesson calls run concurrently** (`DIRECT_CONCURRENCY`), applied in observation order.
22. **Raindrop** is a write-only `Trace` (`TRACE_IMPL=jsonl,raindrop` tee); never read on the learning path.

### 00b. Status at 15:25 (pre-compaction handoff for the orchestrator)

**Run A** — frozen, ungated, governed DONE (each 20 rounds, 0 failed, 0 V holes). naive+self_ref (one process,
`munch-run-a2`, log `var/runs/run-a.direct.log`) still running at handoff. `RAINDROP` quota ran out mid-run: sends
dropped silently, runs unaffected (write-only trace); local `var/runs/run-a/events.jsonl` is complete.
governed story (all from records):
- Q1 `st∈{2,7}` @60 (backtest 6 fixed/4 held-out/0 broken); Q6 eight-symbol set @90 (5/5/0); Q5 ×0.995 @240 (5/4/0).
- D1 @300 → dispositive fire @307 (genuine undercounts 137 vs 191, 614 vs 856) → wrong successors REFUSED @360
  (broke 4), @390 (broke 2), @420 (no held-out) → successor `st∈{2,4,7}` admitted @450 (5/2/0), predecessor
  superseded. Drift-to-supersede latency 150.
- Floor `rs 3 excluded` admitted @540 (6/5/0), tool_access rewired → governed floor beat landed.
- Q1 accuracy by window (0–149, 150–299, 300–374, 375–449, 450–524, 525–599): governed 13/30, 32/32, 0/14, 0/14,
  10/19, 12/18; ungated 12/30, 28/32, 0/14, 8/14, 17/19, 15/18; frozen/self_ref/naive 0 throughout.
- Ad-hoc paired (not pre-registered), quirk-bearing, minus frozen, idx 150–299: governed +0.60 [0.52,0.68] n=95,
  ungated +0.56, naive +0.20, self_ref 0.00. Official readings come from `report`.
**Weakness found (report it, do NOT fix mid-run):** revisit guard fires on small consistent residuals that are not
drift: ungated fired @141 (pre-D1) on its correct Q1 decision from claire-rounded residuals and superseded it;
ungated @535 and governed @467 (open) fired on off-by-one/one-rounding-step residuals. Post-event fix: tighten
attribution for persona/rounding phrasing and boundary residuals. Add to LESSONS + deck residue slide.

**Run B** (adversarial authority) RUNNING since 15:17: `RUN_ID=run-b`, snapshot `60086e4` (`munch-run-b`),
`AUTHORITY_POISON_RATE=0.20`, `CONF_DIR=<munch-run-b>/engine/conf/run-b` (forecasts F1–F7 registered; F2 = governed
admits 0 N1-derived, naive and ungated ≥1; F7 = governed − ungated on controls after round 10), arms frozen, naive,
ungated, governed, `TRACE_IMPL=jsonl`, other knobs as Run A learning arms. Log `var/runs/run-b.log`. ETA ~15:55–16:05.
Launcher script: scratchpad `launch_run_b.sh` (already fired).

**Deck:** https://claude.ai/artifact/9spap78fYyEfE9GfuZ6jo5 (Slides type, private; user must share). 18 slides,
rehearsal placeholders with badges on slides 7, 8, 9, 11. To fill: 7 `[curve]` → Q1 step chart above (governed,
ungated, frozen, D1 marked, fire @307, successor @450); 10 injection screenshot + `[fixed/broken]`; 11 governed
floor @540; 12 `why active_customer` screenshot; 13 F1–F7 readings (show REGISTERED forecast beside reading — slide
currently says "F6 expected below": replace with the registered claim); 17 test/commit counts (442 tests);
18 repo link. Add Run B slide (poison 0.20) if it reads. Revise the deck by its url (read deck.json first).

**Git:** local `m0-scaffold` HEAD ≥ `60086e4`. `origin/m0-scaffold` DELETED at user's request; origin has only `main`.
Do not push anything until the history rewrite (step 6 below). User asked to hold private info.

**Post-run checklist (in order):**
1. When every arm ends: re-close `rounds` for `run-a` with HEAD code (arms wrote round records with different
   snapshots of `round_pipeline`; `$merge` is idempotent) — loop `evidence.close_round` over each arm's rounds.
2. `PLANTED_MAP_CONCURRENCY=16 uv run munchhausen planted-map run-a` (Opus judge; resumes; ~$10); same for run-b
   after it ends.
3. `uv run munchhausen report run-a --against rehearsal-1` → `var/reports/run-a/`; read every forecast beside
   its reading; state disagreements as they stand. Then `report run-b --against run-a`.
4. Demo beats: viewer `munchhausen viewer --run run-a` (injection beat on governed, `why active_customer`,
   floor beat if governed admitted a floor; else ungated's).
5. Export evidence into a tracked `docs/evidence/` (report.md/html, readings.json, manifest.json).
6. **Before any further push:** rewrite history with `git filter-repo` — replace absolute local paths and the
   old key-format note in every commit, map author email to the GitHub noreply address — then force-push.
   `origin/m0-scaffold` was pushed 14:55 with those strings in older commits. Merge to `main` only on the
   user's go-ahead.
7. Update README (claim language, n/intervals, what was built on the day) and LESSONS if new patterns appear.

---

## 0. Orchestrated build (12:45–13:30): state, binding decisions, open items

Six surface agents (S1 world, S2 forward + runtime sandbox, S3 shaping, S4 adjudication, S5 telemetry/evidence,
S6 viewer/injection), each in its own worktree with file ownership (`ORCHESTRATION.md`), then one adversarial
review per surface and one fix round, plus a pilot-gate agent. Everything is merged on `m0-scaffold` (= branch
`integration`, `0158818`). 359 tests pass, ruff clean. Error patterns: `corpus/LESSONS.md` (branch `lessons`).

**State.** M1 world, M2 forward pass, M3 backward pass, M4 viewer + evidence report are built. Atlas:
`setup` re-applied after the schema additions; `world` rebuilt (pack hash in `runs`); V set sealed and
stratified (control 14, Q1 9, P1 5, Q3 4, Q5 4, Q6 4). Quirks built: Q1 (+D1), Q3, Q5, Q6, P1, N1. Not built:
Q2, Q4/D2, Q7, Q8 (D2 is therefore cut). Pilot gate (SPEC § 12) reads in range on `claude-haiku-5-5`: controls
17/17, quirk-bearing 0/23 (n=40); n=120: 37/37, 2/83.

**Keys.** `.env` names are aliased in `config.py`: `anthropic_munch_key` (org API key) + `anthropic_workspace_key`
(→ `ANTHROPIC_WORKSPACE_ID` header) = auth mode `api_key_workspace`, every model served; `claude_oauth_key` is
the fallback (serves only haiku-4-5); `voyage_key`, `typesafe_key`. Per-role Atlas users still absent →
`isolation: convention`.

Binding decisions made in this build (don't relitigate):
1. **Proposer = `claude-haiku-5-5`** (SPEC § 12 hedge: haiku-4-5 failed controls at 0.65 after mechanical
   fixes). Haiku 5.5 refuses `temperature` (400), so `PROPOSER_TEMPERATURE` defaults to unset; replay noise is
   handled by rule 3. SPEC § 3/§ 16 still say haiku-4-5; the config holds.
2. **Rounds are half-open `[lo, hi)`** everywhere (runner, episodic pass, round record, backward hook).
3. **Admission (SPEC § 7.4 amended):** a fix counts only when the with-draft replay recorded the draft
   `applied`; admit needs `fixed ≥ min ∧ fixed_heldout ≥ min ∧ broken ≤ max ∧ fixed − broken ≥ BACKTEST_MIN_FIXED`.
   Fewer than `BACKTEST_MIN_N` scored pairs → verdict `insufficient`, L4 HOLD (never a refuse).
4. **Backtest population** excludes the warrant's and context's sources, `Draft.nominator_seen_episode_ids`, and
   any episode whose question id or text equals one of theirs; a non-supersede draft reads the last
   `BACKTEST_RECENT` episodes; misses whose terms meet the hook are sampled first.
5. **Nominator sees neighbour residuals as `{signature_match, attributable, direction}` only**;
   `NOMINATOR_RESIDUAL_WINDOW` 4.
6. **Direction read is windowed**: from a contested neighbour's earliest open dispositive fire, else the last
   `DIRECTION_WINDOW` (40) matched episodes. Coherence guard also keeps one-persona/one-direction and
   one-collection/one-direction clusters (P1 and Q3 shapes survive).
7. **Retirement counts dispositive fires only**; corroborating fires never settle anything (§ 6.3).
8. **Observation dispositions belong to the episodic pass** (shaped → spent; hold → open); the adjudicator sets
   draft status only.
9. **Index namespaces:** stream `idx ≥ 0`; V `idx = -(1 + k·V_SIZE + j)` with `v_at`; injection
   `idx ≤ INJECT_IDX_BASE` (−1,000,000), `stream="injection"`, `Draft.source="injection"`. Injected
   observations are spent on every exit and excluded from the organic pass (`open_for_pass(exclude_via=…)`);
   owner-admit refuses an all-injection draft.
10. **Runtime sandbox:** every world read goes through `GuardedReader` (`domain/pipeline_guard.py`); floor
    matches are guard-checked at L0 and before `create_view`; `$lookup/$graphLookup/$unionWith` targets are
    rewritten through `view_map`; gold reads `world_evaluation()` (unguarded, evaluator side only).
11. **Terms are run-scoped** (`Term.runs[run] = admitted_at_idx`); hook terms are case/space-normalized.
    Amended (arm isolation): seeded terms stay run-wide; learned terms (`source: nominator`) live in
    `Term.arm_runs[run:arm]` and reach only that arm (`domain.registers.term_visible`; `extract`/`all` take
    `arm`). Nothing writes learned terms yet (SPEC § 22.4 growth is unbuilt), so the leak was latent.
12. **Naive merge = converge successor** (tombstone per merge); readings exclude `converged`/`retired` from drift
    resolution; F4 needs a real supersession with a successor.
13. **Evidence:** proxy readings read `unread (proxy)`; paired readings drop errored or mismatched pairs;
    resumes append `runs.resumes[]` with every moved knob/sha/prompt/port/pack; tokens come from spend (null,
    never 0); event catalog = the names surfaces emit (`corpus/EVIDENCE.md`).

Open / next:
- Smoke run `smoke-1` (all arms, 60 episodes) → then **Run A** (`RUN_ID=run-a`, `RUN_LENGTH` 900, D1 at 300).
- Lens panel `jev` hedges heavily (p≈0.4–0.5): keep `LENS_MODE=record`.
- Injection spend for observer/nominator/replay calls is still tagged with their own stages.
- Cost per governed draft ≈ 16 proposer replays + 8 reranks + 15 Jev calls; levers `BACKTEST_N`, `LENS_PHRASINGS`.
- `lensfit` (§ 9) and Raindrop remain cut.

---

## 1. Where things stand

| Milestone (SPEC § 13) | Slot | State |
|---|---|---|
| M0 scaffold + schema lock | 10:30–11:00 | **done** (late, ~11:50). Commit `52cde25` on branch `m0-scaffold` |
| M0 review fixes | — | **done** (12:21), commit `002a66d` on `m0-scaffold`, after `4764f2f`: § 3a |
| M1 world | 11:00–12:00 | not started — **next** |
| M2 forward pass | 12:00–12:45 | forward pass orchestration written (`loop/episode.py`); collaborators stubbed |
| M3 backward pass | 12:45–14:00 | layer/curator/lifecycle skeletons; L0, L1, curators, admission plan done |
| M4–M6 | 14:00– | stubs only |

Schedule is ~80 min behind (M1 not started at 12:21). Cut order (SPEC § 13, amended): Part II post-event rows → § 9 → `self_ref` →
context policy → D2 → Raindrop. If the day runs short, build the minimum configuration (§ 5 below).

**Verification:** `uv run pytest` → 85 passed, 1 skipped (numpy similarity loader, M2).
`uv run ruff check engine viewer` → clean.
**Atlas validators:** re-applied by `munchhausen setup` after `002a66d` (`backtests`, `episodes` fields present).

## 2. Atlas state (live)

- `MONGODB_URI` is set in `.env` (user added it). Per-role URIs (`MONGODB_URI_LEARNER/EVALUATOR/EXECUTOR`)
  are **not** set; every role falls back to `MONGODB_URI`, so gold isolation holds by convention + the
  import test only, not by database roles.
- `munchhausen ping`: server **8.0.34**; transactions ✓, change streams ✓, `$rankFusion` ✓, `$scoreFusion` ✗
  (needs 8.2; post-event only, no impact). `autoEmbed` and Agent Engine: unverified.
- `munchhausen setup` ran (idempotent; re-run is a no-op). Database `munchhausen` has all 16 stores,
  validators (`warn`), B-tree/multikey/TTL indexes, `spend` as time series, pre/post images on
  `decisions` + `tool_access`.
- Search indexes created: `decisions_vec`, `observations_vec`, `terms_search` (were `PENDING` at creation;
  confirm `READY`). Skipped by our cap knob, not refused by Atlas: `decisions_search`, `episodes_search`.
  If the sandbox tier is above M0/Flex, raise `SEARCH_INDEX_CAP` and re-run `setup`.
- **Sample data is NOT loaded.** Only `admin/config/local` exist (~1 MB). Blocks M1.
  User action: Atlas → Clusters → `…` → Load Sample Dataset; then drop every sample DB except
  `sample_analytics` (SPEC § 3 storage premise, 80% threshold).
- An unrelated `.env` key is not a driver URI and is not read by config. Don't print it.

## 3. Binding decisions (made in M0; don't relitigate)

Architecture
1. **uv workspace** at repo root: `engine/` (package `munchhausen`) and `viewer/` (package
   `munchhausen_viewer`, depends on the engine). Python pinned `>=3.12,<3.13`.
2. **Layering, test-enforced** (`engine/tests/test_architecture.py`):
   `domain` (pure) ← `ports` (Protocols) ← `agent/loop/learn/metrics` (application) ← `store/impl`
   (infrastructure) ← `bootstrap/cli` (composition root). `world/` + `truth/` are the evaluation side.
   - `pymongo`/`bson` only under `store/`; `anthropic/voyageai/typesafe/raindrop` only under `impl/`.
   - `learn/ agent/ loop/` never import `truth` or `world`. `truth` importable only from `metrics/ world/ truth/`.
   - Application packages never import `store/ impl/ bootstrap`.
   - Only `store/decisions.py` writes to the `decisions` collection.
3. **Uniform construction:** every implementation has `create(name, settings, store)`; the composition
   root does `registry.resolve(port, name).create(...)`. New implementation = registry entry + class.
   No branching on implementation/dataset/vendor names anywhere else.
4. **World composes Truth.** Registry port `world: {pack: PackWorld}`; adapters are their own registry port
   (`adapter: {sample_analytics: …}`), chosen by the pack's `adapter` field. `PackWorld.create` builds pack,
   question bank, `PackGold`, `Authority`, and exposes `world.truth` for the evaluation side only. The
   `truth` DB handle is not on the Store port; `bootstrap.Harness.world()` gets it via
   `store.atlas.open_truth` (evaluator role).
5. **Transactions stay inside the store.** Atomic changes are pure domain plans
   (`domain/admission.py: plan_admission → Admission`) committed by one repository call
   (`DecisionRepository.admit/supersede/converge`). View DDL is not transactional: `learn/lifecycle.py`
   creates the successor's view before commit and drops predecessors' views after.
6. **Validators derive from domain models** (`store/schemas.py` converts pydantic JSON Schema → Mongo
   `$jsonSchema`: `$ref` inlined, `type`→`bsonType`, date-time→`date`). One source of truth. Schemas are
   additive-only from now on.
7. **Deterministic ids** (`domain/ids.py`): episode `{run}:{arm}:e{idx}`, decision `D-<hash(draft_id)>`,
   latch `T-<decision>-<k>`, etc. Every `put` is an idempotent upsert → resume-safe.
8. **Persisted records** are pydantic `Record` (frozen, `extra="ignore"`, `_id` alias). BSON via
   `store/codec.to_doc` (python-mode dump; sets → sorted lists).

Spec resolutions (spec was ambiguous or self-contradictory)
9. **Observation schema follows § 23.1**, not § 10.1: field `disposition` (not `status`), `via`, `class`
   (python attr `cls`), vectors under `emb.<embedder_key>`. Vector index filters use `disposition`.
10. **Embeddings stored as `emb.<emb_key(embedder_id)>`** where `emb_key` replaces `-`/`.` with `_`
    (`voyage-4` → `emb.voyage_4`). Applies to decisions and observations (E10).
11. **Latch paths:** `latches` is an array of typed subdocuments, so index/query paths are
    `latches.fires_when.terms`, `latches.fires_when.collections`, and lineage `latches.edges`
    (the spec's `latches.wiring.edges` is conceptual). `$graphLookup` connects on `latches.edges`.
12. **Hook match semantics** (`domain/latches.HookLatch.matches`): persona, if set on the hook, is a
    required scope; otherwise match when terms ∩ or collections ∩; any `not_this` row whose keys are all
    present blocks. Atlas does an index-backed `$in` prefilter; the domain function is the one definition.
13. **Gold never reaches the forward pass.** `World.judge(question, answer, idx, with_authority)` returns
    `Judgement{correct, figure?, phrasing?}`; figure/phrasing only for arms with an authority.
14. **`self_ref` leak closed:** `episodes.correct` is gold-derived. `EVALUATION_ONLY_FIELDS`
    (`correct, world_version, figure, phrasing, confirmed_figure`) are projected away by
    `EpisodeRepository.for_learner(..., with_authority=False)`. Learner code for no-authority arms must use it.
15. **Retry is scored against the authority's figure, never gold** → `retry_correct` is learner-legal.
16. **Authority lives in `world/authority.py`** (reads gold), not `agent/`. Scoring is pure:
    `domain/scoring.py: matches()`, `ratio_delta()`.
17. **Hidden tags = quirk ids only.** Template id and persona stay legible on `Question` (hooks and the bar
    need them). Quirk ids live in `world/questions.QuestionBank` and nowhere else.
18. **Round barrier** (documented in `loop/runner.py`): round r's episodes all land before its episodic
    pass; round r+1 starts after. Consultation at idx i then depends on (seed, i), not worker timing.
19. **`hitl` curator** = governed layers with `owner_required=True`: an L4 admit becomes `hold` awaiting L5.
    Under a governed curator, a non-dispositive layer returning `admit` raises.
20. **Proposer wire format:** `impl/models_anthropic.ProposalWire` carries the pipeline as
    `pipeline_json: str` (arbitrary-key objects don't fit strict structured output); mapped to domain
    `Proposal`. Wire schemas live in `impl/`, never in `domain/`.

## 3a. M0 review — what changed (binding; don't relitigate)

Review item numbers are the review's § D table. All code changes are covered by tests in
`engine/tests/test_learning_design.py`, `test_domain.py` and `test_config.py`.

| # | Change | Where |
|---|---|---|
| 3 (B1) | **Paired backtest under the current store.** `BacktestSample` gained `baseline_correct` (replay without the draft) and `context` (admitted ids consulted). `fixed` = with ∧ ¬without; `broken` = without ∧ ¬with; `original_correct` is only the sampling stratum. `Backtester` takes the arm's `Consulter` (not `DecisionRepository`) so replays run in the current admitted store, minus the predecessor. Cost 2 × `BACKTEST_N` proposer calls per draft. | `domain/backtest.py`, `learn/backtest.py` |
| 3 | `Episode.collections` (additive) so a replay can rebuild its `Question`. | `domain/episode.py`, `loop/episode.py` |
| 4 (A2) | **`ungated` arm**: curator `ungated` = [L0, DirectAdmit]; `write_path: episodic`, `consultation: hooks`, same as `governed` but the curator. `governed − ungated` is the effect of the gate (F6). Lint bans the arm name in records. | `learn/curators.py`, `ports/registry.py`, `conf/arms.yaml`, `lint_language.py` |
| 5 (A2) | **Naive's lesson defined.** `domain/lesson.py`: `Lesson{title, kind ∈ taxonomic/procedural/preference, payload}`; `lesson_entry` fills the entry contract mechanically (one chosen option, hook copied from the episode's terms + collection for residual attribution only, no revisit latch, residue says ungoverned). `Models.lesson(episode, observation)` writes it from the episode, the authority's figure + phrasing and the retry pipeline; model `NAIVE_LESSON_MODEL` = Sonnet (same as the nominator, so the payload's author is not a confound; drop to Haiku if spend bites). `SelfGrade.lesson` is now a `Lesson`. `naive`/`self_ref` curators take `LessonShape()` as L0 (the entry-contract L0 would refuse every lesson). Orchestration stub: `learn/direct.py: DirectWriter`. | `domain/lesson.py`, `ports/models.py`, `learn/layers.py`, `learn/direct.py`, `impl/models_anthropic.py` |
| 6 (B5) | **L3 records by default.** `L3Lenses` is implemented: panel → current weights → score; `LENS_MODE=record` always passes (every draft reaches L4 and labels lensfit); `gate` refuses below `LENS_THRESHOLD` except a deterministic `LENS_EXPLORE_EPS` share. Needs `weights: LensRepository` and `seed`. | `learn/layers.py`, `config.py` |
| 7 (B2) | **Revisit guard** counts residuals that are attributable ∧ signature-matched ∧ agree in direction (sign of answer − figure); largest agreeing group must reach `min_residuals`. Per-episode `SIGNATURE_CHECKS` still don't discriminate (documented); direction does. | `loop/residuals.py` |
| 8 (B4) | **Carry every open observation**: `CARRY_ROUNDS` default `None` (= all). | `config.py`, `learn/episodic.py` |
| 9 (B6) | **Nominator not blind; inputs bounded.** `NominatorInput.__post_init__` refuses episodes/observations outside the shape; new `neighbour_residuals`. `Nominator` gains `decisions`, `representation`, `similarity`, `neighbour_k` and fills neighbours before drafting; L2 reuses them via `CurationContext.neighbours`. | `ports/models.py`, `learn/nominate.py` |
| 10 (B3) | **Direction read (E4) is part of the bar.** `DirectionRead` (domain), `EpisodeRepository.direction_read` (one `$facet`; authority arms only, reads `correct`), `Bar.direction_clears` with `BAR_MIN_GAP` 0.10 over ≥ `BAR_MIN_MATCHED` 10, `presentation_filter(shape)` (shared terms, else templates). | `domain/draft.py`, `ports/store.py`, `store/repositories.py`, `learn/episodic.py` |
| 2 (B2) | **One quirk per question.** `QuestionBank` refuses multi-quirk templates; `hidden_quirks(template, persona, persona_quirks)` refuses a preference persona on a quirk template (Dana on controls only). Authority's phrasing therefore names the question's one quirk. Pack design rule + gold isolation test are M1 work (see § 5). | `world/questions.py`, `world/authority.py`, `packs/analytics-v1.yaml` |
| 11 (B7) | **Readings resolve.** `V_EVERY` 150 + `V_OFFSET` 75 (reads at 75, 225, …; never on D1/D2). `metrics/paired.py`: paired bootstrap difference (`BOOTSTRAP_N` 2000, `CI_LEVEL` 0.90) and three-way verdict vs a margin (above: lo > +m; below: hi < −m; else within). `forecasts.yaml` entries are now `{claim, reading, margin, unit}`; F6 added (governed − ungated). Run A is labelled a pilot: knobs that move before Run B force re-registered forecasts and a knob diff in the report. | `config.py`, `loop/runner.py`, `metrics/paired.py`, `conf/forecasts.yaml` |
| 12 (A1) | **Claim narrowed**: "admits only what the authority's figures reproduce out of sample"; residue named (a consistently wrong authority passes); F2 is a sanity check; lensfit is not pitched as "learns which questions to ask". | SPEC § 0/1/7.4/9/14, README, CLAUDE.md, package docstring |
| 13 (A3) | `self_ref` moved up the cut order. **`FROZEN_STREAM` default true**: `frozen` is the paired no-learning reference. The arm-name branch in `Settings.arms()` is gone (`stream_knob: frozen_stream` in `arms.yaml`). | `config.py`, `conf/arms.yaml`, SPEC § 13 |
| 1 (C) | Pilot gate moved to the front of M1 (§ 5); minimum configuration recorded (§ 5, SPEC § 13). | plan only |

Departures from the review, decided here:
- **F1 is not read from `frozen` alone.** `frozen` never holds a Q1 decision, so its Q1 accuracy may not fall at
  D1 (it is wrong before and after). F1 now reads the calibration gap of any arm holding a pre-D1 Q1
  decision (in practice `naive`/`ungated` until replaced, `governed` until superseded), with `frozen` as the
  reference. Demo beat 1 (SPEC § 18) was reworded to match.
- **Minimum configuration's "L2 routes every draft as new"** would make D1 supersession impossible. The plan
  keeps one exception: a supersede the nominator declares against a *contested* neighbour (open dispositive
  fire). Not yet coded; it is the L2 to build if the full L2 is cut.
- SPEC § 14 gained departure 5 (no slot-factored backward pass, review B8) as a named post-event avenue.

Still open from the review (post-event, recorded in SPEC): multi-quirk templates with a residual-reduction
backtest read and an authority naming a quirk the answer actually missed; slot-factored routing of evidence.

## 4. Known open issues (need a decision or user action)

- **Floor views vs roles (SPEC § 20.2 conflict):** learner is specced `read@world`, but floor views must be
  created in `world`. When per-role users are made, the learner (or a dedicated role) needs
  createCollection/dropCollection on `world`. Currently moot (single URI).
- **Provenance order (SPEC § 15):** the "import prior schemas" commit was supposed to precede every engine
  commit. The user chose to commit the scaffold first; `prior/` is an empty placeholder. If prior schemas
  are imported, disclose the actual order in the README *Provenance* section rather than rewriting history.
- **Branch:** work is on `m0-scaffold`, not merged to `main`, not pushed.
- `SEARCH_INDEX_CAP=3` is our default, not a measured tier limit. Confirm the sandbox tier.
- `proposer_model = claude-haiku-4-5` is unverified against the API (SPEC § 3 verify). Haiku 4.5 rejects
  `output_config.effort` — `_parse` only sends effort when passed (nominator only).
- TELLS regexes in `lint_language.py` are a first cut (e.g. `\b(I|we|our|us)\b` is case-insensitive).
- `loop/residuals.SIGNATURE_CHECKS` are first-cut per-episode predicates that don't discriminate (all but
  `rounding` reduce to "answer differs"; `rounding`'s `< 1000` is a pack-dependent literal). The guard's
  direction read carries the discrimination; `date_offset` needs question params (M2).
- **Spend:** paired backtest doubles replay calls (16 Haiku per draft); `naive` lesson writer is one Sonnet
  call per reducible miss. Watch `spend` in the pilot; `NAIVE_LESSON_MODEL` and `BACKTEST_N` are the levers.
- The pack's quirk placement under the one-quirk rule is unsolved for Q1/Q2/Q8 (all act on customers). SPEC
  § 4.2 gives the two routes: place each population where the others' definitions already exclude it, or
  scope each quirk's templates away from the others (Q2 via account totals). Decide at M1 step 2.

## 5. Next — M1 (world), in order — pilot gate first

Done when: pilot gate (§ 12) reads in range; adapter, `analytics-v1` pack, transform registry, gold,
questions, scorer, authority; gold tests and the gold isolation test pass.

0. User loads sample data (§ 2 above). Then **kickoff checks (§ 4.2 verify)**: types of `price`/`total`
   (strings), ticker set in `transactions`, distribution of `accounts.limit`. Fix Q6 members and Q7 `T`.
   Validators are current (§ 1); re-run `munchhausen setup` after any schema change.
1. **Pilot slice:** `AnthropicModels.propose` (M2 item, pulled forward), the adapter's `build` for
   customers/accounts/transactions, ~4 control templates + Q1's materialize/gold transforms and templates,
   `QuestionBank.stream`, `PackGold.gold`. Run the **pilot gate**: frozen proposer ≤ 35% on Q1, ≥ 70% on
   controls over 40 questions. Failing high → rename mnemonic fields, then lower the proposer; failing low on
   controls → raise the proposer or cut templates. Nothing else matters until this reads in range.
2. `engine/packs/analytics-v1.yaml`: fill the rest — minimum set first (Q3 floor + `deleted_at` decoy, Q5,
   P1, N1), then Q2/Q4/Q6/Q7/Q8 as time allows. **One quirk per template** (`QuestionBank` enforces it);
   P1 on control templates only (pass `persona_quirks={"dana": "P1_dana_rounding"}`); decide the Q1/Q2/Q8
   placement (§ 4). ≥ 4 templates, ≥ 3 phrasings each (`Pack.validate_coverage()`).
3. `world/transforms.py`: register `@materialize` and `@gold` transforms; `stable_bucket(key, seed)` for hash
   assignment. **Gold test per transform on a hand-computed fixture, plus the gold isolation test** (each
   quirk template's gold unchanged by every other quirk's gold transform), before any arm runs.
4. `world/questions.py`: ~12 `Template`s, `stream(seed)` (65/35 via `QUIRK_SHARE`), `v_set(seed, size)`
   disjoint from the stream; populate `_hidden` via `hidden_quirks`.
5. `truth/gold.py: PackGold.gold` at `world_version` (`v0`, `v0+D1`, `v0+D1+D2`).
6. `world/authority.py`: `_abs_tol_for` (Dana rounding → 0.5), `_figure` (N1 poison under `(seed, idx)`),
   `_phrasing` (the question's one quirk; `AUTHORITY_LEVEL`).
7. `PackWorld.build` → adapter writes `world`; CLI command `build-world`. `PackWorld.create` must pass
   `persona_quirks` to `QuestionBank`.

**Minimum configuration if the day runs short** (protects the one complete story: Q1 learned → applied on
an unseen template → D1 fires → superseded with tombstone → recovery on the paired curve, plus the floor
beat): quirks Q1 (D1), Q3, Q5, P1, N1; arms `frozen` (stream on), `naive`, `ungated`, `governed`; L2 routes
new except nominator-declared supersede of a contested neighbour (§ 3a); L3 records; lensfit cut.

Then M2: `AtlasTerms.extract` (+ in-process longest-match fallback), `consulter_for`, `ArmRunner.run`
(cursor claim → lease → ForwardPass → barrier; V at `v_offset + k·v_every`), term vocabulary seeding
(§ 22.4: schema + first `VOCAB_WARMUP` questions, never from the pack — add the test).

Then M3, in the order that protects the story: observer → episodic pass (bar + direction read) → nominator
(neighbours first) → L0/L1/L2/L3(record)/L4 with the paired `Backtester` → `ungated` → `DirectWriter` +
`Models.lesson` for `naive` → `self_ref` last.

## 6. Map of stubs (all raise `NotImplementedError("M<n>: …")`)

`grep -rn NotImplementedError engine/munchhausen` lists them. Highlights: `world/questions.py`,
`world/authority.py`, `truth/gold.py` (M1); `impl/models_anthropic.py` propose, `agent/consultation.py`
semantic + `consulter_for`, `store/repositories.AtlasTerms.extract`, `loop/runner.py`,
`impl/similarity.NumpySimilarity.create` (M2); `learn/observe|episodic|nominate|backtest|direct`, layers
L2 and L4 (L3 is implemented), `impl/lens_panel.JevLensPanel.score`, `AnthropicModels.lesson` (M3);
`metrics/*` except `metrics/paired.py` (M3–M4); `learn/lensfit.py` (M5).

## 7. API notes verified against installed packages

- pymongo 4.18 async: `client.start_session()` is a sync call returning an async context manager;
  `await session.with_transaction(callback)`; `aggregate`, `watch`, `list_search_indexes`,
  `create_search_index` are coroutines (await, then iterate/`to_list()`); `find()` is not.
- anthropic 1.13: `await client.messages.parse(model=…, max_tokens=…, system=…, messages=…,
  output_format=PydanticModel, output_config={"effort": …})` → `.parsed_output`. Check
  `stop_reason == "refusal"`. No forced `tool_choice` on 5.5 models.
- voyageai 0.5: `AsyncClient.embed(texts, model, input_type, output_dimension)`,
  `AsyncClient.rerank(query, documents, model, top_k)` → `.results[i].index/.relevance_score`.
