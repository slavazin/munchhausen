# EVIDENCE — what the harness records, and how a claim is re-derived

Owner: telemetry surface (S5). Every number on a slide is re-derivable from Atlas by a named query, with unit,
population, n, interval where one applies, and the pre-registered forecast beside it (SPEC § 11, LANGUAGE § 7).
Names below are **one-way doors**: readers depend on them. Add a field; never rename or drop one.

## 1. `runs` — one record per run id, written before the first episode

`evidence.start_run(h)` writes it; `munchhausen runs` lists them. The run id is the unit of pre-registration.

| field | meaning |
|---|---|
| `_id` | `RUN_ID` |
| `knobs` | every non-secret knob (`Settings.knobs()`), as registered. Readings use these, never the current config |
| `ports` | arm → port → implementation name |
| `forecasts` | id → claim text (M0 shape, kept) |
| `forecast_register` | id → the full `conf/forecasts.yaml` entry `{claim, reading, margin, unit, read}` |
| `capabilities` | `store.capabilities()` at start |
| `git_sha`, `git_dirty` | the commit the run ran from, and whether the tree had changes |
| `isolation` | `roles` iff all three per-role URIs are set, else `convention` |
| `auth_mode` | which Anthropic credential the client used, never a value: `api_key_workspace` (key + `anthropic-workspace-id` header), `oauth_fallback` (key present, no workspace id, token used), `oauth`, `api_key`, `none` |
| `keys_present` | secret knob → bool, plus `anthropic_workspace_id` (removed from `knobs`). Presence only; a test asserts no secret or workspace id reaches `runs` |
| `models` | model knob → configured model id |
| `models_served` | stamped at `finish_run` from `spend`: stage → `{requested, served, ok, failed{error: n}}` |
| `prompt_hashes` | party → sha256 of its `impl/parties/<party>.py` source (prompt, wire and mapping live there) |
| `pack_hash`, `world_counts` | `World.pack_hash`/`inventory()` when offered, else the pack file's sha256 and `{}` |
| `arm_specs` | arm → `ArmSpec` as registered; readings use these, not the current `conf/arms.yaml` |
| `length` | `run --length` (None: `RUN_LENGTH`) |
| `started_at`, `ended_at` | written at start / by `finish_run` (called from `run` in a `finally`) |
| `lost_spend_writes` | spend rows the call path failed to write, stamped at finish |
| `resumes[]` | one entry per resume where something moved: `{at, length, git_dirty, moved{field: {registered, current}}}` over knobs, git sha, prompt hashes, ports, pack hash, forecasts, arm specs, length |

Rules: the registered fields are never edited; after start only `ended_at`, `models_served`,
`lost_spend_writes` and `resumes[]` are written. Episodes for a run id with no record → refused
(`PreRegistrationError`). A resume with moved fields appends to `resumes[]` and the report prints it; the
registered forecasts hold. Re-registering means a new `RUN_ID` (Run A is a pilot; Run B re-registers;
`report --against` prints the diff of knobs and every registered field).

## 2. Ledgers the readings read

- `episodes`: first attempt `correct`, `confidence`, `consulted[{decision_id, disposition}]` (proposer
  dispositions), `matched_ids` (what the consulter returned: hook-matched or retrieved; E9 reads it),
  `view_map`, `template`, `question_id`, `error`: only a harness failure (`error` starting `episode_failed`,
  `HARNESS_FAILURE_PREFIX`) is excluded from rates and pairs and counted (`n_error`); any other `error` (empty
  result, refused or unparsed pipeline, bad answer_path) is the proposer's wrong answer and counts as a miss;
  `PipelineRefused…` also counts as a guard refusal), `stream` (`stream` | `v` | `injection`), V episodes
  carry their read point in `v_at`.
