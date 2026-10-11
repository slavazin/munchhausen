# Carry-forward — session state for the next implementer

Written 2026-10-11 11:53 PDT, after M0. Read this, then `CLAUDE.md`, then the SPEC sections named under
**Next**. `SPEC.md` is the design and holds wherever this file is silent. Where this file records a
decision that departs from or resolves the spec, this file holds — the spec is not edited to match.

---

## 1. Where things stand

| Milestone (SPEC § 13) | Slot | State |
|---|---|---|
| M0 scaffold + schema lock | 10:30–11:00 | **done** (late, ~11:50). Commit `52cde25` on branch `m0-scaffold` |
| M1 world | 11:00–12:00 | not started — **next** |
| M2 forward pass | 12:00–12:45 | forward pass orchestration written (`loop/episode.py`); collaborators stubbed |
| M3 backward pass | 12:45–14:00 | layer/curator/lifecycle skeletons; L0, L1, curators, admission plan done |
| M4–M6 | 14:00– | stubs only |

Schedule is ~50 min behind. Cut order (SPEC § 13): Part II post-event rows → § 9 → context policy → D2 →
`self_ref` → Raindrop.

**Verification:** `uv run pytest` → 72 passed, 1 skipped (numpy similarity loader, M2).
`uv run ruff check engine viewer` → clean.

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
- The original `.env` key `mongodb_mun_key` is not a driver URI. Purpose unknown
  (possibly an Atlas API key). Not read by config. Don't print it.

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
- `loop/residuals.SIGNATURE_CHECKS` are first-cut per-episode predicates; `date_offset` needs question
  params to be meaningful (M2).

## 5. Next — M1 (world), in order

Done when: adapter, `analytics-v1` pack, transform registry, gold, questions, scorer, authority; gold tests
pass; pilot gate (§ 12) reads in range.

0. User loads sample data (§ 2 above). Then **kickoff checks (§ 4.2 verify)**: types of `price`/`total`
   (strings), ticker set in `transactions`, distribution of `accounts.limit`. Fix Q6 members and Q7 `T`.
1. `engine/packs/analytics-v1.yaml`: fill `quirks:` Q1–Q8, P1, N1 and `poison_bank:` per § 4.2 (≥ 4
   templates, ≥ 3 phrasings each; `Pack.validate_coverage()` checks this). Opaque field names, decoys
   (`deleted_at` decoy for Q3).
2. `world/transforms.py`: register `@materialize` and `@gold` transforms; use `stable_bucket(key, seed)`
   for hash assignment. **Gold test per transform on a hand-computed fixture before any arm runs.**
3. `world/questions.py`: ~12 `Template`s, `QuestionBank.stream(seed)` (65/35 quirk/control via
   `QUIRK_SHARE`), `v_set(seed, size)` disjoint from the stream; populate `_hidden`.
4. `truth/gold.py: PackGold.gold` — compose gold transforms for the question's hidden quirks at
   `world_version` (`PackWorld.world_version`: `v0`, `v0+D1`, `v0+D1+D2`).
5. `world/authority.py`: `_abs_tol_for` (Dana rounding → 0.5), `_figure` (N1 poison under `(seed, idx)`),
   `_phrasing` (one missed quirk at random; `AUTHORITY_LEVEL`).
6. `PackWorld.build` → `SampleAnalyticsAdapter.build` writes `world`; add a CLI command `build-world`.
7. Pilot gate: frozen proposer ≤ 35% on quirk-bearing, ≥ 70% on controls over 40 stream questions — this
   needs `AnthropicModels.propose` (M2 item, pull it forward).

Then M2: `AnthropicModels.propose`, `AtlasTerms.extract` (+ in-process longest-match fallback),
`consulter_for`, `ArmRunner.run` (cursor claim → lease → ForwardPass → barrier), term vocabulary seeding
(§ 22.4: schema + first `VOCAB_WARMUP` questions, never from the pack — add the test).

## 6. Map of stubs (all raise `NotImplementedError("M<n>: …")`)

`grep -rn NotImplementedError engine/munchhausen` lists them. Highlights: `world/questions.py`,
`world/authority.py`, `truth/gold.py` (M1); `impl/models_anthropic.py` propose, `agent/consultation.py`
semantic + `consulter_for`, `store/repositories.AtlasTerms.extract`, `loop/runner.py`,
`impl/similarity.NumpySimilarity.create` (M2); `learn/observe|episodic|nominate|backtest`, layers L2–L4,
`impl/lens_panel.JevLensPanel.score` (M3); `metrics/*` (M3–M4); `learn/lensfit.py` (M5).

## 7. API notes verified against installed packages

- pymongo 4.18 async: `client.start_session()` is a sync call returning an async context manager;
  `await session.with_transaction(callback)`; `aggregate`, `watch`, `list_search_indexes`,
  `create_search_index` are coroutines (await, then iterate/`to_list()`); `find()` is not.
- anthropic 1.13: `await client.messages.parse(model=…, max_tokens=…, system=…, messages=…,
  output_format=PydanticModel, output_config={"effort": …})` → `.parsed_output`. Check
  `stop_reason == "refusal"`. No forced `tool_choice` on 5.5 models.
- voyageai 0.5: `AsyncClient.embed(texts, model, input_type, output_dimension)`,
  `AsyncClient.rerank(query, documents, model, top_k)` → `.results[i].index/.relevance_score`.
