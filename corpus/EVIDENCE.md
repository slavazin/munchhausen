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
| `started_at`, `ended_at` | `ended_at` and `models_served` are the only fields written after start |

Rules: an existing record is returned unedited on resume. Episodes for a run id with no record → refused
(`PreRegistrationError`). A changed `conf/forecasts.yaml` under an existing run id is warned and ignored:
re-registering means a new `RUN_ID` (Run A is a pilot; Run B re-registers; `report --against` prints the knob diff).

## 2. Ledgers the readings read

- `episodes`: first attempt `correct`, `confidence`, `consulted[{decision_id, disposition}]`, `view_map`,
  `template`, `stream` (`stream` | `v` | `injection`), `tokens` (`{"in": n, "out": n}` is the shape the round
  record sums), V episodes carry their read point in `v_at` (else `idx`).
- `decisions`: lifecycle and status index. **Ask (S4):** add `admitted_at_idx` at admission; a superseded
  decision's `lifecycle.at_idx` is its supersession index, so its admission index is otherwise recovered from
  its draft's round (end of round).
- `drafts` (`round`, `status`), `backtests` (`sampled[]` paired outcomes), `fires` (`role`, `at_idx`).
- `planted_map` (new, evaluation only): `{_id: PM-<decision>, run_id, arm, decision_id, quirk|null, scope, model}`,
  written by `munchhausen planted-map <run_id>` (Opus judge; never on the learning path).
- `spend` (time series, meta `{run_id, arm, stage, model}`): one row per model call — `tokens_in/out`,
  `tokens_cache_read/write`, `latency_ms`, `usd` (list price, `MODEL_PRICES_USD_PER_MTOK`), `prompt_hash`
  (sha256 of the system prompt), `request_id` (`"cache"` on a response-cache hit), `served_model`
  (`message.model`), `ok`, `error` (class and HTTP status, e.g. `RateLimitError(429)`). **A failed call is a row.**
  Parties calling `client` directly use `llm.record_call(...)` and `llm.record_error(...)`.

## 3. `rounds` and trace events

`evidence.close_round(h, arm, round, (first, last))` runs one aggregation over `episodes` with `$lookup`s into
`drafts`, `decisions`, `observations`, `fires`, `spend`, `rounds` and `$merge`s into `rounds` on
`(run_id, arm, round)`: `n_stream, acc_stream, acc_self_assessed, calibration_gap, acc_v, store_sizes,
admitted, refused (drafts of the round), superseded, moot, retired, converged (lifecycle index in range),
fires{role: n}, view_filtered, tokens_in/out, tokens_per_episode, usd_cum, usd, usd_per_episode, closed_at`.

Trace (`TRACE_IMPL=jsonl`) → `var/runs/<run_id>/events.jsonl`, one line per event:
`{at, run_id, name, arm, idx?, <ids>…}`. Write-only: nothing on the learning path reads it (SPEC § 21).
Emit with `trace.event(name, payload)`; names outside the catalog are written with `uncatalogued: true`.

| name | payload ids |
|---|---|
| `episode` | `arm, idx, episode_id, question_id, template` (via `begin`/`finish`) |
| `consultation` | `arm, idx, episode_id, decision_id, disposition` |
| `guard_refusal` | `arm, idx, party, stage, reason` (pipeline guard; the sandbox reading counts these) |
| `observation` | `arm, idx, observation_id, episode_id, class` |
| `shape` | `arm, round, shape_id, observation_ids` |
| `bar` | `arm, round, shape_id, passed, gap` |
| `draft` | `arm, round, draft_id, shape_id, route` |
| `layer` | `arm, draft_id, layer, verdict` |
| `backtest` | `arm, draft_id, backtest_id, fixed, fixed_heldout, broken, verdict` |
| `admission` | `arm, idx, decision_id, draft_id, backtest_id` |
| `supersession` | `arm, idx, decision_id, superseded_by, fire_ids` |
| `moot`, `retire` | `arm, idx, decision_id, reason` |
| `view_rewire` | `arm, idx, decision_id, logical, view` |
| `fire` | `arm, idx, fire_id, decision_id, role, cause` |
| `fire_disposed` | `arm, idx, fire_id, disposition, disposer` |
| `owner_override` | `arm, idx, decision_id, draft_id, verdict` |
| `run_start`, `round_close`, `run_finish` | written by `evidence.py` |

## 4. Readings (`metrics/readings.py`)

Each returns `{name, value, unit, population, n, interval?, level?, query, note?}`. Arms come from `ArmSpec`s;
arm names live only in `conf/forecasts.yaml` (`read:` blocks).
- Curves: stream accuracy, self-assessed accuracy, calibration gap per arm per round; V accuracy per read point.
- F1 `drift_calibration`: per arm holding a pre-drift decision on the drifting quirk (planted map; without one,
  every pre-drift decision, flagged PROXY), gap after − before over `DRIFT_WINDOW`, after-window cut at the
  supersession; two-sample bootstrap; the reference arm's difference-in-differences in the note.
- F2/F3 `planted_count`/`planted_scope`: verdict `agrees`/`disagrees`/`unread`.
- F4 `drift_latency`: resolution index − drift index; unresolved arms censored at their last index.
- F5/F6 `paired_accuracy`: paired on `idx`, quirk-bearing templates (pack), `idx ≥ after_round · ROUND_SIZE`.
- Stale-applied rate (L11: eligible only from `admission + LABEL_HORIZON`), backtest admit rate and fixed/broken
  histograms, § 12 premise, supersession audit (doctrine § 11.2), E9 retrieval lead, spend, models served,
  guard refusals.
Verdicts: `above` / `within` / `below` (`unread` with no pairs). A reading without its inputs is `unread`.

## 5. Report

`munchhausen report <run_id> [--against <run_id>]` → `var/reports/<run_id>/`: `readings.json`, `report.md`,
`report.html` (self-contained data; Chart.js pinned), `manifest.json` (figure → query, n, unit; a test asserts
every figure has one). `munchhausen report-demo` renders a SYNTHETIC run (labelled) with no Atlas or model.
`munchhausen spend [run_id]` — live cost per arm × stage × model. `munchhausen runs [--diff A --diff B]`.