- `decisions`: lifecycle; `admitted_at_idx` when S4 writes it (else the lifecycle index while admitted, else the
  end of its draft's round). Drift resolution = a held pre-drift decision `superseded` with its successor
  present; `converged` (a merge) and `retired` are not resolution.
- `drafts` (`round`, `status`, `source`: `injection` drafts and their backtests are counted apart, never in
  organic readings), `backtests` (`sampled[]` paired outcomes), `fires` (`role`, `at_idx`), `tool_access`
  (rewires, for the floor beat).
- `planted_map` (evaluation only): `{_id: PM-<id>, run_id, arm, decision_id, quirk|null, scope, model, subject}`,
  `subject` `decision` or `draft` (backtested drafts, for the § 12 premise join). Written by
  `munchhausen planted-map <run_id>`: `PLANTED_MAP_MODEL`, then `PLANTED_MAP_FALLBACK_MODEL` per subject; rows
  persisted as read; a re-run maps only unmapped subjects; spend tagged arm `EVALUATION_SPEND_ARM`.
- Not metered: Voyage embed/rerank and the TypeSafe lens panel (the report discloses it).
- `spend` (time series, meta `{run_id, arm, stage, model, episode_id?}`; `episode_id` from the `ContextVar`
  named `current_episode_id` that the forward pass sets): one row per model call — `tokens_in/out`,
  `tokens_cache_read/write`, `latency_ms`, `usd` (list price, `MODEL_PRICES_USD_PER_MTOK`), `prompt_hash`
  (sha256 of the system prompt), `request_id` (`"cache"` on a response-cache hit), `served_model`
  (`message.model`), `ok`, `error` (class and HTTP status, e.g. `RateLimitError(429)`). **A failed call is a row.**
  Parties calling `client` directly use `llm.record_call(...)` and `llm.record_error(...)`.
- **Disclosed cost-attribution skew: shared Voyage caches.** `embedding_cache` and `rerank_cache` (`EMBED_CACHE`,
  `RERANK_CACHE`) are content-addressed and shared by every arm and run by design: the same input gets the same
  vector or order, so no arm's retrieval depends on which arm asked first. Their spend does. A `spend` row
  (stage `embed`/`rerank`, meta `arm` = the arm whose port sent the request, `VOYAGE_UNATTRIBUTED_ARM` when the
  port is bound to none) is written only for an actual Voyage request; a cache hit writes no row and is counted
  only in the port's `stats()`. The first arm to embed or rerank an input pays and every later arm reads it free;
  two arms that miss in the same micro-batch window both pay. Per-arm embed/rerank `usd` therefore reads arrival
  order, not each arm's own need. Read it summed over arms, or per arm as an upper bound; never as a paired
  difference. Model calls are not skewed this way: the response cache (`RESPONSE_CACHE`) keys on the arm, and a
  hit writes a zero-token row with `request_id: "cache"`.

## 3. `rounds` and trace events

`evidence.close_round(h, arm, round, (lo, hi))` (half-open, as the runner emits it) runs one aggregation over
`episodes` with `$lookup`s into `drafts`, `decisions`, `observations`, `fires`, `spend`, `rounds` and `$merge`s
into `rounds` on `(run_id, arm, round)`: `n_stream, n_error, acc_stream, acc_self_assessed, calibration_gap`
(the three over stream episodes without `error`), `acc_v, store_sizes, admitted, refused (drafts of the round),
superseded, moot, retired, converged (lifecycle index in range), fires{role: n}, view_filtered, tokens_in/out,
tokens_per_episode` (from `spend` rows whose `meta.episode_id` is one of the round's episodes; null when none
are attributed, never 0), `usd_cum, usd, usd_per_episode, closed_at`. A round with no episodes in range gets an
empty record.

Trace (`TRACE_IMPL=jsonl`) → `var/runs/<run_id>/events.jsonl`, one line per event:
`{at, run_id, name, arm, idx?, <ids>…}`. Write-only: nothing on the learning path reads it (SPEC § 21).
The catalog (`domain/registers.TRACE_EVENTS`) is the names the surfaces emit; also catalogued by pattern:
`<stage>.failed`, `lifecycle.<status>`, `injection.*`. Other names are written with `uncatalogued: true`.
`TRACE_IMPL` may name several traces (`jsonl,raindrop`); each receives every call. `raindrop` (SPEC § 25.1)
sends episodes, their signals and the events matching `RAINDROP_EVENTS`; nothing reads it back.

| surface | names |
|---|---|
| forward pass, runner (S2) | `episode` (begin: ids, `template`, `persona`, `text`, `run_id`; finish: the answer), `consultation_set`, `view_resolved`, `guard_refusal` (carries `party`; read as `unknown` without it), `proposal_failed`, `episode_output` (`pipeline`, `confidence`), `episode_written`, `episode_failed`, `fire_raised`, `round_closed`; signals `correct` and `authority_correction` (value: the figure, comment: the phrasing) |
| shaping (S3) | `observation.none`, `observation.refused`, `observation.written`, `shape.formed`, `shape.split`, `shape.failed`, `shape.windowed`, `shape.refused`, `bar.verdict`, `bar.direction_read`, `nominator.run`, `nomination.failed`, `draft.written`, `draft.renominated`, `draft.resumed`, `draft.adjudicated`, `draft.supersede_stripped` |
| adjudication, lifecycle (S4) | `backward.round`, `backward.unavailable`, `adjudication`, `adjudication.layer`, `adjudication.failed`, `backtest`, `admission`, `admission.failed`, `lifecycle.superseded` / `.converged` / `.moot` / `.retired` / `.sweep`, `view.create`, `view.drop`, `tool_access.rewire`, `fire.dispose`, `owner.dispose`, `direct.merge`, `self_grade`, `lensfit.label` |
| injection (S6) | `injection.*` (counted apart) |
| evidence (S5) | `run_start`, `run_finish` |

## 4. Readings (`metrics/readings.py`)

Each returns `{name, value, unit, population, n, interval?, level?, query, note?}`. Arms come from `ArmSpec`s;
arm names live only in `conf/forecasts.yaml` (`read:` blocks).
- Curves: stream accuracy, self-assessed accuracy, calibration gap per arm per round (errored excluded and
  counted); V accuracy per read point; **paired difference vs the reference arm** (F1's `read.reference`),
  rolling over `PAIRED_ROLLING_WINDOW` indices, one point per round with interval and n (demo beat 1).
- F1 `drift_calibration`: per arm holding a pre-drift decision on the drifting quirk, gap after − before over
  `DRIFT_WINDOW`; the after-window ends at a supersession or retirement (a converge does not end holding);
  two-sample bootstrap; the reference arm's difference-in-differences in the note.
- F2/F3 `planted_count`/`planted_scope` over decision subjects: `agrees`/`disagrees`; `unread` without a map or
  when an expected arm did not run.
- F4 `drift_latency`: supersession index − drift index. If either arm never held, or held but did not resolve,
  the comparison is `unread` with the reason.
- F5/F6 `paired_accuracy`: paired on `idx`, same `question_id`, neither side errored (dropped pairs counted in the
  note), quirk-bearing templates (pack), `idx ≥ after_round · ROUND_SIZE`.
- Stale-applied rate (L11), lifecycle counts (converged apart), backtest admit rate and histograms (organic
  only), § 12 premise joined to the planted map of each draft (misses on the draft's quirk; unmapped drafts →
  PROXY), supersession audit (doctrine § 11.2), E9 (reads `matched_ids`), floor (rewires, view-filtered
  episodes), injection counts, spend, models served, guard refusals (from episodes' `error`), not-metered calls.
- E8 (exploratory, not pre-registered): `novelty(a, r)` = mean over arm a's observations written in round r
  (disposition ≠ noise, via ≠ injection) of the minimum cosine distance to any of a's observations from rounds
  < r, on `emb.<key>` with the key from the arm's registered `representation` port; round 0 undefined; n per
  round. **Lead** = (idx of the first dispositive fire at or after D1_AT on a decision mapped to the drifting
  quirk) − (last idx of the first round starting at or after D1_AT whose novelty exceeds the pre-D1 rounds'
  mean + 2 SD). `unread` without a fire, an alarm, ≥ 2 pre-D1 rounds, or the planted map.
Verdicts: `above` / `within` / `below`; `unread` with no pairs or missing inputs; **`unread (proxy)`** whenever
the population is a proxy (no planted map): a proxy never earns an agreement verdict.

## 5. Report

`munchhausen report <run_id> [--against <run_id>]` → `var/reports/<run_id>/`: `readings.json`, `report.md`,
`report.html` (self-contained data; Chart.js pinned), `manifest.json` (figure → query, n, unit; a test asserts
every figure has one). `munchhausen report-demo` renders a SYNTHETIC run (labelled) with no Atlas or model.
`munchhausen spend [run_id]` — live cost per arm × stage × model. `munchhausen runs [--diff A --diff B]`.
