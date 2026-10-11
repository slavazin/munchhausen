# Evidence report — run `run-a`

Started 2026-10-11T21:41:34.388000Z, ended 2026-10-11T22:23:06.645000Z; git `5c171151316e6e9cba418117b98cc1bc06ffbfd8`; isolation `roles`; pack hash `71b9b2113725`; arms read: frozen, self_ref, naive, ungated, governed.

Anthropic auth mode: `api_key_workspace` (presence only); run length 600; spend rows lost: 0.

> Resume 1 at 2026-10-11T21:50:26.720000Z: moved since registration: git_sha, knobs.conf_dir, knobs.direct_concurrency, knobs.packs_dir, knobs.raindrop_debug, knobs.workers_per_arm (registered forecasts and knobs hold).
> Resume 2 at 2026-10-11T21:51:35.207000Z: moved since registration: git_sha, knobs.backtest_concurrency, knobs.backtest_n, knobs.backtest_sample, knobs.bar_min_templates_floor, knobs.conf_dir, knobs.direct_concurrency, knobs.packs_dir, knobs.raindrop_debug, knobs.workers_per_arm (registered forecasts and knobs hold).
> Resume 3 at 2026-10-11T21:53:37.216000Z: moved since registration: git_sha, knobs.backtest_concurrency, knobs.backtest_n, knobs.backtest_sample, knobs.bar_min_templates_floor, knobs.conf_dir, knobs.direct_concurrency, knobs.packs_dir, knobs.raindrop_debug, knobs.workers_per_arm (registered forecasts and knobs hold).

| model knob | configured |
|---|---|
| embed_model | voyage-4 |
| lens_fallback_model | claude-opus-5-5 |
| naive_lesson_model | claude-sonnet-5-5 |
| nominator_model | claude-sonnet-5-5 |
| observer_model | claude-haiku-4-5 |
| planted_map_fallback_model | claude-sonnet-5-5 |
| planted_map_model | claude-opus-5-5 |
| proposer_model | claude-haiku-5-5 |
| rerank_model | rerank-3 |

- stage `embed`: requested voyage-4; served NONE; 1255 calls answered; failed: none.
- stage `lesson`: requested claude-sonnet-5-5; served claude-sonnet-5-5; 201 calls answered; failed: none.
- stage `nominate`: requested claude-sonnet-5-5; served claude-sonnet-5-5; 192 calls answered; failed: none.
- stage `observe`: requested claude-haiku-4-5; served claude-haiku-4-5-20251001; 668 calls answered; failed: none.
- stage `propose`: requested claude-haiku-5-5; served claude-haiku-5-5; 3800 calls answered; failed: ValidationError × 1.
- stage `replay`: requested claude-haiku-5-5; served claude-haiku-5-5; 462 calls answered; failed: none.
- stage `rerank`: requested rerank-3; served NONE; 2110 calls answered; failed: none.
- stage `retry`: requested claude-haiku-5-5; served claude-haiku-5-5; 739 calls answered; failed: none.
- stage `self_grade`: requested claude-haiku-5-5; served claude-haiku-5-5; 600 calls answered; failed: none.

Every figure below names the query that produced it (`manifest.json`). A forecast is printed beside its reading; a disagreement stands as one. Forecasts are the ones registered in `runs` at start, not the current `conf/forecasts.yaml`.

## Forecasts beside their readings

### F1

- **Forecast:** an arm holding a pre-D1 Q1 decision shows a calibration gap over D1_AT…D1_AT+150 above its gap over the 150 episodes before D1_AT, until a successor is admitted (margin 0.05 accuracy points (fraction)).
- **Reading:** calibration gap (mean confidence − accuracy) after minus before, per arm; frozen with the stream on is the no-decision reference.
  - `F1.ungated` = +0.193 accuracy points (calibration gap, after − before), 90% interval [+0.096, +0.288]; n = 90; population: stream episodes of arm ungated (harness failures excluded): idx 150…299 (before) vs 300…389 (after); n = smaller window. Note: held: D-79aec5f32f. frozen-referenced difference-in-differences +0.148 [+0.043, +0.246], n = 90 paired indices per window (smaller).
  - `F1.governed` = +0.172 accuracy points (calibration gap, after − before), 90% interval [+0.084, +0.259]; n = 150; population: stream episodes of arm governed (harness failures excluded): idx 150…299 (before) vs 300…449 (after); n = smaller window. Note: held: D-b469701131. frozen-referenced difference-in-differences +0.130 [+0.056, +0.203], n = 150 paired indices per window (smaller).
- **Verdict** `F1.ungated`: above the margin: the reading agrees with the forecast.
- **Verdict** `F1.governed`: above the margin: the reading agrees with the forecast.

### F2

- **Forecast:** sanity check, not a finding: governed admits 0 N1-derived decisions; naive admits ≥ 1 (margin 0.0 decisions).
- **Reading:** planted_map N1-derived admitted count per arm.
  - `planted_count.N1.frozen` = 0 decisions; n = 0; population: decisions of arm frozen mapped by the planted-map judge.
  - `planted_count.N1.self_ref` = 0 decisions; n = 339; population: decisions of arm self_ref mapped by the planted-map judge.
  - `planted_count.N1.naive` = 0 decisions; n = 197; population: decisions of arm naive mapped by the planted-map judge.
  - `planted_count.N1.ungated` = 0 decisions; n = 12; population: decisions of arm ungated mapped by the planted-map judge.
  - `planted_count.N1.governed` = 0 decisions; n = 5; population: decisions of arm governed mapped by the planted-map judge.
- **Verdict** `F2`: the reading disagrees with the forecast.

### F3

- **Forecast:** naive holds P1 at org scope; governed holds it at persona scope or not at all (margin 0.0 decisions).
- **Reading:** planted_map P1 scope per arm.
  - `planted_scope.P1.frozen` = ['none'] scope labels; n = 0; population: decisions of arm frozen mapped to P1.
  - `planted_scope.P1.self_ref` = ['none'] scope labels; n = 0; population: decisions of arm self_ref mapped to P1.
  - `planted_scope.P1.naive` = ['org'] scope labels; n = 1; population: decisions of arm naive mapped to P1.
  - `planted_scope.P1.ungated` = ['org'] scope labels; n = 1; population: decisions of arm ungated mapped to P1.
  - `planted_scope.P1.governed` = ['none'] scope labels; n = 0; population: decisions of arm governed mapped to P1.
- **Verdict** `F3`: the reading agrees with the forecast.

### F4

- **Forecast:** governed drift-to-supersede latency for D1 is below naive's and below ungated's, where those arms resolve the drift at all (margin 30.0 episodes (one ROUND_SIZE)).
- **Reading:** latency difference (other − governed); a single drift event per arm, so the verdict is the sign beyond the margin, with no interval.
  - `F4.naive-governed` = — episodes; n = 0; population: drift D1 at idx 300; arms naive, governed. Note: governed: 150 (D-b469701131 superseded by D-44b2471eeb); naive: — (never held). One drift event per arm: no interval.
  - `F4.ungated-governed` = -60.0 episodes; n = 1; population: drift D1 at idx 300; arms ungated, governed. Note: governed: 150 (D-b469701131 superseded by D-44b2471eeb); ungated: 90 (D-79aec5f32f superseded by D-6b50b38199). One drift event per arm: no interval.
- **Verdict** `F4.naive-governed`: unread: the reading's inputs are missing or an arm did not resolve (see note).
- **Verdict** `F4.ungated-governed`: below the negative margin: the reading disagrees with the forecast.

### F5

- **Forecast:** on quirk-bearing stream questions after round 10, governed accuracy is above naive's (margin 0.05 accuracy (fraction)).
- **Reading:** paired difference governed − naive, same questions by index.
  - `paired_accuracy.governed-naive` = +0.228 accuracy (fraction), 90% interval [+0.169, +0.284]; n = 254; population: quirk-bearing stream questions with idx ≥ 300 (round ≥ 10), paired by idx, same question_id, no harness failure.
- **Verdict** `F5`: above the margin: the reading agrees with the forecast.

### F6

- **Forecast:** on quirk-bearing stream questions after round 10, governed accuracy is above ungated's (the gate's effect) (margin 0.05 accuracy (fraction)).
- **Reading:** paired difference governed − ungated, same questions by index.
  - `paired_accuracy.governed-ungated` = -0.217 accuracy (fraction), 90% interval [-0.272, -0.161]; n = 254; population: quirk-bearing stream questions with idx ≥ 300 (round ≥ 10), paired by idx, same question_id, no harness failure.
- **Verdict** `F6`: below the negative margin: the reading disagrees with the forecast.

## Paired difference against `frozen` (rolling, by stream index)

| arm | idx | difference | interval | n pairs |
|---|---|---|---|---|
| self_ref | 0–29 | +0.000 | [+0.000, +0.000] | 30 |
| self_ref | 0–59 | -0.017 | [-0.050, +0.000] | 60 |
| self_ref | 0–89 | -0.022 | [-0.044, +0.000] | 90 |
| self_ref | 30–119 | -0.056 | [-0.100, -0.022] | 90 |
| self_ref | 60–149 | -0.056 | [-0.100, -0.022] | 90 |
| self_ref | 90–179 | -0.056 | [-0.100, -0.022] | 90 |
| self_ref | 120–209 | -0.033 | [-0.067, +0.000] | 90 |
| self_ref | 150–239 | -0.033 | [-0.067, -0.011] | 90 |
| self_ref | 180–269 | -0.056 | [-0.100, -0.022] | 90 |
| self_ref | 210–299 | -0.056 | [-0.100, -0.022] | 90 |
| self_ref | 240–329 | -0.056 | [-0.100, -0.022] | 90 |
| self_ref | 270–359 | -0.033 | [-0.078, +0.000] | 90 |
| self_ref | 300–389 | -0.022 | [-0.056, +0.011] | 90 |
| self_ref | 330–419 | -0.022 | [-0.067, +0.011] | 90 |
| self_ref | 360–449 | -0.011 | [-0.033, +0.000] | 90 |
| self_ref | 390–479 | -0.011 | [-0.033, +0.000] | 90 |
| self_ref | 420–509 | +0.000 | [+0.000, +0.000] | 90 |
| self_ref | 450–539 | +0.000 | [+0.000, +0.000] | 90 |
| self_ref | 480–569 | +0.000 | [+0.000, +0.000] | 90 |
| self_ref | 510–599 | -0.011 | [-0.033, +0.000] | 90 |
| naive | 0–29 | +0.000 | [+0.000, +0.000] | 30 |
| naive | 0–59 | +0.050 | [+0.017, +0.100] | 60 |
| naive | 0–89 | +0.022 | [-0.011, +0.056] | 90 |
| naive | 30–119 | +0.033 | [-0.011, +0.078] | 90 |
| naive | 60–149 | +0.044 | [-0.011, +0.100] | 90 |
| naive | 90–179 | +0.111 | [+0.056, +0.167] | 90 |
| naive | 120–209 | +0.156 | [+0.100, +0.211] | 90 |
| naive | 150–239 | +0.167 | [+0.100, +0.233] | 90 |
| naive | 180–269 | +0.133 | [+0.078, +0.200] | 90 |
| naive | 210–299 | +0.078 | [+0.022, +0.133] | 90 |
| naive | 240–329 | +0.044 | [-0.011, +0.100] | 90 |
| naive | 270–359 | +0.056 | [-0.011, +0.122] | 90 |
| naive | 300–389 | +0.111 | [+0.033, +0.189] | 90 |
| naive | 330–419 | +0.122 | [+0.033, +0.211] | 90 |
| naive | 360–449 | +0.167 | [+0.078, +0.256] | 90 |
| naive | 390–479 | +0.211 | [+0.122, +0.311] | 90 |
| naive | 420–509 | +0.178 | [+0.089, +0.267] | 90 |
| naive | 450–539 | +0.144 | [+0.067, +0.222] | 90 |
| naive | 480–569 | +0.122 | [+0.056, +0.189] | 90 |
| naive | 510–599 | +0.178 | [+0.111, +0.244] | 90 |
| ungated | 0–29 | +0.000 | [+0.000, +0.000] | 30 |
| ungated | 0–59 | +0.000 | [+0.000, +0.000] | 60 |
| ungated | 0–89 | +0.033 | [+0.011, +0.067] | 90 |
| ungated | 30–119 | +0.078 | [+0.033, +0.133] | 90 |
| ungated | 60–149 | +0.178 | [+0.111, +0.244] | 90 |
| ungated | 90–179 | +0.256 | [+0.178, +0.333] | 90 |
| ungated | 120–209 | +0.333 | [+0.256, +0.411] | 90 |
| ungated | 150–239 | +0.322 | [+0.244, +0.411] | 90 |
| ungated | 180–269 | +0.311 | [+0.233, +0.389] | 90 |
| ungated | 210–299 | +0.356 | [+0.278, +0.433] | 90 |
| ungated | 240–329 | +0.367 | [+0.289, +0.456] | 90 |
| ungated | 270–359 | +0.344 | [+0.267, +0.422] | 90 |
| ungated | 300–389 | +0.278 | [+0.200, +0.356] | 90 |
| ungated | 330–419 | +0.356 | [+0.267, +0.444] | 90 |
| ungated | 360–449 | +0.511 | [+0.422, +0.600] | 90 |
| ungated | 390–479 | +0.611 | [+0.522, +0.700] | 90 |
| ungated | 420–509 | +0.656 | [+0.578, +0.733] | 90 |
| ungated | 450–539 | +0.644 | [+0.567, +0.722] | 90 |
| ungated | 480–569 | +0.689 | [+0.611, +0.767] | 90 |
| ungated | 510–599 | +0.644 | [+0.556, +0.722] | 90 |
| governed | 0–29 | +0.000 | [+0.000, +0.000] | 30 |
| governed | 0–59 | +0.000 | [+0.000, +0.000] | 60 |
| governed | 0–89 | +0.033 | [+0.011, +0.067] | 90 |
| governed | 30–119 | +0.111 | [+0.067, +0.167] | 90 |
| governed | 60–149 | +0.211 | [+0.144, +0.289] | 90 |
| governed | 90–179 | +0.300 | [+0.222, +0.378] | 90 |
| governed | 120–209 | +0.344 | [+0.267, +0.422] | 90 |
| governed | 150–239 | +0.356 | [+0.278, +0.433] | 90 |
| governed | 180–269 | +0.367 | [+0.278, +0.456] | 90 |
| governed | 210–299 | +0.378 | [+0.289, +0.467] | 90 |
| governed | 240–329 | +0.356 | [+0.267, +0.444] | 90 |
| governed | 270–359 | +0.267 | [+0.199, +0.344] | 90 |
| governed | 300–389 | +0.233 | [+0.167, +0.311] | 90 |
| governed | 330–419 | +0.222 | [+0.156, +0.300] | 90 |
| governed | 360–449 | +0.278 | [+0.200, +0.356] | 90 |
| governed | 390–479 | +0.267 | [+0.189, +0.344] | 90 |
| governed | 420–509 | +0.300 | [+0.211, +0.389] | 90 |
| governed | 450–539 | +0.367 | [+0.278, +0.467] | 90 |
| governed | 480–569 | +0.456 | [+0.367, +0.556] | 90 |
| governed | 510–599 | +0.489 | [+0.389, +0.589] | 90 |

## Observation novelty by round (E8; exploratory, not pre-registered)

novelty(arm, r) = mean over the arm's reducible observations written in round r (disposition ≠ noise, via ≠ injection) of the minimum cosine distance to any of the arm's observations from rounds < r, on the run's registered embedder. Round 0 is undefined. Drifts: {'D1': 300}.

| arm | round | novelty (cosine distance) | n observations | n earlier |
|---|---|---|---|---|
| naive | 1 | 0.1550 | 19 | 10 |
| naive | 2 | 0.1816 | 19 | 29 |
| naive | 3 | 0.1323 | 14 | 48 |
| naive | 4 | 0.1114 | 15 | 62 |
| naive | 5 | 0.0784 | 10 | 77 |
| naive | 6 | 0.0820 | 9 | 87 |
| naive | 7 | 0.0712 | 9 | 96 |
| naive | 8 | 0.0791 | 11 | 105 |
| naive | 9 | 0.0850 | 8 | 116 |
| naive | 10 | 0.0789 | 10 | 124 |
| naive | 11 | 0.0434 | 6 | 134 |
| naive | 12 | 0.0681 | 9 | 140 |
| naive | 13 | 0.0662 | 6 | 149 |
| naive | 14 | 0.0592 | 7 | 155 |
| naive | 15 | 0.0385 | 5 | 162 |
| naive | 16 | 0.0637 | 8 | 167 |
| naive | 17 | 0.0615 | 8 | 175 |
| naive | 18 | 0.0672 | 12 | 183 |
| naive | 19 | 0.1037 | 6 | 195 |
| ungated | 1 | 0.1657 | 19 | 11 |
| ungated | 2 | 0.1868 | 16 | 30 |
| ungated | 3 | 0.1415 | 10 | 46 |
| ungated | 4 | 0.1313 | 9 | 56 |
| ungated | 5 | 0.1350 | 7 | 65 |
| ungated | 6 | 0.1737 | 7 | 72 |
| ungated | 7 | 0.0625 | 6 | 79 |
| ungated | 8 | 0.1078 | 5 | 85 |
| ungated | 9 | 0.0990 | 2 | 90 |
| ungated | 10 | 0.0933 | 10 | 92 |
| ungated | 11 | 0.0912 | 10 | 102 |
| ungated | 12 | 0.0721 | 11 | 112 |
| ungated | 13 | 0.0288 | 1 | 123 |
| ungated | 14 | 0.1172 | 1 | 124 |
| ungated | 15 | 0.0360 | 2 | 125 |
| ungated | 16 | 0.0417 | 1 | 127 |
| ungated | 17 | 0.0528 | 2 | 128 |
| ungated | 18 | 0.0222 | 1 | 130 |
| governed | 1 | 0.1506 | 18 | 10 |
| governed | 2 | 0.1773 | 17 | 28 |
| governed | 3 | 0.1582 | 8 | 45 |
| governed | 4 | 0.1963 | 7 | 53 |
| governed | 5 | 0.0810 | 6 | 60 |
| governed | 6 | 0.1453 | 4 | 66 |
| governed | 7 | 0.1102 | 3 | 70 |
| governed | 8 | 0.1399 | 1 | 73 |
| governed | 9 | 0.1243 | 3 | 74 |
| governed | 10 | 0.1015 | 11 | 77 |
| governed | 11 | 0.0762 | 9 | 88 |
| governed | 12 | 0.0517 | 9 | 97 |
| governed | 13 | 0.0632 | 6 | 106 |
| governed | 14 | 0.0777 | 9 | 112 |
| governed | 15 | 0.1117 | 8 | 121 |
| governed | 16 | 0.0874 | 6 | 129 |
| governed | 17 | 0.0643 | 3 | 135 |
| governed | 18 | 0.0289 | 4 | 138 |
| governed | 19 | 0.0550 | 2 | 142 |

## Readings

- `frozen.stream_accuracy` = 0.328 accuracy (fraction); n = 600; population: stream episodes of arm frozen (0 harness failures excluded).
- `frozen.calibration_gap` = +0.305 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm frozen (0 harness failures excluded).
- `frozen.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm frozen.
- `self_ref.stream_accuracy` = 0.300 accuracy (fraction); n = 600; population: stream episodes of arm self_ref (0 harness failures excluded).
- `self_ref.calibration_gap` = +0.296 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm self_ref (0 harness failures excluded).
- `self_ref.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm self_ref.
- `naive.stream_accuracy` = 0.443 accuracy (fraction); n = 600; population: stream episodes of arm naive (0 harness failures excluded).
- `naive.calibration_gap` = +0.075 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm naive (0 harness failures excluded).
- `naive.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm naive.
- `ungated.stream_accuracy` = 0.707 accuracy (fraction); n = 600; population: stream episodes of arm ungated (0 harness failures excluded).
- `ungated.calibration_gap` = -0.073 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm ungated (0 harness failures excluded).
- `ungated.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm ungated.
- `governed.stream_accuracy` = 0.618 accuracy (fraction); n = 600; population: stream episodes of arm governed (0 harness failures excluded).
- `governed.calibration_gap` = +0.071 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm governed (0 harness failures excluded).
- `governed.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm governed.
- `stale_applied.ungated` = 0.292 share of episodes; n = 65; population: stream episodes of arm ungated with idx ≥ 300 on Q1_active_customer templates (L11: ≥ LABEL_HORIZON after admission).
- `stale_applied.governed` = 0.431 share of episodes; n = 65; population: stream episodes of arm governed with idx ≥ 300 on Q1_active_customer templates (L11: ≥ LABEL_HORIZON after admission).
- `quirk_recall.frozen` = 0.000 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm frozen.
- `quirk_recall.self_ref` = 0.000 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm self_ref.
- `quirk_recall.naive` = 0.800 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm naive. Note: P1_claire_rounding, Q3_soft_delete, Q5_revenue, Q6_tech_names.
- `quirk_recall.ungated` = 1.000 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm ungated. Note: P1_claire_rounding, Q1_active_customer, Q3_soft_delete, Q5_revenue, Q6_tech_names.
- `quirk_recall.governed` = 0.800 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm governed. Note: Q1_active_customer, Q3_soft_delete, Q5_revenue, Q6_tech_names.
- `backtest.admit_rate.governed` = 0.333 share of backtests; n = 15; population: organic backtests of arm governed.
- `backtest.fixed_hist.governed` = {1: 4, 2: 1, 3: 2, 4: 2, 5: 3, 6: 2, 7: 1} backtests per fixed count; n = 15; population: organic backtests of arm governed.
- `backtest.broken_hist.governed` = {0: 13, 2: 1, 4: 1} backtests per broken count; n = 15; population: organic backtests of arm governed.
- `backtest.premise.governed` = 0.900 share of encoded misses fixed; n = 40; population: paired-replay samples whose baseline missed on the draft's quirk, first 10 organic backtests of arm governed. Note: § 12 premise (≥ 50%): holds.
- `supersession_audit.ungated` = 1 supersessions after a dispositive fire; n = 1; population: superseded decisions of arm ungated.
- `supersession_audit.governed` = 1 supersessions after a dispositive fire; n = 1; population: superseded decisions of arm governed.
- `E9.self_ref-over-ungated` = — share of lead indices; n = 0; population: quirk-bearing stream indices where ungated missed and self_ref hit.
- `E9.self_ref-over-governed` = 0.000 share of lead indices; n = 2; population: quirk-bearing stream indices where governed missed and self_ref hit.
- `E9.naive-over-ungated` = 0.455 share of lead indices; n = 11; population: quirk-bearing stream indices where ungated missed and naive hit.
- `E9.naive-over-governed` = 0.071 share of lead indices; n = 42; population: quirk-bearing stream indices where governed missed and naive hit.
- `spend.usd.frozen` = 0.476 USD (list price); n = 760; population: model calls tagged arm frozen.
- `spend.usd_per_episode.frozen` = 0.001 USD per stream episode; n = 600; population: model calls tagged arm frozen / stream episodes.
- `spend.usd.governed` = 4.490 USD (list price); n = 2389; population: model calls tagged arm governed.
- `spend.usd_per_episode.governed` = 0.007 USD per stream episode; n = 600; population: model calls tagged arm governed / stream episodes.
- `spend.usd.naive` = 3.737 USD (list price); n = 2619; population: model calls tagged arm naive.
- `spend.usd_per_episode.naive` = 0.006 USD per stream episode; n = 600; population: model calls tagged arm naive / stream episodes.
- `spend.usd.self_ref` = 1.190 USD (list price); n = 2424; population: model calls tagged arm self_ref.
- `spend.usd_per_episode.self_ref` = 0.002 USD per stream episode; n = 600; population: model calls tagged arm self_ref / stream episodes.
- `spend.usd.ungated` = 4.728 USD (list price); n = 1836; population: model calls tagged arm ungated. Note: 1 failed calls.
- `spend.usd_per_episode.ungated` = 0.008 USD per stream episode; n = 600; population: model calls tagged arm ungated / stream episodes.
- `models.served.embed` = ['none'] model ids; n = 1255; population: model calls of stage embed. Note: requested voyage-4.
- `models.served.lesson` = ['claude-sonnet-5-5'] model ids; n = 201; population: model calls of stage lesson. Note: requested claude-sonnet-5-5.
- `models.served.nominate` = ['claude-sonnet-5-5'] model ids; n = 192; population: model calls of stage nominate. Note: requested claude-sonnet-5-5.
- `models.served.observe` = ['claude-haiku-4-5-20251001'] model ids; n = 668; population: model calls of stage observe. Note: requested claude-haiku-4-5.
- `models.served.propose` = ['claude-haiku-5-5'] model ids; n = 3801; population: model calls of stage propose. Note: requested claude-haiku-5-5; failed: ValidationError × 1.
- `models.served.replay` = ['claude-haiku-5-5'] model ids; n = 462; population: model calls of stage replay. Note: requested claude-haiku-5-5.
- `models.served.rerank` = ['none'] model ids; n = 2110; population: model calls of stage rerank. Note: requested rerank-3.
- `models.served.retry` = ['claude-haiku-5-5'] model ids; n = 739; population: model calls of stage retry. Note: requested claude-haiku-5-5.
- `models.served.self_grade` = ['claude-haiku-5-5'] model ids; n = 600; population: model calls of stage self_grade. Note: requested claude-haiku-5-5.
- `lifecycle.self_ref` = {'admitted': 131, 'converged': 186, 'moot': 22} decisions per lifecycle status; n = 339; population: decisions of arm self_ref. Note: converged = merged into a successor; not a supersession, never a drift resolution.
- `lifecycle.naive` = {'admitted': 68, 'converged': 121, 'moot': 8} decisions per lifecycle status; n = 197; population: decisions of arm naive. Note: converged = merged into a successor; not a supersession, never a drift resolution.
- `lifecycle.ungated` = {'admitted': 11, 'superseded': 1} decisions per lifecycle status; n = 12; population: decisions of arm ungated. Note: converged = merged into a successor; not a supersession, never a drift resolution.
- `lifecycle.governed` = {'admitted': 4, 'superseded': 1} decisions per lifecycle status; n = 5; population: decisions of arm governed. Note: converged = merged into a successor; not a supersession, never a drift resolution.
- `floor.rewires.governed` = [{'logical': 'transactions', 'view': 'transactions__D-f08c8d69ae', 'decision_id': 'D-f08c8d69ae'}] rewired collections; n = 1; population: tool_access rows of arm governed.
- `floor.view_filtered.governed` = 60 episodes; n = 600; population: stream episodes of arm governed whose pipeline ran through a view. Note: first at idx 540.
- `injection.drafts` = 0 drafts; n = 0; population: drafts with source injection.
- `injection.backtests` = {} backtests per verdict; n = 0; population: backtests of injection drafts.
- `injection.episodes` = 0 episodes; n = 0; population: episodes with stream injection.
- `injection.events` = {} trace events; n = 0; population: injection.* trace events.
- `sandbox.guard_refusals.frozen` = 0 refused pipelines; n = 760; population: episodes of arm frozen.
- `sandbox.guard_refusals.self_ref` = 0 refused pipelines; n = 760; population: episodes of arm self_ref.
- `sandbox.guard_refusals.naive` = 0 refused pipelines; n = 760; population: episodes of arm naive.
- `sandbox.guard_refusals.ungated` = 0 refused pipelines; n = 760; population: episodes of arm ungated.
- `sandbox.guard_refusals.governed` = 0 refused pipelines; n = 760; population: episodes of arm governed.
- `spend.not_metered` = ['typesafe lens panel'] call kinds; n = 0; population: model calls outside the Anthropic and Voyage call paths. Note: these calls are not metered: spend readings exclude their cost and tokens.
- `E8.lead.naive` = — episodes; n = 0; population: novelty rounds of arm naive; dispositive fires of arm naive on Q1 decisions at idx ≥ 300. Note: exploratory, not pre-registered; no round after the drift exceeds pre-drift mean + 2 SD (0.187).
- `E8.lead.ungated` = — episodes; n = 0; population: novelty rounds of arm ungated; dispositive fires of arm ungated on Q1 decisions at idx ≥ 300. Note: exploratory, not pre-registered; no round after the drift exceeds pre-drift mean + 2 SD (0.213).
- `E8.lead.governed` = — episodes; n = 0; population: novelty rounds of arm governed; dispositive fires of arm governed on Q1 decisions at idx ≥ 300. Note: exploratory, not pre-registered; no round after the drift exceeds pre-drift mean + 2 SD (0.212).

## Curves (per arm, per round of stream episodes)

| arm | round | idx | n | accuracy | self-assessed | calibration gap |
|---|---|---|---|---|---|---|
| frozen | 0 | 0–29 | 30 | 0.467 | 0.703 | +0.237 |
| frozen | 1 | 30–59 | 30 | 0.200 | 0.625 | +0.425 |
| frozen | 2 | 60–89 | 30 | 0.267 | 0.560 | +0.293 |
| frozen | 3 | 90–119 | 30 | 0.367 | 0.648 | +0.282 |
| frozen | 4 | 120–149 | 30 | 0.367 | 0.659 | +0.293 |
| frozen | 5 | 150–179 | 30 | 0.267 | 0.628 | +0.362 |
| frozen | 6 | 180–209 | 30 | 0.367 | 0.645 | +0.278 |
| frozen | 7 | 210–239 | 30 | 0.433 | 0.583 | +0.150 |
| frozen | 8 | 240–269 | 30 | 0.367 | 0.628 | +0.262 |
| frozen | 9 | 270–299 | 30 | 0.400 | 0.673 | +0.273 |
| frozen | 10 | 300–329 | 30 | 0.300 | 0.607 | +0.307 |
| frozen | 11 | 330–359 | 30 | 0.400 | 0.673 | +0.273 |
| frozen | 12 | 360–389 | 30 | 0.267 | 0.617 | +0.350 |
| frozen | 13 | 390–419 | 30 | 0.433 | 0.633 | +0.200 |
| frozen | 14 | 420–449 | 30 | 0.233 | 0.635 | +0.402 |
| frozen | 15 | 450–479 | 30 | 0.333 | 0.621 | +0.288 |
| frozen | 16 | 480–509 | 30 | 0.300 | 0.653 | +0.353 |
| frozen | 17 | 510–539 | 30 | 0.267 | 0.670 | +0.403 |
| frozen | 18 | 540–569 | 30 | 0.133 | 0.563 | +0.430 |
| frozen | 19 | 570–599 | 30 | 0.400 | 0.642 | +0.242 |
| self_ref | 0 | 0–29 | 30 | 0.467 | 0.707 | +0.240 |
| self_ref | 1 | 30–59 | 30 | 0.167 | 0.554 | +0.387 |
| self_ref | 2 | 60–89 | 30 | 0.233 | 0.493 | +0.260 |
| self_ref | 3 | 90–119 | 30 | 0.267 | 0.580 | +0.313 |
| self_ref | 4 | 120–149 | 30 | 0.333 | 0.626 | +0.293 |
| self_ref | 5 | 150–179 | 30 | 0.233 | 0.560 | +0.326 |
| self_ref | 6 | 180–209 | 30 | 0.333 | 0.566 | +0.233 |
| self_ref | 7 | 210–239 | 30 | 0.400 | 0.556 | +0.156 |
| self_ref | 8 | 240–269 | 30 | 0.267 | 0.537 | +0.271 |
| self_ref | 9 | 270–299 | 30 | 0.367 | 0.671 | +0.304 |
| self_ref | 10 | 300–329 | 30 | 0.267 | 0.567 | +0.301 |
| self_ref | 11 | 330–359 | 30 | 0.367 | 0.568 | +0.202 |
| self_ref | 12 | 360–389 | 30 | 0.267 | 0.577 | +0.311 |
| self_ref | 13 | 390–419 | 30 | 0.400 | 0.589 | +0.189 |
| self_ref | 14 | 420–449 | 30 | 0.233 | 0.611 | +0.378 |
| self_ref | 15 | 450–479 | 30 | 0.333 | 0.630 | +0.296 |
| self_ref | 16 | 480–509 | 30 | 0.300 | 0.646 | +0.346 |
| self_ref | 17 | 510–539 | 30 | 0.267 | 0.655 | +0.388 |
| self_ref | 18 | 540–569 | 30 | 0.133 | 0.590 | +0.456 |
| self_ref | 19 | 570–599 | 30 | 0.367 | 0.641 | +0.274 |
| naive | 0 | 0–29 | 30 | 0.467 | 0.702 | +0.235 |
| naive | 1 | 30–59 | 30 | 0.300 | 0.515 | +0.215 |
| naive | 2 | 60–89 | 30 | 0.233 | 0.470 | +0.237 |
| naive | 3 | 90–119 | 30 | 0.400 | 0.546 | +0.146 |
| naive | 4 | 120–149 | 30 | 0.500 | 0.565 | +0.065 |
| naive | 5 | 150–179 | 30 | 0.433 | 0.466 | +0.032 |
| naive | 6 | 180–209 | 30 | 0.533 | 0.517 | -0.016 |
| naive | 7 | 210–239 | 30 | 0.600 | 0.496 | -0.104 |
| naive | 8 | 240–269 | 30 | 0.433 | 0.480 | +0.047 |
| naive | 9 | 270–299 | 30 | 0.400 | 0.537 | +0.137 |
| naive | 10 | 300–329 | 30 | 0.367 | 0.460 | +0.093 |
| naive | 11 | 330–359 | 30 | 0.500 | 0.550 | +0.050 |
| naive | 12 | 360–389 | 30 | 0.433 | 0.476 | +0.043 |
| naive | 13 | 390–419 | 30 | 0.533 | 0.515 | -0.018 |
| naive | 14 | 420–449 | 30 | 0.467 | 0.513 | +0.047 |
| naive | 15 | 450–479 | 30 | 0.633 | 0.507 | -0.126 |
| naive | 16 | 480–509 | 30 | 0.300 | 0.498 | +0.198 |
| naive | 17 | 510–539 | 30 | 0.400 | 0.541 | +0.141 |
| naive | 18 | 540–569 | 30 | 0.367 | 0.491 | +0.125 |
| naive | 19 | 570–599 | 30 | 0.567 | 0.522 | -0.045 |
| ungated | 0 | 0–29 | 30 | 0.467 | 0.692 | +0.225 |
| ungated | 1 | 30–59 | 30 | 0.200 | 0.627 | +0.427 |
| ungated | 2 | 60–89 | 30 | 0.367 | 0.560 | +0.193 |
| ungated | 3 | 90–119 | 30 | 0.500 | 0.652 | +0.152 |
| ungated | 4 | 120–149 | 30 | 0.667 | 0.610 | -0.057 |
| ungated | 5 | 150–179 | 30 | 0.600 | 0.580 | -0.020 |
| ungated | 6 | 180–209 | 30 | 0.733 | 0.585 | -0.148 |
| ungated | 7 | 210–239 | 30 | 0.700 | 0.591 | -0.109 |
| ungated | 8 | 240–269 | 30 | 0.667 | 0.567 | -0.099 |
| ungated | 9 | 270–299 | 30 | 0.900 | 0.667 | -0.233 |
| ungated | 10 | 300–329 | 30 | 0.600 | 0.677 | +0.077 |
| ungated | 11 | 330–359 | 30 | 0.633 | 0.682 | +0.048 |
| ungated | 12 | 360–389 | 30 | 0.567 | 0.655 | +0.088 |
| ungated | 13 | 390–419 | 30 | 0.967 | 0.642 | -0.325 |
| ungated | 14 | 420–449 | 30 | 0.933 | 0.638 | -0.295 |
| ungated | 15 | 450–479 | 30 | 0.933 | 0.617 | -0.317 |
| ungated | 16 | 480–509 | 30 | 0.967 | 0.687 | -0.280 |
| ungated | 17 | 510–539 | 30 | 0.933 | 0.678 | -0.255 |
| ungated | 18 | 540–569 | 30 | 0.867 | 0.608 | -0.258 |
| ungated | 19 | 570–599 | 30 | 0.933 | 0.657 | -0.277 |
| governed | 0 | 0–29 | 30 | 0.467 | 0.713 | +0.246 |
| governed | 1 | 30–59 | 30 | 0.200 | 0.610 | +0.410 |
| governed | 2 | 60–89 | 30 | 0.367 | 0.555 | +0.188 |
| governed | 3 | 90–119 | 30 | 0.600 | 0.690 | +0.090 |
| governed | 4 | 120–149 | 30 | 0.667 | 0.690 | +0.023 |
| governed | 5 | 150–179 | 30 | 0.633 | 0.702 | +0.068 |
| governed | 6 | 180–209 | 30 | 0.733 | 0.687 | -0.047 |
| governed | 7 | 210–239 | 30 | 0.767 | 0.662 | -0.105 |
| governed | 8 | 240–269 | 30 | 0.767 | 0.730 | -0.037 |
| governed | 9 | 270–299 | 30 | 0.800 | 0.743 | -0.057 |
| governed | 10 | 300–329 | 30 | 0.567 | 0.713 | +0.147 |
| governed | 11 | 330–359 | 30 | 0.533 | 0.697 | +0.163 |
| governed | 12 | 360–389 | 30 | 0.567 | 0.700 | +0.133 |
| governed | 13 | 390–419 | 30 | 0.667 | 0.718 | +0.052 |
| governed | 14 | 420–449 | 30 | 0.533 | 0.721 | +0.187 |
| governed | 15 | 450–479 | 30 | 0.600 | 0.695 | +0.095 |
| governed | 16 | 480–509 | 30 | 0.633 | 0.725 | +0.092 |
| governed | 17 | 510–539 | 30 | 0.767 | 0.708 | -0.058 |
| governed | 18 | 540–569 | 30 | 0.667 | 0.643 | -0.023 |
| governed | 19 | 570–599 | 30 | 0.833 | 0.685 | -0.148 |

## V accuracy (sealed V set)

- `frozen` at idx 75: 0.350 accuracy (fraction), n = 40 V questions.
- `frozen` at idx 225: 0.350 accuracy (fraction), n = 40 V questions.
- `frozen` at idx 375: 0.350 accuracy (fraction), n = 40 V questions.
- `frozen` at idx 525: 0.350 accuracy (fraction), n = 40 V questions.
- `self_ref` at idx 75: 0.325 accuracy (fraction), n = 40 V questions.
- `self_ref` at idx 225: 0.350 accuracy (fraction), n = 40 V questions.
- `self_ref` at idx 375: 0.325 accuracy (fraction), n = 40 V questions.
- `self_ref` at idx 525: 0.300 accuracy (fraction), n = 40 V questions.
- `naive` at idx 75: 0.325 accuracy (fraction), n = 40 V questions.
- `naive` at idx 225: 0.475 accuracy (fraction), n = 40 V questions.
- `naive` at idx 375: 0.300 accuracy (fraction), n = 40 V questions.
- `naive` at idx 525: 0.400 accuracy (fraction), n = 40 V questions.
- `ungated` at idx 75: 0.525 accuracy (fraction), n = 40 V questions.
- `ungated` at idx 225: 0.775 accuracy (fraction), n = 40 V questions.
- `ungated` at idx 375: 0.625 accuracy (fraction), n = 40 V questions.
- `ungated` at idx 525: 0.900 accuracy (fraction), n = 40 V questions.
- `governed` at idx 75: 0.550 accuracy (fraction), n = 40 V questions.
- `governed` at idx 225: 0.650 accuracy (fraction), n = 40 V questions.
- `governed` at idx 375: 0.550 accuracy (fraction), n = 40 V questions.
- `governed` at idx 525: 0.675 accuracy (fraction), n = 40 V questions.

## Lifecycle

| arm | id | status | at idx | admitted idx | superseded by | quirk (planted map) |
|---|---|---|---|---|---|---|
| governed | D-01a513926b | admitted | 90 | 90 |  | Q6_tech_names |
| governed | F-D-01a513926b-unattributed-107 | fire:open | 107 |  |  |  |
| governed | F-D-01a513926b-unattributed-120 | fire:open | 120 |  |  |  |
| governed | F-D-01a513926b-unattributed-145 | fire:open | 145 |  |  |  |
| governed | F-D-01a513926b-unattributed-180 | fire:open | 180 |  |  |  |
| governed | F-D-01a513926b-unattributed-204 | fire:open | 204 |  |  |  |
| governed | F-D-01a513926b-unattributed-218 | fire:open | 218 |  |  |  |
| governed | F-D-01a513926b-unattributed-221 | fire:open | 221 |  |  |  |
| governed | D-69ccceb1c1 | admitted | 240 | 240 |  | Q5_revenue |
| governed | F-D-b469701131-unattributed-240 | fire:applied | 240 |  |  |  |
| governed | F-D-b469701131-T-D-b469701131-1-g0 | fire:applied | 307 |  |  |  |
| governed | F-D-01a513926b-unattributed-396 | fire:open | 396 |  |  |  |
| governed | D-44b2471eeb | admitted | 450 | 450 |  | Q1_active_customer |
| governed | D-b469701131 | superseded | 450 | 60 | D-44b2471eeb | Q1_active_customer |
| governed | F-D-01a513926b-unattributed-452 | fire:open | 452 |  |  |  |
| governed | F-D-01a513926b-unattributed-465 | fire:open | 465 |  |  |  |
| governed | F-D-44b2471eeb-T-D-44b2471eeb-1-g0 | fire:open | 467 |  |  |  |
| governed | F-D-01a513926b-unattributed-468 | fire:open | 468 |  |  |  |
| governed | F-D-44b2471eeb-unattributed-475 | fire:open | 475 |  |  |  |
| governed | D-f08c8d69ae | admitted | 540 | 540 |  | Q3_soft_delete |
| governed | F-D-f08c8d69ae-unattributed-540 | fire:open | 540 |  |  |  |
| governed | F-D-f08c8d69ae-unattributed-546 | fire:open | 546 |  |  |  |
| governed | F-D-44b2471eeb-unattributed-562 | fire:open | 562 |  |  |  |
| governed | F-D-f08c8d69ae-unattributed-564 | fire:open | 564 |  |  |  |
| governed | F-D-f08c8d69ae-unattributed-567 | fire:open | 567 |  |  |  |
| governed | F-D-f08c8d69ae-unattributed-572 | fire:open | 572 |  |  |  |
| governed | F-D-44b2471eeb-unattributed-579 | fire:open | 579 |  |  |  |
| governed | F-D-f08c8d69ae-unattributed-580 | fire:open | 580 |  |  |  |
| governed | F-D-44b2471eeb-unattributed-584 | fire:open | 584 |  |  |  |
| governed | F-D-f08c8d69ae-unattributed-594 | fire:open | 594 |  |  |  |
| naive | D-d02fea6b5c | converged | 30 | 30 |  | P1_claire_rounding |
| naive | D-6407894d0b | converged | 30 | 30 |  | P1_claire_rounding |
| naive | D-8ebe270c2b | converged | 30 | 30 |  |  |
| naive | F-D-8e3b54c002-unattributed-32 | fire:applied | 32 |  |  |  |
| naive | F-D-1efbf58073-unattributed-33 | fire:applied | 33 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-33 | fire:applied | 33 |  |  |  |
| naive | F-D-8e3b54c002-unattributed-33 | fire:applied | 33 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-33 | fire:applied | 33 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-34 | fire:applied | 34 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-35 | fire:applied | 35 |  |  |  |
| naive | F-D-1efbf58073-unattributed-35 | fire:applied | 35 |  |  |  |
| naive | F-D-8e3b54c002-unattributed-35 | fire:applied | 35 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-35 | fire:applied | 35 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-40 | fire:applied | 40 |  |  |  |
| naive | F-D-8e3b54c002-unattributed-41 | fire:applied | 41 |  |  |  |
| naive | F-D-8e3b54c002-unattributed-43 | fire:applied | 43 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-44 | fire:applied | 44 |  |  |  |
| naive | F-D-1efbf58073-unattributed-45 | fire:applied | 45 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-45 | fire:applied | 45 |  |  |  |
| naive | F-D-8e3b54c002-unattributed-45 | fire:applied | 45 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-45 | fire:applied | 45 |  |  |  |
| naive | F-D-1efbf58073-unattributed-47 | fire:applied | 47 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-47 | fire:applied | 47 |  |  |  |
| naive | F-D-8e3b54c002-unattributed-47 | fire:applied | 47 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-47 | fire:applied | 47 |  |  |  |
| naive | F-D-8e3b54c002-unattributed-48 | fire:applied | 48 |  |  |  |
| naive | F-D-1efbf58073-unattributed-58 | fire:applied | 58 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-58 | fire:applied | 58 |  |  |  |
| naive | F-D-8e3b54c002-unattributed-58 | fire:applied | 58 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-58 | fire:applied | 58 |  |  |  |
| naive | D-2ed34b3974 | admitted | 60 | 60 |  |  |
| naive | D-6fd541346d | admitted | 60 | 60 |  |  |
| naive | D-0cb40baf68 | admitted | 60 | 60 |  |  |
| naive | D-2f9637133f | admitted | 60 | 60 |  |  |
| naive | D-90712f0bc6 | converged | 60 | 30 |  |  |
| naive | D-8e3b54c002 | converged | 60 | 30 |  |  |
| naive | D-24694a2fdd | converged | 60 | 60 |  |  |
| naive | D-41d0f04522 | converged | 60 | 30 |  |  |
| naive | D-996d0b9270 | converged | 60 | 60 |  |  |
| naive | D-89f2d86419 | converged | 60 | 60 |  |  |
| naive | D-29cdc837f5 | converged | 60 | 60 |  |  |
| naive | D-da67c168e0 | converged | 60 | 60 |  |  |
| naive | F-D-4634e8da0a-unattributed-60 | fire:applied | 60 |  |  |  |
| naive | F-D-f66a60f411-unattributed-62 | fire:applied | 62 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-64 | fire:applied | 64 |  |  |  |
| naive | F-D-1efbf58073-unattributed-64 | fire:applied | 64 |  |  |  |
| naive | F-D-f66a60f411-unattributed-64 | fire:applied | 64 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-1efbf58073-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-65 | fire:open | 65 |  |  |  |
| naive | F-D-f66a60f411-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-f66a60f411-unattributed-66 | fire:applied | 66 |  |  |  |
| naive | F-D-f66a60f411-unattributed-67 | fire:applied | 67 |  |  |  |
| naive | F-D-f66a60f411-unattributed-70 | fire:applied | 70 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-71 | fire:open | 71 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-72 | fire:applied | 72 |  |  |  |
| naive | F-D-1efbf58073-unattributed-72 | fire:applied | 72 |  |  |  |
| naive | F-D-20cf406490-unattributed-74 | fire:applied | 74 |  |  |  |
| naive | F-D-a7183b418b-unattributed-74 | fire:applied | 74 |  |  |  |
| naive | F-D-fa5211201e-unattributed-74 | fire:applied | 74 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-1efbf58073-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-fb4bd92cdf-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-e0a0c38607-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-f66a60f411-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-85 | fire:applied | 85 |  |  |  |
| naive | F-D-a7183b418b-unattributed-88 | fire:applied | 88 |  |  |  |
| naive | F-D-a7183b418b-unattributed-89 | fire:applied | 89 |  |  |  |
| naive | F-D-fa5211201e-unattributed-89 | fire:applied | 89 |  |  |  |
| naive | D-77e6d11b27 | admitted | 90 | 90 |  | Q6_tech_names |
| naive | D-0ab6f958fe | admitted | 90 | 90 |  |  |
| naive | D-774932d6f8 | admitted | 90 | 90 |  |  |
| naive | D-f9b7159309 | converged | 90 | 90 |  | P1_claire_rounding |
| naive | D-fb4bd92cdf | converged | 90 | 60 |  |  |
| naive | D-f36f44fe25 | converged | 90 | 90 |  |  |
| naive | D-9c7bfb9d2c | converged | 90 | 90 |  |  |
| naive | D-66c975af95 | converged | 90 | 90 |  |  |
| naive | D-bccbe2463f | converged | 90 | 90 |  |  |
| naive | D-efab0a14d7 | converged | 90 | 90 |  |  |
| naive | F-D-31505adbdf-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-e63f8b4c35-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-1efbf58073-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-1ec28d60b7-unattributed-91 | fire:applied | 91 |  |  |  |
| naive | F-D-1ec28d60b7-unattributed-93 | fire:applied | 93 |  |  |  |
| naive | F-D-f66a60f411-unattributed-95 | fire:applied | 95 |  |  |  |
| naive | F-D-20cf406490-unattributed-96 | fire:applied | 96 |  |  |  |
| naive | F-D-3e54be5c09-unattributed-96 | fire:applied | 96 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-98 | fire:open | 98 |  |  |  |
| naive | F-D-f66a60f411-unattributed-99 | fire:applied | 99 |  |  |  |
| naive | F-D-e63f8b4c35-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-9eafbcfeda-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-e0a0c38607-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-31505adbdf-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-1efbf58073-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-102 | fire:open | 102 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-a7183b418b-unattributed-104 | fire:applied | 104 |  |  |  |
| naive | F-D-3e54be5c09-unattributed-104 | fire:applied | 104 |  |  |  |
| naive | F-D-832280b537-unattributed-104 | fire:open | 104 |  |  |  |
| naive | F-D-f66a60f411-unattributed-105 | fire:applied | 105 |  |  |  |
| naive | F-D-e63f8b4c35-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-9eafbcfeda-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-1efbf58073-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-31505adbdf-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-e0a0c38607-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-bfd45e171d-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-a7183b418b-unattributed-109 | fire:applied | 109 |  |  |  |
| naive | F-D-3e54be5c09-unattributed-109 | fire:applied | 109 |  |  |  |
| naive | F-D-832280b537-unattributed-109 | fire:open | 109 |  |  |  |
| naive | F-D-f66a60f411-unattributed-111 | fire:applied | 111 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-112 | fire:open | 112 |  |  |  |
| naive | F-D-20cf406490-unattributed-113 | fire:applied | 113 |  |  |  |
| naive | F-D-fa5211201e-unattributed-113 | fire:applied | 113 |  |  |  |
| naive | F-D-1ec28d60b7-unattributed-115 | fire:applied | 115 |  |  |  |
| naive | F-D-20cf406490-unattributed-116 | fire:applied | 116 |  |  |  |
| naive | F-D-3e54be5c09-unattributed-116 | fire:applied | 116 |  |  |  |
| naive | D-d321935970 | admitted | 120 | 120 |  |  |
| naive | D-1fdf062e78 | converged | 120 | 90 |  | P1_claire_rounding |
| naive | D-1ec28d60b7 | converged | 120 | 90 |  |  |
| naive | D-1efbf58073 | converged | 120 | 30 |  |  |
| naive | D-e63f8b4c35 | converged | 120 | 90 |  |  |
| naive | D-aa1b84cb64 | converged | 120 | 90 |  | Q5_revenue |
| naive | F-D-f95c319115-unattributed-120 | fire:applied | 120 |  |  |  |
| naive | F-D-f95c319115-unattributed-125 | fire:applied | 125 |  |  |  |
| naive | F-D-20cf406490-unattributed-127 | fire:applied | 127 |  |  |  |
| naive | F-D-3e54be5c09-unattributed-127 | fire:applied | 127 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-127 | fire:open | 127 |  |  |  |
| naive | F-D-f95c319115-unattributed-128 | fire:applied | 128 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-133 | fire:open | 133 |  |  |  |
| naive | F-D-134e3a479f-unattributed-133 | fire:applied | 133 |  |  |  |
| naive | F-D-6fd541346d-unattributed-133 | fire:open | 133 |  |  |  |
| naive | F-D-20cf406490-unattributed-135 | fire:applied | 135 |  |  |  |
| naive | F-D-3e54be5c09-unattributed-135 | fire:applied | 135 |  |  |  |
| naive | F-D-20cf406490-anomaly0-135 | fire:applied | 135 |  |  |  |
| naive | F-D-3e54be5c09-anomaly0-135 | fire:applied | 135 |  |  |  |
| naive | F-D-f66a60f411-unattributed-140 | fire:applied | 140 |  |  |  |
| naive | F-D-20cf406490-unattributed-141 | fire:applied | 141 |  |  |  |
| naive | F-D-fa5211201e-unattributed-141 | fire:applied | 141 |  |  |  |
| naive | F-D-f66a60f411-unattributed-142 | fire:applied | 142 |  |  |  |
| naive | F-D-f95c319115-unattributed-143 | fire:applied | 143 |  |  |  |
| naive | D-dd4ba69cd5 | admitted | 150 | 150 |  | Q3_soft_delete |
| naive | D-612f19016d | admitted | 150 | 150 |  |  |
| naive | D-a76732ecc8 | admitted | 150 | 150 |  |  |
| naive | D-f66a60f411 | converged | 150 | 60 |  |  |
| naive | D-a7183b418b | converged | 150 | 60 |  |  |
| naive | D-ad510e57a3 | converged | 150 | 120 |  | Q5_revenue |
| naive | D-c09d513d09 | converged | 150 | 150 |  |  |
| naive | D-a9a546d5ed | converged | 150 | 150 |  |  |
| naive | D-bfd45e171d | converged | 150 | 30 |  |  |
| naive | D-fa5211201e | converged | 150 | 60 |  |  |
| naive | D-9eafbcfeda | converged | 150 | 90 |  |  |
| naive | D-f95c319115 | converged | 150 | 120 |  |  |
| naive | D-851bfaf38e | converged | 150 | 120 |  |  |
| naive | D-5e2af37aad | converged | 150 | 120 |  |  |
| naive | D-bac10ff625 | converged | 150 | 150 |  |  |
| naive | F-D-df7a1e3b89-unattributed-150 | fire:applied | 150 |  |  |  |
| naive | F-D-6e4155552b-unattributed-150 | fire:applied | 150 |  |  |  |
| naive | F-D-9929c9927a-unattributed-150 | fire:applied | 150 |  |  |  |
| naive | F-D-84e1b27a0b-unattributed-152 | fire:applied | 152 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-152 | fire:applied | 152 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-152 | fire:open | 152 |  |  |  |
| naive | F-D-0cb40baf68-unattributed-152 | fire:open | 152 |  |  |  |
| naive | F-D-84e1b27a0b-unattributed-160 | fire:applied | 160 |  |  |  |
| naive | F-D-df7a1e3b89-unattributed-161 | fire:applied | 161 |  |  |  |
| naive | F-D-134e3a479f-unattributed-161 | fire:applied | 161 |  |  |  |
| naive | F-D-2f9637133f-unattributed-161 | fire:open | 161 |  |  |  |
| naive | F-D-84e1b27a0b-unattributed-165 | fire:applied | 165 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-165 | fire:open | 165 |  |  |  |
| naive | F-D-49139f67e5-unattributed-165 | fire:applied | 165 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-165 | fire:applied | 165 |  |  |  |
| naive | F-D-a5050cb656-unattributed-165 | fire:applied | 165 |  |  |  |
| naive | F-D-0cb40baf68-unattributed-165 | fire:open | 165 |  |  |  |
| naive | F-D-31505adbdf-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-2da3374391-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-7013cd82e7-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-171 | fire:open | 171 |  |  |  |
| naive | F-D-9e555d85b8-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-cbe35d411d-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-7013cd82e7-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-2da3374391-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-37f5a76282-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-e0a0c38607-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-cbe35d411d-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-37f5a76282-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-7013cd82e7-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-2da3374391-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-9e555d85b8-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-31505adbdf-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-172 | fire:open | 172 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-84e1b27a0b-unattributed-176 | fire:applied | 176 |  |  |  |
| naive | D-ff675f9c69 | admitted | 180 | 180 |  |  |
| naive | D-b61059e3c9 | admitted | 180 | 180 |  |  |
| naive | D-5112a1e669 | admitted | 180 | 180 |  |  |
| naive | D-49139f67e5 | converged | 180 | 90 |  | Q3_soft_delete |
| naive | D-84e1b27a0b | converged | 180 | 120 |  |  |
| naive | D-20cf406490 | converged | 180 | 60 |  |  |
| naive | D-37f5a76282 | converged | 180 | 150 |  |  |
| naive | D-9929c9927a | converged | 180 | 150 |  |  |
| naive | F-D-77e6d11b27-unattributed-190 | fire:open | 190 |  |  |  |
| naive | F-D-9e555d85b8-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-cbe35d411d-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-7013cd82e7-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-2da3374391-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-e0a0c38607-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-5112a1e669-unattributed-190 | fire:open | 190 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-194 | fire:open | 194 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-195 | fire:open | 195 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-199 | fire:open | 199 |  |  |  |
| naive | F-D-9e555d85b8-unattributed-199 | fire:applied | 199 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-199 | fire:applied | 199 |  |  |  |
| naive | F-D-cbe35d411d-unattributed-199 | fire:applied | 199 |  |  |  |
| naive | F-D-7013cd82e7-unattributed-199 | fire:applied | 199 |  |  |  |
| naive | F-D-2da3374391-unattributed-199 | fire:applied | 199 |  |  |  |
| naive | F-D-e0a0c38607-unattributed-199 | fire:applied | 199 |  |  |  |
| naive | F-D-6fd541346d-unattributed-201 | fire:open | 201 |  |  |  |
| naive | F-D-011a0643a3-unattributed-201 | fire:applied | 201 |  |  |  |
| naive | F-D-134e3a479f-unattributed-201 | fire:applied | 201 |  |  |  |
| naive | F-D-625734ab25-unattributed-201 | fire:applied | 201 |  |  |  |
| naive | F-D-2f9637133f-unattributed-201 | fire:open | 201 |  |  |  |
| naive | F-D-df7a1e3b89-unattributed-202 | fire:applied | 202 |  |  |  |
| naive | F-D-134e3a479f-unattributed-202 | fire:applied | 202 |  |  |  |
| naive | D-ed3e9851df | admitted | 210 | 210 |  |  |
| naive | D-1abc15e30a | admitted | 210 | 210 |  |  |
| naive | D-13ed32258f | admitted | 210 | 210 |  |  |
| naive | D-f379da9a1e | admitted | 210 | 210 |  |  |
| naive | D-124b284685 | admitted | 210 | 210 |  |  |
| naive | D-31505adbdf | converged | 210 | 60 |  |  |
| naive | D-cbe35d411d | converged | 210 | 120 |  |  |
| naive | D-9e555d85b8 | converged | 210 | 120 |  |  |
| naive | F-D-aa768995d4-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-7013cd82e7-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-2da3374391-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-210 | fire:open | 210 |  |  |  |
| naive | F-D-5112a1e669-unattributed-210 | fire:open | 210 |  |  |  |
| naive | F-D-9975d472be-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-124b284685-unattributed-210 | fire:open | 210 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-df7a1e3b89-unattributed-215 | fire:applied | 215 |  |  |  |
| naive | F-D-134e3a479f-unattributed-215 | fire:applied | 215 |  |  |  |
| naive | F-D-6e4155552b-unattributed-215 | fire:applied | 215 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-215 | fire:open | 215 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-216 | fire:open | 216 |  |  |  |
| naive | F-D-3e54be5c09-unattributed-216 | fire:applied | 216 |  |  |  |
| naive | F-D-df7a1e3b89-unattributed-216 | fire:applied | 216 |  |  |  |
| naive | F-D-6cfae3beaa-unattributed-216 | fire:applied | 216 |  |  |  |
| naive | F-D-aa768995d4-unattributed-223 | fire:applied | 223 |  |  |  |
| naive | F-D-2da3374391-unattributed-223 | fire:applied | 223 |  |  |  |
| naive | F-D-aa768995d4-unattributed-224 | fire:applied | 224 |  |  |  |
| naive | F-D-2da3374391-unattributed-224 | fire:applied | 224 |  |  |  |
| naive | F-D-7013cd82e7-unattributed-224 | fire:applied | 224 |  |  |  |
| naive | F-D-aa768995d4-anomaly0-224 | fire:applied | 224 |  |  |  |
| naive | F-D-2da3374391-anomaly0-224 | fire:applied | 224 |  |  |  |
| naive | F-D-7013cd82e7-anomaly0-224 | fire:applied | 224 |  |  |  |
| naive | F-D-a76732ecc8-unattributed-228 | fire:open | 228 |  |  |  |
| naive | F-D-774932d6f8-unattributed-228 | fire:open | 228 |  |  |  |
| naive | F-D-aa768995d4-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-2da3374391-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-237 | fire:open | 237 |  |  |  |
| naive | F-D-9975d472be-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-5112a1e669-unattributed-237 | fire:open | 237 |  |  |  |
| naive | F-D-124b284685-unattributed-237 | fire:open | 237 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-237 | fire:open | 237 |  |  |  |
| naive | D-9edb69b444 | admitted | 240 | 240 |  |  |
| naive | D-8a1cd63838 | admitted | 240 | 240 |  |  |
| naive | D-481fe1c5b5 | admitted | 240 | 240 |  |  |
| naive | D-625734ab25 | converged | 240 | 60 |  |  |
| naive | D-134e3a479f | converged | 240 | 120 |  |  |
| naive | D-2da3374391 | converged | 240 | 150 |  |  |
| naive | D-6e4155552b | converged | 240 | 150 |  |  |
| naive | D-7013cd82e7 | converged | 240 | 150 |  |  |
| naive | D-6cfae3beaa | converged | 240 | 180 |  |  |
| naive | D-324cc3d871 | converged | 240 | 180 |  |  |
| naive | F-D-481fe1c5b5-unattributed-241 | fire:open | 241 |  |  |  |
| naive | F-D-13ed32258f-unattributed-241 | fire:open | 241 |  |  |  |
| naive | F-D-0df0ef7a1d-unattributed-241 | fire:applied | 241 |  |  |  |
| naive | F-D-d43a0cd139-unattributed-245 | fire:applied | 245 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-245 | fire:open | 245 |  |  |  |
| naive | F-D-df7a1e3b89-unattributed-245 | fire:applied | 245 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-250 | fire:open | 250 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-251 | fire:open | 251 |  |  |  |
| naive | F-D-124b284685-unattributed-251 | fire:open | 251 |  |  |  |
| naive | F-D-9975d472be-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-aa768995d4-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-455a2f9731-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-0131cb944c-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-e0a0c38607-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-254 | fire:open | 254 |  |  |  |
| naive | F-D-aa768995d4-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-5112a1e669-unattributed-254 | fire:open | 254 |  |  |  |
| naive | F-D-455a2f9731-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-0131cb944c-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-124b284685-unattributed-254 | fire:open | 254 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-255 | fire:open | 255 |  |  |  |
| naive | F-D-124b284685-unattributed-255 | fire:open | 255 |  |  |  |
| naive | F-D-9975d472be-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-aa768995d4-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-455a2f9731-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-0131cb944c-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-e0a0c38607-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-aa768995d4-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-260 | fire:open | 260 |  |  |  |
| naive | F-D-0131cb944c-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-9975d472be-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-124b284685-unattributed-260 | fire:open | 260 |  |  |  |
| naive | F-D-5112a1e669-unattributed-260 | fire:open | 260 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-260 | fire:open | 260 |  |  |  |
| naive | F-D-e2987f79f5-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-13ed32258f-unattributed-264 | fire:open | 264 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-264 | fire:open | 264 |  |  |  |
| naive | F-D-011a0643a3-unattributed-264 | fire:applied | 264 |  |  |  |
| naive | F-D-3e54be5c09-unattributed-269 | fire:applied | 269 |  |  |  |
| naive | F-D-df7a1e3b89-unattributed-269 | fire:applied | 269 |  |  |  |
| naive | F-D-011a0643a3-unattributed-269 | fire:applied | 269 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-269 | fire:open | 269 |  |  |  |
| naive | F-D-c41d1820b5-unattributed-269 | fire:open | 269 |  |  |  |
| naive | D-d2ada920d6 | admitted | 270 | 270 |  |  |
| naive | D-20e22cab5e | admitted | 270 | 270 |  |  |
| naive | D-011a0643a3 | converged | 270 | 180 |  |  |
| naive | D-e2987f79f5 | converged | 270 | 60 |  |  |
| naive | D-9975d472be | converged | 270 | 210 |  |  |
| naive | D-92b4fc16af | converged | 270 | 240 |  |  |
| naive | D-f98b30ae88 | converged | 270 | 240 |  |  |
| naive | D-e966c99010 | converged | 270 | 270 |  |  |
| naive | F-D-f32c20567a-unattributed-270 | fire:applied | 270 |  |  |  |
| naive | F-D-612f19016d-unattributed-272 | fire:open | 272 |  |  |  |
| naive | F-D-df7a1e3b89-unattributed-273 | fire:applied | 273 |  |  |  |
| naive | F-D-d43a0cd139-unattributed-273 | fire:applied | 273 |  |  |  |
| naive | F-D-df7a1e3b89-anomaly0-273 | fire:applied | 273 |  |  |  |
| naive | F-D-d43a0cd139-anomaly0-273 | fire:applied | 273 |  |  |  |
| naive | F-D-f32c20567a-unattributed-276 | fire:applied | 276 |  |  |  |
| naive | F-D-f32c20567a-unattributed-277 | fire:applied | 277 |  |  |  |
| naive | F-D-9edb69b444-unattributed-278 | fire:open | 278 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-282 | fire:open | 282 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-283 | fire:open | 283 |  |  |  |
| naive | F-D-d43a0cd139-unattributed-283 | fire:applied | 283 |  |  |  |
| naive | F-D-df7a1e3b89-unattributed-283 | fire:applied | 283 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-283 | fire:open | 283 |  |  |  |
| naive | F-D-f32c20567a-unattributed-284 | fire:applied | 284 |  |  |  |
| naive | F-D-f32c20567a-unattributed-285 | fire:applied | 285 |  |  |  |
| naive | F-D-9edb69b444-unattributed-286 | fire:open | 286 |  |  |  |
| naive | F-D-f32c20567a-unattributed-286 | fire:applied | 286 |  |  |  |
| naive | F-D-77e4b829d0-unattributed-287 | fire:applied | 287 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-287 | fire:open | 287 |  |  |  |
| naive | F-D-ff675f9c69-unattributed-287 | fire:open | 287 |  |  |  |
| naive | F-D-8a1cd63838-unattributed-290 | fire:open | 290 |  |  |  |
| naive | F-D-6fd541346d-unattributed-290 | fire:open | 290 |  |  |  |
| naive | F-D-6fd541346d-unattributed-292 | fire:open | 292 |  |  |  |
| naive | F-D-b61059e3c9-unattributed-292 | fire:open | 292 |  |  |  |
| naive | F-D-d43a0cd139-unattributed-296 | fire:applied | 296 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-296 | fire:open | 296 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-296 | fire:open | 296 |  |  |  |
| naive | F-D-d43a0cd139-unattributed-298 | fire:applied | 298 |  |  |  |
| naive | F-D-13ed32258f-unattributed-298 | fire:open | 298 |  |  |  |
| naive | D-f6226a4df6 | admitted | 300 | 300 |  |  |
| naive | D-b85e3bf9b1 | admitted | 300 | 300 |  |  |
| naive | D-2bd79bf439 | admitted | 300 | 300 |  |  |
| naive | D-a5050cb656 | converged | 300 | 120 |  |  |
| naive | D-df7a1e3b89 | converged | 300 | 150 |  |  |
| naive | D-f605a68a82 | converged | 300 | 150 |  |  |
| naive | D-059d5eb032 | converged | 300 | 300 |  | Q5_revenue |
| naive | D-fc46ae7260 | converged | 300 | 60 |  |  |
| naive | D-cf1ea3f49d | converged | 300 | 120 |  |  |
| naive | D-dafd6a3c65 | converged | 300 | 150 |  |  |
| naive | F-D-aa768995d4-unattributed-300 | fire:applied | 300 |  |  |  |
| naive | F-D-455a2f9731-unattributed-300 | fire:applied | 300 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-300 | fire:open | 300 |  |  |  |
| naive | F-D-0131cb944c-unattributed-300 | fire:applied | 300 |  |  |  |
| naive | F-D-5112a1e669-unattributed-300 | fire:open | 300 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-300 | fire:applied | 300 |  |  |  |
| naive | F-D-124b284685-unattributed-300 | fire:open | 300 |  |  |  |
| naive | F-D-d2ada920d6-unattributed-300 | fire:open | 300 |  |  |  |
| naive | F-D-13ed32258f-unattributed-301 | fire:open | 301 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-301 | fire:open | 301 |  |  |  |
| naive | F-D-9d8240c2d4-unattributed-301 | fire:applied | 301 |  |  |  |
| naive | F-D-aa768995d4-unattributed-308 | fire:applied | 308 |  |  |  |
| naive | F-D-455a2f9731-unattributed-308 | fire:applied | 308 |  |  |  |
| naive | F-D-0131cb944c-unattributed-308 | fire:applied | 308 |  |  |  |
| naive | F-D-4f749a3469-unattributed-310 | fire:applied | 310 |  |  |  |
| naive | F-D-d43a0cd139-unattributed-310 | fire:applied | 310 |  |  |  |
| naive | F-D-f32c20567a-unattributed-311 | fire:applied | 311 |  |  |  |
| naive | F-D-aa768995d4-unattributed-314 | fire:applied | 314 |  |  |  |
| naive | F-D-455a2f9731-unattributed-314 | fire:applied | 314 |  |  |  |
| naive | F-D-0131cb944c-unattributed-314 | fire:applied | 314 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-315 | fire:open | 315 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-319 | fire:open | 319 |  |  |  |
| naive | F-D-b85e3bf9b1-unattributed-320 | fire:open | 320 |  |  |  |
| naive | F-D-f32c20567a-unattributed-322 | fire:applied | 322 |  |  |  |
| naive | F-D-f32c20567a-unattributed-324 | fire:applied | 324 |  |  |  |
| naive | F-D-f32c20567a-unattributed-325 | fire:applied | 325 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-325 | fire:open | 325 |  |  |  |
| naive | F-D-ff675f9c69-unattributed-325 | fire:open | 325 |  |  |  |
| naive | F-D-4634e8da0a-unattributed-325 | fire:applied | 325 |  |  |  |
| naive | F-D-b85e3bf9b1-unattributed-327 | fire:open | 327 |  |  |  |
| naive | F-D-d43a0cd139-unattributed-329 | fire:applied | 329 |  |  |  |
| naive | F-D-4f749a3469-unattributed-329 | fire:applied | 329 |  |  |  |
| naive | D-07be77ebcb | admitted | 330 | 330 |  |  |
| naive | D-bd467fdc7e | admitted | 330 | 330 |  |  |
| naive | D-4634e8da0a | converged | 330 | 30 |  |  |
| naive | D-aa768995d4 | converged | 330 | 210 |  |  |
| naive | D-d43a0cd139 | converged | 330 | 240 |  |  |
| naive | D-455a2f9731 | converged | 330 | 240 |  |  |
| naive | D-534405a26a | converged | 330 | 270 |  |  |
| naive | D-718cc6dd8d | converged | 330 | 270 |  |  |
| naive | D-73666836e8 | converged | 330 | 300 |  |  |
| naive | D-6ba59037ed | converged | 330 | 330 |  |  |
| naive | F-D-f32c20567a-unattributed-330 | fire:applied | 330 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-333 | fire:open | 333 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-339 | fire:open | 339 |  |  |  |
| naive | F-D-4f749a3469-unattributed-340 | fire:applied | 340 |  |  |  |
| naive | F-D-b6e3af94a4-unattributed-340 | fire:applied | 340 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-340 | fire:open | 340 |  |  |  |
| naive | F-D-b6e3af94a4-unattributed-342 | fire:applied | 342 |  |  |  |
| naive | F-D-4f749a3469-unattributed-342 | fire:applied | 342 |  |  |  |
| naive | F-D-f32c20567a-unattributed-343 | fire:applied | 343 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-344 | fire:open | 344 |  |  |  |
| naive | F-D-f32c20567a-unattributed-347 | fire:applied | 347 |  |  |  |
| naive | F-D-f32c20567a-unattributed-348 | fire:applied | 348 |  |  |  |
| naive | F-D-3e0cd59348-unattributed-348 | fire:applied | 348 |  |  |  |
| naive | F-D-b6e3af94a4-unattributed-351 | fire:applied | 351 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-351 | fire:open | 351 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-351 | fire:open | 351 |  |  |  |
| naive | F-D-f32c20567a-unattributed-355 | fire:applied | 355 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-357 | fire:open | 357 |  |  |  |
| naive | F-D-5112a1e669-unattributed-357 | fire:open | 357 |  |  |  |
| naive | F-D-91967bcb5e-unattributed-357 | fire:applied | 357 |  |  |  |
| naive | F-D-3734c59906-unattributed-357 | fire:applied | 357 |  |  |  |
| naive | F-D-0131cb944c-unattributed-357 | fire:applied | 357 |  |  |  |
| naive | D-d28d851a56 | admitted | 360 | 360 |  |  |
| naive | D-b288e46eb5 | converged | 360 | 330 |  |  |
| naive | D-3e54be5c09 | converged | 360 | 90 |  |  |
| naive | D-52583961cc | converged | 360 | 150 |  |  |
| naive | D-30573e9930 | converged | 360 | 300 |  |  |
| naive | F-D-91967bcb5e-unattributed-360 | fire:applied | 360 |  |  |  |
| naive | F-D-0131cb944c-unattributed-360 | fire:applied | 360 |  |  |  |
| naive | F-D-f32c20567a-unattributed-361 | fire:applied | 361 |  |  |  |
| naive | F-D-3e0cd59348-unattributed-361 | fire:applied | 361 |  |  |  |
| naive | F-D-2f9637133f-unattributed-362 | fire:open | 362 |  |  |  |
| naive | F-D-481fe1c5b5-unattributed-362 | fire:open | 362 |  |  |  |
| naive | F-D-13ed32258f-unattributed-362 | fire:open | 362 |  |  |  |
| naive | F-D-0df0ef7a1d-unattributed-362 | fire:applied | 362 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-365 | fire:open | 365 |  |  |  |
| naive | F-D-83a7ffc93f-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-9c34737739-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-124b284685-unattributed-365 | fire:open | 365 |  |  |  |
| naive | F-D-d2ada920d6-unattributed-365 | fire:open | 365 |  |  |  |
| naive | F-D-91967bcb5e-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-0131cb944c-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-f32c20567a-unattributed-373 | fire:applied | 373 |  |  |  |
| naive | F-D-a76732ecc8-unattributed-374 | fire:open | 374 |  |  |  |
| naive | F-D-612f19016d-unattributed-374 | fire:open | 374 |  |  |  |
| naive | F-D-07be77ebcb-unattributed-375 | fire:open | 375 |  |  |  |
| naive | F-D-c9d5a80ab5-unattributed-375 | fire:applied | 375 |  |  |  |
| naive | F-D-f32c20567a-unattributed-378 | fire:applied | 378 |  |  |  |
| naive | F-D-f32c20567a-unattributed-380 | fire:applied | 380 |  |  |  |
| naive | F-D-f32c20567a-unattributed-381 | fire:applied | 381 |  |  |  |
| naive | F-D-b6e3af94a4-unattributed-384 | fire:applied | 384 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-384 | fire:open | 384 |  |  |  |
| naive | F-D-13ed32258f-unattributed-384 | fire:open | 384 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-384 | fire:open | 384 |  |  |  |
| naive | F-D-f32c20567a-unattributed-385 | fire:applied | 385 |  |  |  |
| naive | F-D-b61059e3c9-unattributed-386 | fire:open | 386 |  |  |  |
| naive | F-D-8a1cd63838-unattributed-386 | fire:open | 386 |  |  |  |
| naive | F-D-7c4f9e4f3b-unattributed-388 | fire:applied | 388 |  |  |  |
| naive | F-D-edec23a128-unattributed-388 | fire:applied | 388 |  |  |  |
| naive | F-D-9d8240c2d4-unattributed-388 | fire:applied | 388 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-388 | fire:open | 388 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-388 | fire:open | 388 |  |  |  |
| naive | D-63de7c2e3b | admitted | 390 | 390 |  |  |
| naive | D-1e864e79dd | admitted | 390 | 390 |  |  |
| naive | D-d41e927a49 | admitted | 390 | 390 |  |  |
| naive | D-79bd0538b0 | admitted | 390 | 390 |  | Q5_revenue |
| naive | D-9c34737739 | converged | 390 | 360 |  |  |
| naive | D-b6e3af94a4 | converged | 390 | 330 |  |  |
| naive | D-7c4f9e4f3b | converged | 390 | 360 |  |  |
| naive | D-edec23a128 | converged | 390 | 360 |  |  |
| naive | F-D-f32c20567a-unattributed-390 | fire:applied | 390 |  |  |  |
| naive | F-D-08574335ce-unattributed-391 | fire:applied | 391 |  |  |  |
| naive | F-D-e311127aa6-unattributed-391 | fire:applied | 391 |  |  |  |
| naive | F-D-494211a406-unattributed-391 | fire:applied | 391 |  |  |  |
| naive | F-D-9d8240c2d4-unattributed-391 | fire:applied | 391 |  |  |  |
| naive | F-D-f32c20567a-unattributed-393 | fire:applied | 393 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-395 | fire:open | 395 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-395 | fire:open | 395 |  |  |  |
| naive | F-D-83a7ffc93f-unattributed-395 | fire:applied | 395 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-395 | fire:applied | 395 |  |  |  |
| naive | F-D-124b284685-unattributed-395 | fire:open | 395 |  |  |  |
| naive | F-D-d2ada920d6-unattributed-395 | fire:open | 395 |  |  |  |
| naive | F-D-0131cb944c-unattributed-395 | fire:applied | 395 |  |  |  |
| naive | F-D-d9e8ec7663-unattributed-395 | fire:applied | 395 |  |  |  |
| naive | F-D-0131cb944c-unattributed-402 | fire:applied | 402 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-402 | fire:open | 402 |  |  |  |
| naive | F-D-d9e8ec7663-unattributed-402 | fire:applied | 402 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-402 | fire:applied | 402 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-402 | fire:open | 402 |  |  |  |
| naive | F-D-83a7ffc93f-unattributed-402 | fire:applied | 402 |  |  |  |
| naive | F-D-124b284685-unattributed-402 | fire:open | 402 |  |  |  |
| naive | F-D-5112a1e669-unattributed-402 | fire:open | 402 |  |  |  |
| naive | F-D-3734c59906-unattributed-403 | fire:applied | 403 |  |  |  |
| naive | F-D-0131cb944c-unattributed-403 | fire:applied | 403 |  |  |  |
| naive | F-D-d9e8ec7663-unattributed-403 | fire:applied | 403 |  |  |  |
| naive | F-D-124b284685-unattributed-403 | fire:open | 403 |  |  |  |
| naive | F-D-08574335ce-unattributed-404 | fire:applied | 404 |  |  |  |
| naive | F-D-b77654dd64-unattributed-404 | fire:applied | 404 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-404 | fire:open | 404 |  |  |  |
| naive | F-D-13ed32258f-unattributed-404 | fire:open | 404 |  |  |  |
| naive | F-D-f32c20567a-unattributed-405 | fire:applied | 405 |  |  |  |
| naive | F-D-3e0cd59348-unattributed-405 | fire:applied | 405 |  |  |  |
| naive | F-D-f32c20567a-unattributed-406 | fire:applied | 406 |  |  |  |
| naive | F-D-08574335ce-unattributed-407 | fire:applied | 407 |  |  |  |
| naive | F-D-e311127aa6-unattributed-407 | fire:applied | 407 |  |  |  |
| naive | F-D-494211a406-unattributed-407 | fire:applied | 407 |  |  |  |
| naive | F-D-b77654dd64-unattributed-407 | fire:applied | 407 |  |  |  |
| naive | F-D-9d8240c2d4-unattributed-407 | fire:applied | 407 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-407 | fire:open | 407 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-407 | fire:open | 407 |  |  |  |
| naive | F-D-f32c20567a-unattributed-409 | fire:applied | 409 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-409 | fire:open | 409 |  |  |  |
| naive | F-D-0131cb944c-unattributed-416 | fire:applied | 416 |  |  |  |
| naive | F-D-d9e8ec7663-unattributed-416 | fire:applied | 416 |  |  |  |
| naive | D-a7743b85de | admitted | 420 | 420 |  |  |
| naive | D-b515f08061 | admitted | 420 | 420 |  |  |
| naive | D-39fce54a96 | converged | 420 | 210 |  |  |
| naive | D-0131cb944c | converged | 420 | 240 |  |  |
| naive | D-1b610ad439 | converged | 420 | 270 |  |  |
| naive | D-55e64f00c2 | converged | 420 | 270 |  |  |
| naive | D-3734c59906 | converged | 420 | 330 |  |  |
| naive | D-e57bec8fa0 | converged | 420 | 420 |  |  |
| naive | D-4378514f1f | moot | 420 | 120 |  |  |
| naive | F-D-91967bcb5e-unattributed-422 | fire:applied | 422 |  |  |  |
| naive | F-D-d9e8ec7663-unattributed-422 | fire:applied | 422 |  |  |  |
| naive | F-D-6fd541346d-unattributed-423 | fire:open | 423 |  |  |  |
| naive | F-D-e55aeaea90-unattributed-423 | fire:applied | 423 |  |  |  |
| naive | F-D-6fd541346d-unattributed-426 | fire:open | 426 |  |  |  |
| naive | F-D-e55aeaea90-unattributed-426 | fire:applied | 426 |  |  |  |
| naive | F-D-f32c20567a-unattributed-428 | fire:applied | 428 |  |  |  |
| naive | F-D-08574335ce-unattributed-430 | fire:applied | 430 |  |  |  |
| naive | F-D-b77654dd64-unattributed-430 | fire:applied | 430 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-430 | fire:open | 430 |  |  |  |
| naive | F-D-13ed32258f-unattributed-430 | fire:open | 430 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-431 | fire:open | 431 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-432 | fire:open | 432 |  |  |  |
| naive | F-D-f32c20567a-unattributed-434 | fire:applied | 434 |  |  |  |
| naive | F-D-f32c20567a-unattributed-436 | fire:applied | 436 |  |  |  |
| naive | F-D-b85e3bf9b1-unattributed-437 | fire:open | 437 |  |  |  |
| naive | F-D-f32c20567a-unattributed-441 | fire:applied | 441 |  |  |  |
| naive | F-D-4f749a3469-unattributed-443 | fire:applied | 443 |  |  |  |
| naive | F-D-08574335ce-unattributed-443 | fire:applied | 443 |  |  |  |
| naive | F-D-494211a406-unattributed-443 | fire:applied | 443 |  |  |  |
| naive | F-D-e311127aa6-unattributed-443 | fire:applied | 443 |  |  |  |
| naive | F-D-9d8240c2d4-unattributed-443 | fire:applied | 443 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-443 | fire:open | 443 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-443 | fire:open | 443 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-445 | fire:open | 445 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-445 | fire:open | 445 |  |  |  |
| naive | F-D-83a7ffc93f-unattributed-445 | fire:applied | 445 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-445 | fire:applied | 445 |  |  |  |
| naive | F-D-124b284685-unattributed-445 | fire:open | 445 |  |  |  |
| naive | F-D-d2ada920d6-unattributed-445 | fire:open | 445 |  |  |  |
| naive | F-D-91967bcb5e-unattributed-445 | fire:applied | 445 |  |  |  |
| naive | F-D-d9e8ec7663-unattributed-445 | fire:applied | 445 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-446 | fire:open | 446 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-448 | fire:open | 448 |  |  |  |
| naive | D-19066ba77a | admitted | 450 | 450 |  |  |
| naive | D-0fea7fc2d1 | converged | 450 | 330 |  |  |
| naive | D-f467670b0c | converged | 450 | 420 |  |  |
| naive | D-83a7ffc93f | converged | 450 | 330 |  |  |
| naive | D-c9d5a80ab5 | converged | 450 | 360 |  |  |
| naive | D-d9e8ec7663 | converged | 450 | 390 |  |  |
| naive | F-D-f32c20567a-unattributed-451 | fire:applied | 451 |  |  |  |
| naive | F-D-481fe1c5b5-unattributed-453 | fire:open | 453 |  |  |  |
| naive | F-D-348482f9db-unattributed-453 | fire:applied | 453 |  |  |  |
| naive | F-D-13ed32258f-unattributed-453 | fire:open | 453 |  |  |  |
| naive | F-D-0df0ef7a1d-unattributed-453 | fire:applied | 453 |  |  |  |
| naive | F-D-08574335ce-unattributed-454 | fire:applied | 454 |  |  |  |
| naive | F-D-19066ba77a-unattributed-454 | fire:open | 454 |  |  |  |
| naive | F-D-b77654dd64-unattributed-454 | fire:applied | 454 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-454 | fire:open | 454 |  |  |  |
| naive | F-D-13ed32258f-unattributed-454 | fire:open | 454 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-458 | fire:open | 458 |  |  |  |
| naive | F-D-a56e2d31d2-unattributed-458 | fire:applied | 458 |  |  |  |
| naive | F-D-5112a1e669-unattributed-458 | fire:open | 458 |  |  |  |
| naive | F-D-91967bcb5e-unattributed-458 | fire:applied | 458 |  |  |  |
| naive | F-D-16e3c5e645-unattributed-458 | fire:applied | 458 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-458 | fire:applied | 458 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-458 | fire:open | 458 |  |  |  |
| naive | F-D-124b284685-unattributed-458 | fire:open | 458 |  |  |  |
| naive | F-D-f379da9a1e-anomaly0-458 | fire:open | 458 |  |  |  |
| naive | F-D-a56e2d31d2-anomaly0-458 | fire:applied | 458 |  |  |  |
| naive | F-D-5112a1e669-anomaly0-458 | fire:open | 458 |  |  |  |
| naive | F-D-91967bcb5e-anomaly0-458 | fire:applied | 458 |  |  |  |
| naive | F-D-16e3c5e645-anomaly0-458 | fire:applied | 458 |  |  |  |
| naive | F-D-6bf0d59ca8-anomaly0-458 | fire:applied | 458 |  |  |  |
| naive | F-D-63de7c2e3b-anomaly0-458 | fire:open | 458 |  |  |  |
| naive | F-D-124b284685-anomaly0-458 | fire:open | 458 |  |  |  |
| naive | F-D-f32c20567a-unattributed-461 | fire:applied | 461 |  |  |  |
| naive | F-D-08574335ce-unattributed-467 | fire:applied | 467 |  |  |  |
| naive | F-D-19066ba77a-unattributed-467 | fire:open | 467 |  |  |  |
| naive | F-D-b77654dd64-unattributed-467 | fire:applied | 467 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-467 | fire:open | 467 |  |  |  |
| naive | F-D-13ed32258f-unattributed-467 | fire:open | 467 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-467 | fire:open | 467 |  |  |  |
| naive | F-D-08574335ce-unattributed-470 | fire:applied | 470 |  |  |  |
| naive | F-D-19066ba77a-unattributed-470 | fire:open | 470 |  |  |  |
| naive | F-D-b77654dd64-unattributed-470 | fire:applied | 470 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-470 | fire:open | 470 |  |  |  |
| naive | F-D-13ed32258f-unattributed-470 | fire:open | 470 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-470 | fire:open | 470 |  |  |  |
| naive | F-D-08574335ce-unattributed-471 | fire:applied | 471 |  |  |  |
| naive | F-D-19066ba77a-unattributed-471 | fire:open | 471 |  |  |  |
| naive | F-D-b77654dd64-unattributed-471 | fire:applied | 471 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-471 | fire:open | 471 |  |  |  |
| naive | F-D-13ed32258f-unattributed-471 | fire:open | 471 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-471 | fire:open | 471 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-478 | fire:open | 478 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-478 | fire:open | 478 |  |  |  |
| naive | F-D-16e3c5e645-unattributed-478 | fire:applied | 478 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-478 | fire:applied | 478 |  |  |  |
| naive | F-D-124b284685-unattributed-478 | fire:open | 478 |  |  |  |
| naive | F-D-d2ada920d6-unattributed-478 | fire:open | 478 |  |  |  |
| naive | F-D-a56e2d31d2-unattributed-478 | fire:applied | 478 |  |  |  |
| naive | D-84260f51a8 | admitted | 480 | 480 |  |  |
| naive | D-6f138aedfe | admitted | 480 | 480 |  |  |
| naive | D-4697772679 | admitted | 480 | 480 |  |  |
| naive | D-219094225a | admitted | 480 | 480 |  |  |
| naive | D-61fd9c6c43 | converged | 480 | 450 |  |  |
| naive | F-D-b85e3bf9b1-unattributed-481 | fire:open | 481 |  |  |  |
| naive | F-D-4f749a3469-unattributed-482 | fire:applied | 482 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-482 | fire:open | 482 |  |  |  |
| naive | F-D-494211a406-unattributed-482 | fire:applied | 482 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-482 | fire:open | 482 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-487 | fire:open | 487 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-487 | fire:open | 487 |  |  |  |
| naive | F-D-16e3c5e645-unattributed-487 | fire:applied | 487 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-487 | fire:applied | 487 |  |  |  |
| naive | F-D-124b284685-unattributed-487 | fire:open | 487 |  |  |  |
| naive | F-D-d2ada920d6-unattributed-487 | fire:open | 487 |  |  |  |
| naive | F-D-a56e2d31d2-unattributed-487 | fire:applied | 487 |  |  |  |
| naive | F-D-84260f51a8-unattributed-487 | fire:open | 487 |  |  |  |
| naive | F-D-f32c20567a-unattributed-489 | fire:applied | 489 |  |  |  |
| naive | F-D-b85e3bf9b1-unattributed-490 | fire:open | 490 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-492 | fire:open | 492 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-493 | fire:open | 493 |  |  |  |
| naive | F-D-13ed32258f-unattributed-493 | fire:open | 493 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-493 | fire:open | 493 |  |  |  |
| naive | F-D-f32c20567a-unattributed-494 | fire:applied | 494 |  |  |  |
| naive | F-D-08574335ce-unattributed-495 | fire:applied | 495 |  |  |  |
| naive | F-D-19066ba77a-unattributed-495 | fire:open | 495 |  |  |  |
| naive | F-D-b77654dd64-unattributed-495 | fire:applied | 495 |  |  |  |
| naive | F-D-ed3e9851df-unattributed-495 | fire:open | 495 |  |  |  |
| naive | F-D-13ed32258f-unattributed-495 | fire:open | 495 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-497 | fire:open | 497 |  |  |  |
| naive | F-D-494211a406-unattributed-497 | fire:applied | 497 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-497 | fire:open | 497 |  |  |  |
| naive | F-D-f32c20567a-unattributed-498 | fire:applied | 498 |  |  |  |
| naive | F-D-a56e2d31d2-unattributed-502 | fire:applied | 502 |  |  |  |
| naive | F-D-124b284685-unattributed-502 | fire:open | 502 |  |  |  |
| naive | F-D-f32c20567a-unattributed-503 | fire:applied | 503 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-504 | fire:open | 504 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-505 | fire:open | 505 |  |  |  |
| naive | F-D-6fd541346d-unattributed-506 | fire:open | 506 |  |  |  |
| naive | F-D-e55aeaea90-unattributed-506 | fire:applied | 506 |  |  |  |
| naive | F-D-2f9637133f-unattributed-507 | fire:open | 507 |  |  |  |
| naive | F-D-481fe1c5b5-unattributed-507 | fire:open | 507 |  |  |  |
| naive | F-D-348482f9db-unattributed-507 | fire:applied | 507 |  |  |  |
| naive | F-D-13ed32258f-unattributed-507 | fire:open | 507 |  |  |  |
| naive | F-D-0df0ef7a1d-unattributed-507 | fire:applied | 507 |  |  |  |
| naive | F-D-f32c20567a-unattributed-509 | fire:applied | 509 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-509 | fire:open | 509 |  |  |  |
| naive | D-644c34deb0 | admitted | 510 | 510 |  |  |
| naive | D-93d4c8a6f5 | admitted | 510 | 510 |  |  |
| naive | D-359d1fc7ad | admitted | 510 | 510 |  | Q3_soft_delete |
| naive | D-5410e662d1 | admitted | 510 | 510 |  |  |
| naive | D-eef1deef30 | admitted | 510 | 510 |  |  |
| naive | D-5a68928ca1 | admitted | 510 | 510 |  |  |
| naive | D-4f749a3469 | converged | 510 | 300 |  |  |
| naive | D-efafeef37d | converged | 510 | 450 |  | Q3_soft_delete |
| naive | D-494211a406 | converged | 510 | 360 |  |  |
| naive | D-08574335ce | converged | 510 | 390 |  |  |
| naive | D-b77654dd64 | converged | 510 | 390 |  |  |
| naive | D-cf90409671 | converged | 510 | 450 |  |  |
| naive | D-16e3c5e645 | converged | 510 | 450 |  |  |
| naive | D-5ca0de397b | moot | 510 | 30 |  | P1_claire_rounding |
| naive | D-72ffaad73a | moot | 510 | 180 |  |  |
| naive | D-958ed6fdfe | moot | 510 | 180 |  |  |
| naive | F-D-6f138aedfe-unattributed-510 | fire:open | 510 |  |  |  |
| naive | F-D-2965a753c6-unattributed-510 | fire:applied | 510 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-510 | fire:open | 510 |  |  |  |
| naive | F-D-6fd541346d-unattributed-513 | fire:open | 513 |  |  |  |
| naive | F-D-e55aeaea90-unattributed-513 | fire:applied | 513 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-515 | fire:open | 515 |  |  |  |
| naive | F-D-2965a753c6-unattributed-515 | fire:applied | 515 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-515 | fire:open | 515 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-517 | fire:open | 517 |  |  |  |
| naive | F-D-2965a753c6-unattributed-517 | fire:applied | 517 |  |  |  |
| naive | F-D-13ed32258f-unattributed-517 | fire:open | 517 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-517 | fire:open | 517 |  |  |  |
| naive | F-D-84260f51a8-unattributed-518 | fire:open | 518 |  |  |  |
| naive | F-D-a56e2d31d2-unattributed-518 | fire:applied | 518 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-518 | fire:open | 518 |  |  |  |
| naive | F-D-05e0b400d7-unattributed-518 | fire:applied | 518 |  |  |  |
| naive | F-D-6bf0d59ca8-unattributed-518 | fire:applied | 518 |  |  |  |
| naive | F-D-5112a1e669-unattributed-518 | fire:open | 518 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-518 | fire:open | 518 |  |  |  |
| naive | F-D-124b284685-unattributed-518 | fire:open | 518 |  |  |  |
| naive | F-D-84260f51a8-anomaly0-518 | fire:open | 518 |  |  |  |
| naive | F-D-a56e2d31d2-anomaly0-518 | fire:applied | 518 |  |  |  |
| naive | F-D-f379da9a1e-anomaly0-518 | fire:open | 518 |  |  |  |
| naive | F-D-05e0b400d7-anomaly0-518 | fire:applied | 518 |  |  |  |
| naive | F-D-6bf0d59ca8-anomaly0-518 | fire:applied | 518 |  |  |  |
| naive | F-D-5112a1e669-anomaly0-518 | fire:open | 518 |  |  |  |
| naive | F-D-63de7c2e3b-anomaly0-518 | fire:open | 518 |  |  |  |
| naive | F-D-124b284685-anomaly0-518 | fire:open | 518 |  |  |  |
| naive | F-D-2f9637133f-unattributed-522 | fire:open | 522 |  |  |  |
| naive | F-D-481fe1c5b5-unattributed-522 | fire:open | 522 |  |  |  |
| naive | F-D-348482f9db-unattributed-522 | fire:applied | 522 |  |  |  |
| naive | F-D-13ed32258f-unattributed-522 | fire:open | 522 |  |  |  |
| naive | F-D-0df0ef7a1d-unattributed-522 | fire:applied | 522 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-523 | fire:open | 523 |  |  |  |
| naive | F-D-2965a753c6-unattributed-523 | fire:applied | 523 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-523 | fire:open | 523 |  |  |  |
| naive | F-D-93d4c8a6f5-unattributed-524 | fire:open | 524 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-524 | fire:open | 524 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-527 | fire:open | 527 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-527 | fire:open | 527 |  |  |  |
| naive | F-D-2965a753c6-unattributed-527 | fire:applied | 527 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-527 | fire:open | 527 |  |  |  |
| naive | F-D-481fe1c5b5-unattributed-528 | fire:open | 528 |  |  |  |
| naive | F-D-348482f9db-unattributed-528 | fire:applied | 528 |  |  |  |
| naive | F-D-13ed32258f-unattributed-528 | fire:open | 528 |  |  |  |
| naive | F-D-0df0ef7a1d-unattributed-528 | fire:applied | 528 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-530 | fire:open | 530 |  |  |  |
| naive | F-D-2965a753c6-unattributed-530 | fire:applied | 530 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-530 | fire:open | 530 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-532 | fire:open | 532 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-532 | fire:open | 532 |  |  |  |
| naive | F-D-2965a753c6-unattributed-532 | fire:applied | 532 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-532 | fire:open | 532 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-533 | fire:open | 533 |  |  |  |
| naive | F-D-2965a753c6-unattributed-533 | fire:applied | 533 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-533 | fire:open | 533 |  |  |  |
| naive | F-D-6fd541346d-unattributed-535 | fire:open | 535 |  |  |  |
| naive | F-D-e55aeaea90-unattributed-535 | fire:applied | 535 |  |  |  |
| naive | F-D-f32c20567a-unattributed-537 | fire:applied | 537 |  |  |  |
| naive | F-D-dd4ba69cd5-unattributed-537 | fire:open | 537 |  |  |  |
| naive | F-D-b85e3bf9b1-unattributed-539 | fire:open | 539 |  |  |  |
| naive | D-746f62b3d5 | admitted | 540 | 540 |  |  |
| naive | D-47ab72f9b1 | admitted | 540 | 540 |  |  |
| naive | D-1c8059e917 | admitted | 540 | 540 |  |  |
| naive | D-1172ffc26a | admitted | 540 | 540 |  |  |
| naive | D-8e3497b188 | admitted | 540 | 540 |  |  |
| naive | D-11358304ec | admitted | 540 | 540 |  |  |
| naive | D-3e0cd59348 | converged | 540 | 90 |  | P1_claire_rounding |
| naive | D-f32c20567a | converged | 540 | 270 |  |  |
| naive | D-e0a0c38607 | converged | 540 | 60 |  |  |
| naive | D-0df0ef7a1d | converged | 540 | 210 |  |  |
| naive | D-9d8240c2d4 | converged | 540 | 270 |  |  |
| naive | D-6bf0d59ca8 | converged | 540 | 270 |  |  |
| naive | D-488a3c45d6 | converged | 540 | 330 |  |  |
| naive | D-832280b537 | moot | 540 | 90 |  |  |
| naive | F-D-6fd541346d-unattributed-544 | fire:open | 544 |  |  |  |
| naive | F-D-e55aeaea90-unattributed-544 | fire:applied | 544 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-545 | fire:open | 545 |  |  |  |
| naive | F-D-2965a753c6-unattributed-545 | fire:applied | 545 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-545 | fire:open | 545 |  |  |  |
| naive | F-D-93d4c8a6f5-unattributed-546 | fire:open | 546 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-549 | fire:open | 549 |  |  |  |
| naive | F-D-2965a753c6-unattributed-549 | fire:applied | 549 |  |  |  |
| naive | F-D-b85e3bf9b1-unattributed-550 | fire:open | 550 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-553 | fire:open | 553 |  |  |  |
| naive | F-D-2965a753c6-unattributed-553 | fire:applied | 553 |  |  |  |
| naive | F-D-13ed32258f-unattributed-553 | fire:open | 553 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-553 | fire:open | 553 |  |  |  |
| naive | F-D-5112a1e669-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-84260f51a8-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-b61059e3c9-unattributed-556 | fire:open | 556 |  |  |  |
| naive | F-D-8a1cd63838-unattributed-556 | fire:open | 556 |  |  |  |
| naive | F-D-e55aeaea90-unattributed-556 | fire:applied | 556 |  |  |  |
| naive | F-D-f379da9a1e-unattributed-558 | fire:open | 558 |  |  |  |
| naive | F-D-84260f51a8-unattributed-558 | fire:open | 558 |  |  |  |
| naive | F-D-a56e2d31d2-unattributed-558 | fire:applied | 558 |  |  |  |
| naive | F-D-5112a1e669-unattributed-558 | fire:open | 558 |  |  |  |
| naive | F-D-91967bcb5e-unattributed-558 | fire:applied | 558 |  |  |  |
| naive | F-D-05e0b400d7-unattributed-558 | fire:applied | 558 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-558 | fire:open | 558 |  |  |  |
| naive | F-D-124b284685-unattributed-558 | fire:open | 558 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-560 | fire:open | 560 |  |  |  |
| naive | F-D-2965a753c6-unattributed-560 | fire:applied | 560 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-560 | fire:open | 560 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-565 | fire:open | 565 |  |  |  |
| naive | F-D-2965a753c6-unattributed-565 | fire:applied | 565 |  |  |  |
| naive | F-D-93d4c8a6f5-unattributed-567 | fire:open | 567 |  |  |  |
| naive | F-D-b85e3bf9b1-unattributed-569 | fire:open | 569 |  |  |  |
| naive | D-993dda5749 | admitted | 570 | 570 |  | P1_claire_rounding |
| naive | D-aabe6b73b3 | admitted | 570 | 570 |  |  |
| naive | D-9b3d787e02 | admitted | 570 | 570 |  |  |
| naive | D-32dc16249b | admitted | 570 | 570 |  |  |
| naive | D-1921c26346 | admitted | 570 | 570 |  |  |
| naive | D-faff8e84ef | admitted | 570 | 570 |  |  |
| naive | D-7d496cff7b | admitted | 570 | 570 |  |  |
| naive | D-d9d14a5745 | admitted | 570 | 570 |  |  |
| naive | D-bd8f04bb75 | admitted | 570 | 570 |  |  |
| naive | D-4fc03d98d3 | converged | 570 | 120 |  | P1_claire_rounding |
| naive | D-70e8a90653 | converged | 570 | 540 |  | P1_claire_rounding |
| naive | D-d29ba6239a | converged | 570 | 570 |  | P1_claire_rounding |
| naive | D-e55aeaea90 | converged | 570 | 420 |  |  |
| naive | D-936cdc9ded | converged | 570 | 540 |  |  |
| naive | D-e311127aa6 | converged | 570 | 390 |  |  |
| naive | D-348482f9db | converged | 570 | 420 |  |  |
| naive | D-a56e2d31d2 | converged | 570 | 450 |  |  |
| naive | D-09f0e5cbeb | converged | 570 | 450 |  |  |
| naive | D-a380087445 | converged | 570 | 480 |  |  |
| naive | D-2965a753c6 | converged | 570 | 510 |  |  |
| naive | D-c41d1820b5 | moot | 570 | 240 |  |  |
| naive | D-d744ae0d71 | moot | 570 | 270 |  |  |
| naive | F-D-2f9637133f-unattributed-570 | fire:open | 570 |  |  |  |
| naive | F-D-481fe1c5b5-unattributed-570 | fire:open | 570 |  |  |  |
| naive | F-D-47ab72f9b1-unattributed-570 | fire:open | 570 |  |  |  |
| naive | F-D-13ed32258f-unattributed-570 | fire:open | 570 |  |  |  |
| naive | F-D-93d4c8a6f5-unattributed-572 | fire:open | 572 |  |  |  |
| naive | F-D-77e6d11b27-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-63de7c2e3b-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-11358304ec-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-124b284685-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-d2ada920d6-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-05e0b400d7-unattributed-575 | fire:applied | 575 |  |  |  |
| naive | F-D-9599b9fc73-unattributed-575 | fire:applied | 575 |  |  |  |
| naive | F-D-91967bcb5e-unattributed-575 | fire:applied | 575 |  |  |  |
| naive | F-D-93d4c8a6f5-unattributed-580 | fire:open | 580 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-588 | fire:open | 588 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-588 | fire:open | 588 |  |  |  |
| naive | F-D-2ed34b3974-unattributed-592 | fire:open | 592 |  |  |  |
| naive | F-D-a7743b85de-unattributed-593 | fire:open | 593 |  |  |  |
| naive | F-D-9599b9fc73-unattributed-593 | fire:applied | 593 |  |  |  |
| naive | F-D-0ab6f958fe-unattributed-597 | fire:open | 597 |  |  |  |
| naive | F-D-6f138aedfe-unattributed-597 | fire:open | 597 |  |  |  |
| naive | F-D-20e22cab5e-unattributed-597 | fire:open | 597 |  |  |  |
| naive | F-D-2f9637133f-unattributed-599 | fire:open | 599 |  |  |  |
| naive | F-D-47ab72f9b1-unattributed-599 | fire:open | 599 |  |  |  |
| naive | F-D-481fe1c5b5-unattributed-599 | fire:open | 599 |  |  |  |
| naive | F-D-13ed32258f-unattributed-599 | fire:open | 599 |  |  |  |
| naive | F-D-32dc16249b-unattributed-599 | fire:open | 599 |  |  |  |
| naive | D-46463b6024 | admitted | 600 | 600 |  | P1_claire_rounding |
| naive | D-e310b13dc8 | admitted | 600 | 600 |  | Q3_soft_delete |
| naive | D-0cacfc414c | admitted | 600 | 600 |  |  |
| naive | D-5fec30ab9f | admitted | 600 | 600 |  |  |
| naive | D-03bb8f5a24 | admitted | 600 | 600 |  |  |
| naive | D-f0b4d66baf | admitted | 600 | 600 |  |  |
| naive | D-c46b73040d | converged | 600 | 570 |  | P1_claire_rounding |
| naive | D-77e4b829d0 | converged | 600 | 180 |  |  |
| naive | D-91967bcb5e | converged | 600 | 330 |  |  |
| naive | D-05e0b400d7 | converged | 600 | 510 |  |  |
| naive | D-9599b9fc73 | converged | 600 | 570 |  |  |
| naive | D-522dda3257 | moot | 600 | 300 |  |  |
| self_ref | D-ab10f09e13 | admitted | 30 | 30 |  |  |
| self_ref | D-aff8b960df | admitted | 30 | 30 |  |  |
| self_ref | D-40bfe4dca2 | admitted | 30 | 30 |  |  |
| self_ref | D-957adaa9b7 | admitted | 30 | 30 |  |  |
| self_ref | D-76d69df076 | admitted | 30 | 30 |  |  |
| self_ref | D-577af3f881 | admitted | 30 | 30 |  |  |
| self_ref | D-6131d16d10 | converged | 30 | 30 |  |  |
| self_ref | D-422971bd91 | admitted | 60 | 60 |  |  |
| self_ref | D-c46eb84b03 | converged | 60 | 60 |  |  |
| self_ref | F-D-957adaa9b7-anomaly0-70 | fire:open | 70 |  |  |  |
| self_ref | F-D-ab10f09e13-anomaly0-70 | fire:open | 70 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-70 | fire:open | 70 |  |  |  |
| self_ref | F-D-c5da5d7229-anomaly0-70 | fire:open | 70 |  |  |  |
| self_ref | D-fa9cb0c040 | admitted | 90 | 90 |  |  |
| self_ref | D-ed58e25b15 | admitted | 90 | 90 |  |  |
| self_ref | D-a561349715 | admitted | 90 | 90 |  |  |
| self_ref | D-525421eb38 | admitted | 90 | 90 |  |  |
| self_ref | D-ce7d1fd453 | admitted | 90 | 90 |  |  |
| self_ref | D-c6939981f3 | converged | 90 | 30 |  |  |
| self_ref | D-06cca8bfe5 | converged | 90 | 30 |  |  |
| self_ref | D-05343161fc | converged | 90 | 60 |  |  |
| self_ref | D-9237c08413 | converged | 90 | 60 |  |  |
| self_ref | D-b67c1e45da | converged | 90 | 90 |  |  |
| self_ref | D-c5801b208b | converged | 90 | 90 |  |  |
| self_ref | D-562b1d7906 | converged | 90 | 90 |  |  |
| self_ref | F-D-fe138b9df7-anomaly0-91 | fire:applied | 91 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-91 | fire:open | 91 |  |  |  |
| self_ref | F-D-c5da5d7229-anomaly0-98 | fire:open | 98 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-98 | fire:open | 98 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-100 | fire:open | 100 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-100 | fire:open | 100 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-100 | fire:open | 100 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-107 | fire:open | 107 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-107 | fire:open | 107 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-107 | fire:open | 107 |  |  |  |
| self_ref | F-D-a561349715-anomaly1-107 | fire:open | 107 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-107 | fire:open | 107 |  |  |  |
| self_ref | F-D-577af3f881-anomaly1-107 | fire:open | 107 |  |  |  |
| self_ref | F-D-c5da5d7229-anomaly0-112 | fire:open | 112 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-112 | fire:open | 112 |  |  |  |
| self_ref | F-D-52eb800ece-anomaly0-118 | fire:applied | 118 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-118 | fire:open | 118 |  |  |  |
| self_ref | F-D-76d69df076-anomaly0-118 | fire:open | 118 |  |  |  |
| self_ref | F-D-a97cd6612e-anomaly0-118 | fire:applied | 118 |  |  |  |
| self_ref | F-D-82f5e7a61e-anomaly0-118 | fire:applied | 118 |  |  |  |
| self_ref | F-D-40bfe4dca2-anomaly0-118 | fire:open | 118 |  |  |  |
| self_ref | D-17cef6212d | admitted | 120 | 120 |  |  |
| self_ref | D-0e9a9c08e7 | admitted | 120 | 120 |  |  |
| self_ref | D-6f95684225 | admitted | 120 | 120 |  |  |
| self_ref | D-4809405a01 | converged | 120 | 60 |  |  |
| self_ref | D-52eb800ece | converged | 120 | 90 |  |  |
| self_ref | D-e0e90d71f6 | converged | 120 | 90 |  |  |
| self_ref | D-2a8713f6dc | converged | 120 | 120 |  |  |
| self_ref | D-605ccc38ce | converged | 120 | 120 |  |  |
| self_ref | F-D-5f711a7557-anomaly0-121 | fire:applied | 121 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-121 | fire:open | 121 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-132 | fire:open | 132 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-132 | fire:open | 132 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-132 | fire:open | 132 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-139 | fire:open | 139 |  |  |  |
| self_ref | F-D-40bfe4dca2-anomaly0-139 | fire:open | 139 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-139 | fire:open | 139 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-139 | fire:open | 139 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-145 | fire:open | 145 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-145 | fire:open | 145 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-145 | fire:open | 145 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-146 | fire:open | 146 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-146 | fire:open | 146 |  |  |  |
| self_ref | F-D-40bfe4dca2-anomaly0-146 | fire:open | 146 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-146 | fire:open | 146 |  |  |  |
| self_ref | F-D-a561349715-anomaly1-146 | fire:open | 146 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-146 | fire:open | 146 |  |  |  |
| self_ref | F-D-40bfe4dca2-anomaly1-146 | fire:open | 146 |  |  |  |
| self_ref | F-D-577af3f881-anomaly1-146 | fire:open | 146 |  |  |  |
| self_ref | D-ce0f3516d0 | admitted | 150 | 150 |  |  |
| self_ref | D-a96a39d680 | admitted | 150 | 150 |  |  |
| self_ref | D-cc99bfa8f4 | admitted | 150 | 150 |  |  |
| self_ref | D-d37ebcb3f8 | admitted | 150 | 150 |  |  |
| self_ref | D-7725c88e1c | converged | 150 | 60 |  |  |
| self_ref | D-fe138b9df7 | converged | 150 | 60 |  |  |
| self_ref | D-5c4a2e7943 | converged | 150 | 90 |  |  |
| self_ref | D-7238c8ece5 | converged | 150 | 90 |  |  |
| self_ref | D-81650a64b9 | converged | 150 | 120 |  |  |
| self_ref | D-b16c4f80e0 | converged | 150 | 120 |  |  |
| self_ref | D-bfac8c0f04 | converged | 150 | 150 |  |  |
| self_ref | D-a7be011fdb | converged | 150 | 150 |  |  |
| self_ref | D-69b24d0771 | converged | 150 | 150 |  |  |
| self_ref | F-D-957adaa9b7-anomaly0-153 | fire:open | 153 |  |  |  |
| self_ref | F-D-ab10f09e13-anomaly0-153 | fire:open | 153 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-153 | fire:open | 153 |  |  |  |
| self_ref | F-D-c32813e288-anomaly0-169 | fire:applied | 169 |  |  |  |
| self_ref | F-D-90e74d972b-anomaly0-169 | fire:applied | 169 |  |  |  |
| self_ref | F-D-fa9cb0c040-anomaly0-169 | fire:open | 169 |  |  |  |
| self_ref | F-D-82f5e7a61e-anomaly0-169 | fire:applied | 169 |  |  |  |
| self_ref | F-D-5f711a7557-anomaly0-169 | fire:applied | 169 |  |  |  |
| self_ref | F-D-76d69df076-anomaly0-169 | fire:open | 169 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-169 | fire:open | 169 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly0-175 | fire:applied | 175 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-175 | fire:open | 175 |  |  |  |
| self_ref | F-D-dd07959475-anomaly0-175 | fire:applied | 175 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-175 | fire:open | 175 |  |  |  |
| self_ref | F-D-957adaa9b7-anomaly0-176 | fire:open | 176 |  |  |  |
| self_ref | F-D-ab10f09e13-anomaly0-176 | fire:open | 176 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-176 | fire:open | 176 |  |  |  |
| self_ref | F-D-957adaa9b7-anomaly1-176 | fire:open | 176 |  |  |  |
| self_ref | F-D-ab10f09e13-anomaly1-176 | fire:open | 176 |  |  |  |
| self_ref | F-D-577af3f881-anomaly1-176 | fire:open | 176 |  |  |  |
| self_ref | D-9a57eb6491 | admitted | 180 | 180 |  |  |
| self_ref | D-0790f712eb | admitted | 180 | 180 |  |  |
| self_ref | D-a7b53adf29 | admitted | 180 | 180 |  |  |
| self_ref | D-f5cd1815c1 | converged | 180 | 60 |  |  |
| self_ref | D-82f5e7a61e | converged | 180 | 90 |  |  |
| self_ref | D-26182d547c | converged | 180 | 120 |  |  |
| self_ref | D-4a526698d2 | converged | 180 | 150 |  |  |
| self_ref | D-e045259b19 | converged | 180 | 150 |  |  |
| self_ref | D-f1bab1e3b8 | converged | 180 | 180 |  |  |
| self_ref | D-0e094c024b | converged | 180 | 180 |  |  |
| self_ref | D-92e0ec9604 | converged | 180 | 180 |  |  |
| self_ref | D-2ea54a6d04 | converged | 180 | 180 |  |  |
| self_ref | D-879c1a260d | converged | 180 | 150 |  |  |
| self_ref | F-D-632f41de5c-anomaly0-180 | fire:applied | 180 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-180 | fire:open | 180 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-180 | fire:open | 180 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly1-180 | fire:applied | 180 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-180 | fire:open | 180 |  |  |  |
| self_ref | F-D-577af3f881-anomaly1-180 | fire:open | 180 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly2-180 | fire:applied | 180 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly2-180 | fire:open | 180 |  |  |  |
| self_ref | F-D-577af3f881-anomaly2-180 | fire:open | 180 |  |  |  |
| self_ref | F-D-5f711a7557-anomaly0-185 | fire:applied | 185 |  |  |  |
| self_ref | F-D-5f711a7557-anomaly0-187 | fire:applied | 187 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-190 | fire:open | 190 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly1-190 | fire:open | 190 |  |  |  |
| self_ref | F-D-5f711a7557-anomaly0-192 | fire:applied | 192 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-196 | fire:open | 196 |  |  |  |
| self_ref | F-D-dd07959475-anomaly0-196 | fire:applied | 196 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-196 | fire:open | 196 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly0-198 | fire:applied | 198 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-198 | fire:open | 198 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly1-198 | fire:applied | 198 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-198 | fire:open | 198 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly0-200 | fire:applied | 200 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-200 | fire:open | 200 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-204 | fire:open | 204 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-204 | fire:open | 204 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-204 | fire:open | 204 |  |  |  |
| self_ref | F-D-a561349715-anomaly1-204 | fire:open | 204 |  |  |  |
| self_ref | F-D-577af3f881-anomaly1-204 | fire:open | 204 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-204 | fire:open | 204 |  |  |  |
| self_ref | D-df41889959 | admitted | 210 | 210 |  |  |
| self_ref | D-0aa4a8e158 | admitted | 210 | 210 |  |  |
| self_ref | D-5c601f9ac3 | admitted | 210 | 210 |  |  |
| self_ref | D-e95d26b293 | admitted | 210 | 210 |  |  |
| self_ref | D-6621461470 | admitted | 210 | 210 |  |  |
| self_ref | D-eb4f4017ac | admitted | 210 | 210 |  |  |
| self_ref | D-f39af2efef | admitted | 210 | 210 |  |  |
| self_ref | D-9afda86b6c | admitted | 210 | 210 |  |  |
| self_ref | D-4802ce821d | converged | 210 | 120 |  |  |
| self_ref | D-5f711a7557 | converged | 210 | 120 |  |  |
| self_ref | D-d0c5f4e844 | converged | 210 | 150 |  |  |
| self_ref | D-cb2d8971b9 | converged | 210 | 180 |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-210 | fire:open | 210 |  |  |  |
| self_ref | F-D-0e9a9c08e7-anomaly0-214 | fire:open | 214 |  |  |  |
| self_ref | F-D-765f3ead35-anomaly0-214 | fire:applied | 214 |  |  |  |
| self_ref | F-D-5baafeef0c-anomaly0-214 | fire:applied | 214 |  |  |  |
| self_ref | F-D-c2285ae442-anomaly0-214 | fire:open | 214 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-221 | fire:open | 221 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-221 | fire:open | 221 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-221 | fire:open | 221 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-221 | fire:open | 221 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-221 | fire:open | 221 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-221 | fire:open | 221 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-222 | fire:open | 222 |  |  |  |
| self_ref | F-D-5c601f9ac3-anomaly0-222 | fire:open | 222 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-223 | fire:open | 223 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-223 | fire:open | 223 |  |  |  |
| self_ref | F-D-4333d27f11-anomaly0-225 | fire:applied | 225 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-225 | fire:open | 225 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-225 | fire:open | 225 |  |  |  |
| self_ref | F-D-5c601f9ac3-anomaly0-225 | fire:open | 225 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-229 | fire:open | 229 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly0-229 | fire:applied | 229 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-229 | fire:open | 229 |  |  |  |
| self_ref | F-D-a561349715-anomaly1-229 | fire:open | 229 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly1-229 | fire:applied | 229 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-229 | fire:open | 229 |  |  |  |
| self_ref | F-D-0e9a9c08e7-anomaly0-230 | fire:open | 230 |  |  |  |
| self_ref | F-D-ce0f3516d0-anomaly0-230 | fire:open | 230 |  |  |  |
| self_ref | F-D-59efbbad45-anomaly0-230 | fire:applied | 230 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-230 | fire:open | 230 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly0-234 | fire:applied | 234 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-234 | fire:open | 234 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-234 | fire:open | 234 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-234 | fire:open | 234 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly1-234 | fire:applied | 234 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-234 | fire:open | 234 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-234 | fire:open | 234 |  |  |  |
| self_ref | F-D-577af3f881-anomaly1-234 | fire:open | 234 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-235 | fire:open | 235 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-235 | fire:open | 235 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-235 | fire:open | 235 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-235 | fire:open | 235 |  |  |  |
| self_ref | F-D-df41889959-anomaly2-235 | fire:open | 235 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly2-235 | fire:open | 235 |  |  |  |
| self_ref | D-66e55b4eda | admitted | 240 | 240 |  |  |
| self_ref | D-4925a2ae38 | admitted | 240 | 240 |  |  |
| self_ref | D-9143a19782 | admitted | 240 | 240 |  |  |
| self_ref | D-c79ba0d523 | admitted | 240 | 240 |  |  |
| self_ref | D-e9fa32936d | converged | 240 | 120 |  |  |
| self_ref | D-90e74d972b | converged | 240 | 150 |  |  |
| self_ref | D-98851a9337 | converged | 240 | 180 |  |  |
| self_ref | D-a7c04c7608 | converged | 240 | 180 |  |  |
| self_ref | D-9dfb1ba957 | converged | 240 | 180 |  |  |
| self_ref | D-3ab0915373 | converged | 240 | 210 |  |  |
| self_ref | D-4788a6debf | converged | 240 | 210 |  |  |
| self_ref | D-170864cc41 | converged | 240 | 210 |  |  |
| self_ref | D-491d328eb5 | converged | 240 | 240 |  |  |
| self_ref | D-c935be63ad | converged | 240 | 240 |  |  |
| self_ref | F-D-0aa4a8e158-anomaly0-247 | fire:open | 247 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-247 | fire:open | 247 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-247 | fire:open | 247 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-247 | fire:open | 247 |  |  |  |
| self_ref | F-D-0aa4a8e158-anomaly1-247 | fire:open | 247 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-247 | fire:open | 247 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-247 | fire:open | 247 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-247 | fire:open | 247 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly0-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-a561349715-anomaly1-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly1-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-a561349715-anomaly2-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-df41889959-anomaly2-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly2-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly2-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly2-248 | fire:open | 248 |  |  |  |
| self_ref | F-D-0790f712eb-anomaly0-254 | fire:open | 254 |  |  |  |
| self_ref | F-D-a7b53adf29-anomaly0-254 | fire:open | 254 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-265 | fire:open | 265 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-265 | fire:open | 265 |  |  |  |
| self_ref | F-D-4333d27f11-anomaly0-266 | fire:applied | 266 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-266 | fire:open | 266 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-266 | fire:open | 266 |  |  |  |
| self_ref | F-D-4333d27f11-anomaly1-266 | fire:applied | 266 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-266 | fire:open | 266 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-266 | fire:open | 266 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-267 | fire:open | 267 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-267 | fire:open | 267 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-267 | fire:open | 267 |  |  |  |
| self_ref | F-D-577af3f881-anomaly1-267 | fire:open | 267 |  |  |  |
| self_ref | F-D-df41889959-anomaly2-267 | fire:open | 267 |  |  |  |
| self_ref | F-D-577af3f881-anomaly2-267 | fire:open | 267 |  |  |  |
| self_ref | D-64ee6c4f45 | admitted | 270 | 270 |  |  |
| self_ref | D-7f861d4ae5 | admitted | 270 | 270 |  |  |
| self_ref | D-733daa5271 | admitted | 270 | 270 |  |  |
| self_ref | D-ae3ee55b4c | converged | 270 | 60 |  |  |
| self_ref | D-4333d27f11 | converged | 270 | 150 |  |  |
| self_ref | D-2d5c0c1ddd | converged | 270 | 180 |  |  |
| self_ref | D-5baafeef0c | converged | 270 | 180 |  |  |
| self_ref | D-19c46ff5cd | converged | 270 | 210 |  |  |
| self_ref | D-bfedbf8b9e | converged | 270 | 240 |  |  |
| self_ref | D-0eb1587c27 | converged | 270 | 240 |  |  |
| self_ref | D-9c0c6c26ca | converged | 270 | 240 |  |  |
| self_ref | D-ce7291825e | converged | 270 | 240 |  |  |
| self_ref | D-6b3c4f9897 | converged | 270 | 240 |  |  |
| self_ref | D-9673bda773 | converged | 270 | 270 |  |  |
| self_ref | D-939d486b97 | converged | 270 | 270 |  |  |
| self_ref | D-4f3e8d59fb | converged | 270 | 120 |  |  |
| self_ref | D-59efbbad45 | converged | 270 | 180 |  |  |
| self_ref | F-D-632f41de5c-anomaly0-279 | fire:applied | 279 |  |  |  |
| self_ref | F-D-a114e47670-anomaly0-279 | fire:applied | 279 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-279 | fire:open | 279 |  |  |  |
| self_ref | F-D-733daa5271-anomaly0-279 | fire:open | 279 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly1-279 | fire:applied | 279 |  |  |  |
| self_ref | F-D-a114e47670-anomaly1-279 | fire:applied | 279 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-279 | fire:open | 279 |  |  |  |
| self_ref | F-D-733daa5271-anomaly1-279 | fire:open | 279 |  |  |  |
| self_ref | F-D-9a57eb6491-anomaly0-287 | fire:open | 287 |  |  |  |
| self_ref | F-D-eb4f4017ac-anomaly0-287 | fire:open | 287 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-287 | fire:open | 287 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-291 | fire:open | 291 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-291 | fire:open | 291 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-291 | fire:open | 291 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-291 | fire:open | 291 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-291 | fire:open | 291 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-291 | fire:open | 291 |  |  |  |
| self_ref | F-D-0aa4a8e158-anomaly0-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly0-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-a114e47670-anomaly0-295 | fire:applied | 295 |  |  |  |
| self_ref | F-D-0aa4a8e158-anomaly1-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly1-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-a114e47670-anomaly1-295 | fire:applied | 295 |  |  |  |
| self_ref | F-D-0aa4a8e158-anomaly2-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-df41889959-anomaly2-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly2-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly2-295 | fire:open | 295 |  |  |  |
| self_ref | F-D-a114e47670-anomaly2-295 | fire:applied | 295 |  |  |  |
| self_ref | D-368180e4e2 | admitted | 300 | 300 |  |  |
| self_ref | D-d1a58d9d04 | admitted | 300 | 300 |  |  |
| self_ref | D-187e50deb4 | admitted | 300 | 300 |  |  |
| self_ref | D-0bfefeb798 | admitted | 300 | 300 |  |  |
| self_ref | D-9832a4f3d4 | admitted | 300 | 300 |  |  |
| self_ref | D-300b1121e6 | converged | 300 | 270 |  |  |
| self_ref | D-569255d48e | converged | 300 | 120 |  |  |
| self_ref | D-ed812e0f62 | converged | 300 | 210 |  |  |
| self_ref | D-63cd5319cf | converged | 300 | 270 |  |  |
| self_ref | D-d55c0ed7da | converged | 300 | 270 |  |  |
| self_ref | D-1599ceb520 | converged | 300 | 270 |  |  |
| self_ref | D-c9262dfae6 | converged | 300 | 270 |  |  |
| self_ref | D-6e984e6a9d | converged | 300 | 270 |  |  |
| self_ref | D-bba23435e1 | converged | 300 | 270 |  |  |
| self_ref | D-82b5559d9f | converged | 300 | 300 |  |  |
| self_ref | D-e9322ab1b3 | converged | 300 | 300 |  |  |
| self_ref | D-a114e47670 | converged | 300 | 270 |  |  |
| self_ref | F-D-96524f25c8-anomaly0-300 | fire:applied | 300 |  |  |  |
| self_ref | F-D-368180e4e2-anomaly0-300 | fire:open | 300 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-300 | fire:open | 300 |  |  |  |
| self_ref | F-D-96524f25c8-anomaly1-300 | fire:applied | 300 |  |  |  |
| self_ref | F-D-368180e4e2-anomaly1-300 | fire:open | 300 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly1-300 | fire:open | 300 |  |  |  |
| self_ref | F-D-0e9a9c08e7-anomaly0-303 | fire:open | 303 |  |  |  |
| self_ref | F-D-22edce6519-anomaly0-303 | fire:applied | 303 |  |  |  |
| self_ref | F-D-b604a3747f-anomaly0-303 | fire:applied | 303 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-303 | fire:open | 303 |  |  |  |
| self_ref | F-D-765f3ead35-anomaly0-303 | fire:applied | 303 |  |  |  |
| self_ref | F-D-0e9a9c08e7-anomaly1-303 | fire:open | 303 |  |  |  |
| self_ref | F-D-22edce6519-anomaly1-303 | fire:applied | 303 |  |  |  |
| self_ref | F-D-b604a3747f-anomaly1-303 | fire:applied | 303 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly1-303 | fire:open | 303 |  |  |  |
| self_ref | F-D-765f3ead35-anomaly1-303 | fire:applied | 303 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-316 | fire:open | 316 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-316 | fire:open | 316 |  |  |  |
| self_ref | F-D-a561349715-anomaly1-316 | fire:open | 316 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-316 | fire:open | 316 |  |  |  |
| self_ref | F-D-632f41de5c-anomaly0-318 | fire:applied | 318 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-318 | fire:open | 318 |  |  |  |
| self_ref | F-D-d1a58d9d04-anomaly0-318 | fire:open | 318 |  |  |  |
| self_ref | D-54865e8a23 | admitted | 330 | 330 |  |  |
| self_ref | D-102a074503 | admitted | 330 | 330 |  |  |
| self_ref | D-b521f48d84 | admitted | 330 | 330 |  |  |
| self_ref | D-e4f9ec9a63 | admitted | 330 | 330 |  |  |
| self_ref | D-ac0d26bc5f | admitted | 330 | 330 |  |  |
| self_ref | D-fbc66f360d | admitted | 330 | 330 |  |  |
| self_ref | D-e15c013401 | admitted | 330 | 330 |  |  |
| self_ref | D-241b78c27c | admitted | 330 | 330 |  |  |
| self_ref | D-bab629458f | converged | 330 | 150 |  |  |
| self_ref | D-96524f25c8 | converged | 330 | 240 |  |  |
| self_ref | D-6dfef9bbb9 | converged | 330 | 270 |  |  |
| self_ref | D-93b6feefb6 | converged | 330 | 270 |  |  |
| self_ref | D-711f629e4d | converged | 330 | 300 |  |  |
| self_ref | D-7db23f5023 | converged | 330 | 300 |  |  |
| self_ref | D-1d2e714018 | converged | 330 | 330 |  |  |
| self_ref | D-7caf7ae7d1 | converged | 330 | 330 |  |  |
| self_ref | F-D-aff8b960df-anomaly0-332 | fire:open | 332 |  |  |  |
| self_ref | F-D-5cb9a39ff8-anomaly0-332 | fire:applied | 332 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-334 | fire:open | 334 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-334 | fire:open | 334 |  |  |  |
| self_ref | F-D-dd07959475-anomaly0-334 | fire:applied | 334 |  |  |  |
| self_ref | F-D-de8501da42-anomaly0-340 | fire:applied | 340 |  |  |  |
| self_ref | F-D-921f6debfe-anomaly0-340 | fire:applied | 340 |  |  |  |
| self_ref | F-D-a317a92b56-anomaly0-340 | fire:applied | 340 |  |  |  |
| self_ref | F-D-38ee45f68a-anomaly0-340 | fire:applied | 340 |  |  |  |
| self_ref | F-D-9b3fbbf57c-anomaly0-340 | fire:applied | 340 |  |  |  |
| self_ref | F-D-e3d815d7f1-anomaly0-340 | fire:applied | 340 |  |  |  |
| self_ref | F-D-4d30355b00-anomaly0-340 | fire:applied | 340 |  |  |  |
| self_ref | F-D-78b40551ea-anomaly0-340 | fire:applied | 340 |  |  |  |
| self_ref | F-D-67340bfbe6-anomaly0-344 | fire:applied | 344 |  |  |  |
| self_ref | F-D-e95d26b293-anomaly0-344 | fire:open | 344 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-359 | fire:open | 359 |  |  |  |
| self_ref | F-D-5cb9a39ff8-anomaly0-359 | fire:applied | 359 |  |  |  |
| self_ref | F-D-d1a58d9d04-anomaly0-359 | fire:open | 359 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-359 | fire:open | 359 |  |  |  |
| self_ref | F-D-5cb9a39ff8-anomaly1-359 | fire:applied | 359 |  |  |  |
| self_ref | F-D-d1a58d9d04-anomaly1-359 | fire:open | 359 |  |  |  |
| self_ref | D-13df3ec75f | admitted | 360 | 360 |  |  |
| self_ref | D-4b70ea2792 | admitted | 360 | 360 |  |  |
| self_ref | D-41ddef7365 | admitted | 360 | 360 |  |  |
| self_ref | D-4335c32d08 | admitted | 360 | 360 |  |  |
| self_ref | D-0b0c2137da | admitted | 360 | 360 |  |  |
| self_ref | D-7f722d8a19 | admitted | 360 | 360 |  |  |
| self_ref | D-0a09ef5b76 | admitted | 360 | 360 |  |  |
| self_ref | D-62b91ce7a9 | admitted | 360 | 360 |  |  |
| self_ref | D-f6a2c587c8 | admitted | 360 | 360 |  |  |
| self_ref | D-2b8fe20f65 | admitted | 360 | 360 |  |  |
| self_ref | D-f382564bef | admitted | 360 | 360 |  |  |
| self_ref | D-632f41de5c | converged | 360 | 150 |  |  |
| self_ref | D-11126819fa | converged | 360 | 240 |  |  |
| self_ref | D-03b6129ca8 | converged | 360 | 240 |  |  |
| self_ref | D-d53c918867 | converged | 360 | 270 |  |  |
| self_ref | D-1da23c7adc | converged | 360 | 270 |  |  |
| self_ref | D-a317a92b56 | converged | 360 | 270 |  |  |
| self_ref | D-79a830e53d | converged | 360 | 300 |  |  |
| self_ref | D-22edce6519 | converged | 360 | 300 |  |  |
| self_ref | D-15cd4d30a7 | converged | 360 | 330 |  |  |
| self_ref | D-5cb9a39ff8 | converged | 360 | 330 |  |  |
| self_ref | D-e803da3a1b | converged | 360 | 330 |  |  |
| self_ref | D-3c1971d0e5 | converged | 360 | 360 |  |  |
| self_ref | D-78b40551ea | converged | 360 | 270 |  |  |
| self_ref | D-ac8ff297f0 | moot | 360 | 30 |  |  |
| self_ref | F-D-187b4e3175-anomaly0-365 | fire:applied | 365 |  |  |  |
| self_ref | F-D-76d69df076-anomaly0-365 | fire:open | 365 |  |  |  |
| self_ref | F-D-368180e4e2-anomaly0-365 | fire:open | 365 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-365 | fire:open | 365 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-366 | fire:open | 366 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-366 | fire:open | 366 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-366 | fire:open | 366 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly1-366 | fire:open | 366 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-366 | fire:open | 366 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-366 | fire:open | 366 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-368 | fire:applied | 368 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-368 | fire:open | 368 |  |  |  |
| self_ref | F-D-957adaa9b7-anomaly0-368 | fire:open | 368 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-368 | fire:open | 368 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-376 | fire:open | 376 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-376 | fire:open | 376 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly1-376 | fire:open | 376 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-376 | fire:open | 376 |  |  |  |
| self_ref | F-D-0e9a9c08e7-anomaly0-383 | fire:open | 383 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-383 | fire:applied | 383 |  |  |  |
| self_ref | F-D-9143a19782-anomaly0-383 | fire:open | 383 |  |  |  |
| self_ref | F-D-765f3ead35-anomaly0-383 | fire:applied | 383 |  |  |  |
| self_ref | F-D-0e9a9c08e7-anomaly1-383 | fire:open | 383 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly1-383 | fire:applied | 383 |  |  |  |
| self_ref | F-D-9143a19782-anomaly1-383 | fire:open | 383 |  |  |  |
| self_ref | F-D-765f3ead35-anomaly1-383 | fire:applied | 383 |  |  |  |
| self_ref | D-b67d4f0dad | admitted | 390 | 390 |  |  |
| self_ref | D-93d0a16841 | admitted | 390 | 390 |  |  |
| self_ref | D-883a19049e | admitted | 390 | 390 |  |  |
| self_ref | D-d174edd1c3 | admitted | 390 | 390 |  |  |
| self_ref | D-bfc71d4481 | admitted | 390 | 390 |  |  |
| self_ref | D-b24f6d897f | admitted | 390 | 390 |  |  |
| self_ref | D-765f3ead35 | converged | 390 | 180 |  |  |
| self_ref | D-de8501da42 | converged | 390 | 210 |  |  |
| self_ref | D-975e992859 | converged | 390 | 270 |  |  |
| self_ref | D-20693654fd | converged | 390 | 300 |  |  |
| self_ref | D-b604a3747f | converged | 390 | 300 |  |  |
| self_ref | D-921f6debfe | converged | 390 | 300 |  |  |
| self_ref | D-4d30355b00 | converged | 390 | 330 |  |  |
| self_ref | D-14a7c07039 | converged | 390 | 330 |  |  |
| self_ref | D-ebb09519a1 | converged | 390 | 360 |  |  |
| self_ref | D-11e6ecfdf4 | converged | 390 | 360 |  |  |
| self_ref | D-b69ee4d6ac | converged | 390 | 360 |  |  |
| self_ref | D-4ca6aad9e9 | converged | 390 | 240 |  |  |
| self_ref | F-D-41ddef7365-anomaly0-394 | fire:open | 394 |  |  |  |
| self_ref | F-D-2b8fe20f65-anomaly0-394 | fire:open | 394 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-394 | fire:open | 394 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-394 | fire:open | 394 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-a561349715-anomaly0-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-dd07959475-anomaly0-396 | fire:applied | 396 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly0-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly1-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-a561349715-anomaly1-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-dd07959475-anomaly1-396 | fire:applied | 396 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly1-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-396 | fire:open | 396 |  |  |  |
| self_ref | F-D-ac0d26bc5f-anomaly0-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-2b8fe20f65-anomaly0-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-ac0d26bc5f-anomaly1-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly1-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-2b8fe20f65-anomaly1-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly1-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-ac0d26bc5f-anomaly2-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly2-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-2b8fe20f65-anomaly2-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-df41889959-anomaly2-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly2-415 | fire:open | 415 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly2-415 | fire:open | 415 |  |  |  |
| self_ref | D-740c6fcf52 | admitted | 420 | 420 |  |  |
| self_ref | D-7382ec23ed | admitted | 420 | 420 |  |  |
| self_ref | D-33ba0d1860 | admitted | 420 | 420 |  |  |
| self_ref | D-30623550c1 | admitted | 420 | 420 |  |  |
| self_ref | D-d3e83ac07d | admitted | 420 | 420 |  |  |
| self_ref | D-fc0c5586cb | admitted | 420 | 420 |  |  |
| self_ref | D-3dcac6f33e | admitted | 420 | 420 |  |  |
| self_ref | D-c878a376ba | admitted | 420 | 420 |  |  |
| self_ref | D-7c6144e9c7 | admitted | 420 | 420 |  |  |
| self_ref | D-18690aeb73 | admitted | 420 | 420 |  |  |
| self_ref | D-330b7736e6 | admitted | 420 | 420 |  |  |
| self_ref | D-e3d815d7f1 | converged | 420 | 150 |  |  |
| self_ref | D-74af6e600d | converged | 420 | 240 |  |  |
| self_ref | D-187b4e3175 | converged | 420 | 270 |  |  |
| self_ref | D-e3b87c8707 | converged | 420 | 330 |  |  |
| self_ref | D-53f8ef067e | converged | 420 | 360 |  |  |
| self_ref | D-e79ccd717f | converged | 420 | 390 |  |  |
| self_ref | D-fb46146546 | converged | 420 | 390 |  |  |
| self_ref | D-412aff62c7 | converged | 420 | 390 |  |  |
| self_ref | D-15f5f7d3ea | converged | 420 | 390 |  |  |
| self_ref | D-51f1a2b134 | converged | 420 | 420 |  |  |
| self_ref | D-0d55688a8b | converged | 420 | 420 |  |  |
| self_ref | D-05dbdf59dd | moot | 420 | 60 |  |  |
| self_ref | D-222f2ba89d | moot | 420 | 90 |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-427 | fire:open | 427 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-427 | fire:open | 427 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-427 | fire:open | 427 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-427 | fire:open | 427 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly1-427 | fire:open | 427 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-427 | fire:open | 427 |  |  |  |
| self_ref | F-D-577af3f881-anomaly1-427 | fire:open | 427 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-427 | fire:open | 427 |  |  |  |
| self_ref | F-D-67340bfbe6-anomaly0-431 | fire:applied | 431 |  |  |  |
| self_ref | F-D-e95d26b293-anomaly0-431 | fire:open | 431 |  |  |  |
| self_ref | F-D-67340bfbe6-anomaly0-432 | fire:applied | 432 |  |  |  |
| self_ref | F-D-e95d26b293-anomaly0-432 | fire:open | 432 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-440 | fire:open | 440 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-440 | fire:open | 440 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-440 | fire:open | 440 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly0-440 | fire:open | 440 |  |  |  |
| self_ref | F-D-ca948d9307-anomaly0-440 | fire:applied | 440 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly1-440 | fire:open | 440 |  |  |  |
| self_ref | F-D-df41889959-anomaly1-440 | fire:open | 440 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly1-440 | fire:open | 440 |  |  |  |
| self_ref | F-D-c79ba0d523-anomaly1-440 | fire:open | 440 |  |  |  |
| self_ref | F-D-ca948d9307-anomaly1-440 | fire:applied | 440 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-444 | fire:applied | 444 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-444 | fire:open | 444 |  |  |  |
| self_ref | F-D-0aa4a8e158-anomaly0-449 | fire:open | 449 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-449 | fire:applied | 449 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-449 | fire:open | 449 |  |  |  |
| self_ref | F-D-957adaa9b7-anomaly0-449 | fire:open | 449 |  |  |  |
| self_ref | F-D-eb4f4017ac-anomaly0-449 | fire:open | 449 |  |  |  |
| self_ref | F-D-577af3f881-anomaly0-449 | fire:open | 449 |  |  |  |
| self_ref | D-393fcee795 | admitted | 450 | 450 |  |  |
| self_ref | D-8b1946e696 | admitted | 450 | 450 |  |  |
| self_ref | D-718373769d | admitted | 450 | 450 |  |  |
| self_ref | D-3a78e018c1 | admitted | 450 | 450 |  |  |
| self_ref | D-86b66778ea | admitted | 450 | 450 |  |  |
| self_ref | D-acb99773d9 | admitted | 450 | 450 |  |  |
| self_ref | D-885e025638 | admitted | 450 | 450 |  |  |
| self_ref | D-d87620c02d | admitted | 450 | 450 |  |  |
| self_ref | D-c32813e288 | converged | 450 | 120 |  |  |
| self_ref | D-67340bfbe6 | converged | 450 | 300 |  |  |
| self_ref | D-a635aebdfa | converged | 450 | 330 |  |  |
| self_ref | D-df7056712b | converged | 450 | 330 |  |  |
| self_ref | D-9b3fbbf57c | converged | 450 | 330 |  |  |
| self_ref | D-4261350000 | converged | 450 | 360 |  |  |
| self_ref | D-d3316d071a | converged | 450 | 420 |  |  |
| self_ref | D-ca948d9307 | converged | 450 | 420 |  |  |
| self_ref | D-ce3499c449 | converged | 450 | 420 |  |  |
| self_ref | D-a97cd6612e | converged | 450 | 60 |  |  |
| self_ref | D-dd07959475 | converged | 450 | 150 |  |  |
| self_ref | D-09742d27de | moot | 450 | 150 |  |  |
| self_ref | F-D-ac0d26bc5f-anomaly0-464 | fire:open | 464 |  |  |  |
| self_ref | F-D-393fcee795-anomaly0-464 | fire:open | 464 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-464 | fire:open | 464 |  |  |  |
| self_ref | F-D-2b8fe20f65-anomaly0-464 | fire:open | 464 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-464 | fire:open | 464 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-464 | fire:open | 464 |  |  |  |
| self_ref | F-D-885e025638-anomaly0-464 | fire:open | 464 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-466 | fire:applied | 466 |  |  |  |
| self_ref | F-D-8b1946e696-anomaly0-466 | fire:open | 466 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-466 | fire:open | 466 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-468 | fire:open | 468 |  |  |  |
| self_ref | F-D-393fcee795-anomaly0-468 | fire:open | 468 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-468 | fire:open | 468 |  |  |  |
| self_ref | F-D-885e025638-anomaly0-468 | fire:open | 468 |  |  |  |
| self_ref | F-D-393fcee795-anomaly0-479 | fire:open | 479 |  |  |  |
| self_ref | F-D-62b91ce7a9-anomaly0-479 | fire:open | 479 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-479 | fire:open | 479 |  |  |  |
| self_ref | F-D-885e025638-anomaly0-479 | fire:open | 479 |  |  |  |
| self_ref | D-2c8ca4fe67 | admitted | 480 | 480 |  |  |
| self_ref | D-e57d245dd2 | admitted | 480 | 480 |  |  |
| self_ref | D-6aa7a31e81 | admitted | 480 | 480 |  |  |
| self_ref | D-df66f6e526 | admitted | 480 | 480 |  |  |
| self_ref | D-569372d094 | admitted | 480 | 480 |  |  |
| self_ref | D-6baafbf346 | admitted | 480 | 480 |  |  |
| self_ref | D-6b4b514012 | admitted | 480 | 480 |  |  |
| self_ref | D-97bb98ea54 | admitted | 480 | 480 |  |  |
| self_ref | D-f346b4286f | admitted | 480 | 480 |  |  |
| self_ref | D-38ee45f68a | converged | 480 | 90 |  |  |
| self_ref | D-8fe0210f4d | converged | 480 | 360 |  |  |
| self_ref | D-93de596d09 | converged | 480 | 390 |  |  |
| self_ref | D-5193316307 | converged | 480 | 390 |  |  |
| self_ref | D-c8a5432165 | converged | 480 | 420 |  |  |
| self_ref | D-01c6959db7 | converged | 480 | 420 |  |  |
| self_ref | D-8199bd1286 | converged | 480 | 450 |  |  |
| self_ref | D-4c4c5abbda | converged | 480 | 450 |  |  |
| self_ref | D-8fa0f96dfd | converged | 480 | 450 |  |  |
| self_ref | D-46c91fa6d8 | converged | 480 | 480 |  |  |
| self_ref | D-5f6d928193 | converged | 480 | 480 |  |  |
| self_ref | D-6c2a97924e | moot | 480 | 180 |  |  |
| self_ref | D-fe98530a70 | moot | 480 | 180 |  |  |
| self_ref | F-D-49d4d71749-anomaly0-487 | fire:applied | 487 |  |  |  |
| self_ref | F-D-76d69df076-anomaly0-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-6ce2e98857-anomaly0-487 | fire:applied | 487 |  |  |  |
| self_ref | F-D-fa9cb0c040-anomaly0-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-368180e4e2-anomaly0-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-acb99773d9-anomaly0-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-49d4d71749-anomaly1-487 | fire:applied | 487 |  |  |  |
| self_ref | F-D-76d69df076-anomaly1-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-6ce2e98857-anomaly1-487 | fire:applied | 487 |  |  |  |
| self_ref | F-D-fa9cb0c040-anomaly1-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-368180e4e2-anomaly1-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly1-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-acb99773d9-anomaly1-487 | fire:open | 487 |  |  |  |
| self_ref | F-D-6621461470-anomaly0-504 | fire:open | 504 |  |  |  |
| self_ref | F-D-e95d26b293-anomaly0-504 | fire:open | 504 |  |  |  |
| self_ref | F-D-6f95684225-anomaly0-504 | fire:open | 504 |  |  |  |
| self_ref | F-D-e95d26b293-anomaly0-505 | fire:open | 505 |  |  |  |
| self_ref | F-D-e95d26b293-anomaly1-505 | fire:open | 505 |  |  |  |
| self_ref | D-20206f20ec | admitted | 510 | 510 |  |  |
| self_ref | D-7b48a5c0d0 | admitted | 510 | 510 |  |  |
| self_ref | D-19ce7c34bb | admitted | 510 | 510 |  |  |
| self_ref | D-c4006475f2 | admitted | 510 | 510 |  |  |
| self_ref | D-86440cda99 | admitted | 510 | 510 |  |  |
| self_ref | D-7661ed8444 | admitted | 510 | 510 |  |  |
| self_ref | D-b2b9b26996 | converged | 510 | 60 |  |  |
| self_ref | D-3dfc563463 | converged | 510 | 210 |  |  |
| self_ref | D-460cb6643f | converged | 510 | 300 |  |  |
| self_ref | D-bb16b4fb95 | converged | 510 | 360 |  |  |
| self_ref | D-7eac61cc2e | converged | 510 | 390 |  |  |
| self_ref | D-28857f07b4 | converged | 510 | 420 |  |  |
| self_ref | D-1cc5f78718 | converged | 510 | 450 |  |  |
| self_ref | D-657d19a9dc | converged | 510 | 480 |  |  |
| self_ref | D-c643729bbf | converged | 510 | 510 |  |  |
| self_ref | D-2e804d8a14 | converged | 510 | 510 |  |  |
| self_ref | D-230a264c74 | converged | 510 | 480 |  |  |
| self_ref | D-ada70dedd5 | moot | 510 | 60 |  |  |
| self_ref | D-60c0b5dbe9 | moot | 510 | 120 |  |  |
| self_ref | D-d99455a80f | moot | 510 | 180 |  |  |
| self_ref | D-0262735777 | moot | 510 | 210 |  |  |
| self_ref | D-ec997fb913 | moot | 510 | 210 |  |  |
| self_ref | D-447055b0e4 | moot | 510 | 210 |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-519 | fire:applied | 519 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-519 | fire:open | 519 |  |  |  |
| self_ref | F-D-e15c013401-anomaly0-539 | fire:open | 539 |  |  |  |
| self_ref | D-1d5e18df0b | admitted | 540 | 540 |  |  |
| self_ref | D-0235b3f176 | admitted | 540 | 540 |  |  |
| self_ref | D-dbe00f4a2e | admitted | 540 | 540 |  |  |
| self_ref | D-f24ae5d48d | admitted | 540 | 540 |  |  |
| self_ref | D-58c8d969ae | admitted | 540 | 540 |  |  |
| self_ref | D-59e3b7f31b | admitted | 540 | 540 |  |  |
| self_ref | D-601fe5e0fb | admitted | 540 | 540 |  |  |
| self_ref | D-008e7a2968 | admitted | 540 | 540 |  |  |
| self_ref | D-ca90704445 | admitted | 540 | 540 |  |  |
| self_ref | D-04164d1a40 | converged | 540 | 390 |  |  |
| self_ref | D-49d4d71749 | converged | 540 | 420 |  |  |
| self_ref | D-735f3a545d | converged | 540 | 480 |  |  |
| self_ref | D-760b14d942 | converged | 540 | 510 |  |  |
| self_ref | D-4614e4b2cf | converged | 540 | 510 |  |  |
| self_ref | D-f087644695 | converged | 540 | 510 |  |  |
| self_ref | D-42e40f84f8 | converged | 540 | 510 |  |  |
| self_ref | D-54dbdc5259 | converged | 540 | 510 |  |  |
| self_ref | D-26911af702 | converged | 540 | 540 |  |  |
| self_ref | D-5763a2f1b6 | converged | 540 | 540 |  |  |
| self_ref | D-0db7b534b7 | converged | 540 | 540 |  |  |
| self_ref | D-73c18e1b92 | converged | 540 | 540 |  |  |
| self_ref | D-d8b67e3681 | converged | 540 | 540 |  |  |
| self_ref | D-c5da5d7229 | moot | 540 | 30 |  |  |
| self_ref | D-bcff4b8976 | moot | 540 | 60 |  |  |
| self_ref | D-982ca559ba | moot | 540 | 60 |  |  |
| self_ref | D-2d41ecbd28 | moot | 540 | 120 |  |  |
| self_ref | D-d67e3651da | moot | 540 | 120 |  |  |
| self_ref | D-c2285ae442 | moot | 540 | 150 |  |  |
| self_ref | D-1bc785abbe | moot | 540 | 240 |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-542 | fire:open | 542 |  |  |  |
| self_ref | F-D-368180e4e2-anomaly0-542 | fire:open | 542 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly1-542 | fire:open | 542 |  |  |  |
| self_ref | F-D-368180e4e2-anomaly1-542 | fire:open | 542 |  |  |  |
| self_ref | D-da5e23a3a2 | admitted | 570 | 570 |  |  |
| self_ref | D-d876ab334b | admitted | 570 | 570 |  |  |
| self_ref | D-4c26eec784 | admitted | 570 | 570 |  |  |
| self_ref | D-8c9cb89fbc | admitted | 570 | 570 |  |  |
| self_ref | D-0770985676 | admitted | 570 | 570 |  |  |
| self_ref | D-dc914517fa | admitted | 570 | 570 |  |  |
| self_ref | D-8c38ecaeab | admitted | 570 | 570 |  |  |
| self_ref | D-1c6d61822c | admitted | 570 | 570 |  |  |
| self_ref | D-1563faa710 | admitted | 570 | 570 |  |  |
| self_ref | D-54cd6ce2de | admitted | 570 | 570 |  |  |
| self_ref | D-e22a82f704 | admitted | 570 | 570 |  |  |
| self_ref | D-e7322db2c5 | converged | 570 | 240 |  |  |
| self_ref | D-12a7d2e329 | converged | 570 | 330 |  |  |
| self_ref | D-c32f47395c | converged | 570 | 360 |  |  |
| self_ref | D-6ce2e98857 | converged | 570 | 450 |  |  |
| self_ref | D-6515360750 | converged | 570 | 480 |  |  |
| self_ref | D-4fa17c024b | converged | 570 | 510 |  |  |
| self_ref | D-d1ba556e81 | converged | 570 | 540 |  |  |
| self_ref | D-cd7e5e5d63 | converged | 570 | 540 |  |  |
| self_ref | D-ba4333520a | converged | 570 | 540 |  |  |
| self_ref | D-f86adc8eee | converged | 570 | 570 |  |  |
| self_ref | D-a9ee2df6c5 | converged | 570 | 360 |  |  |
| self_ref | D-654954ed99 | converged | 570 | 390 |  |  |
| self_ref | D-be3c3c34a5 | moot | 570 | 270 |  |  |
| self_ref | D-39a8707177 | moot | 570 | 270 |  |  |
| self_ref | F-D-368180e4e2-anomaly0-575 | fire:open | 575 |  |  |  |
| self_ref | F-D-ed58e25b15-anomaly0-575 | fire:open | 575 |  |  |  |
| self_ref | F-D-54cd6ce2de-anomaly0-578 | fire:open | 578 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-578 | fire:applied | 578 |  |  |  |
| self_ref | F-D-0e9a9c08e7-anomaly0-578 | fire:open | 578 |  |  |  |
| self_ref | F-D-7b48a5c0d0-anomaly0-578 | fire:open | 578 |  |  |  |
| self_ref | F-D-54cd6ce2de-anomaly1-578 | fire:open | 578 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly1-578 | fire:applied | 578 |  |  |  |
| self_ref | F-D-0e9a9c08e7-anomaly1-578 | fire:open | 578 |  |  |  |
| self_ref | F-D-7b48a5c0d0-anomaly1-578 | fire:open | 578 |  |  |  |
| self_ref | F-D-393fcee795-anomaly0-581 | fire:open | 581 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-581 | fire:open | 581 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-581 | fire:open | 581 |  |  |  |
| self_ref | F-D-aff8b960df-anomaly0-581 | fire:open | 581 |  |  |  |
| self_ref | F-D-885e025638-anomaly0-581 | fire:open | 581 |  |  |  |
| self_ref | F-D-393fcee795-anomaly0-589 | fire:open | 589 |  |  |  |
| self_ref | F-D-df41889959-anomaly0-589 | fire:open | 589 |  |  |  |
| self_ref | F-D-9afda86b6c-anomaly0-589 | fire:open | 589 |  |  |  |
| self_ref | F-D-885e025638-anomaly0-589 | fire:open | 589 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-591 | fire:applied | 591 |  |  |  |
| self_ref | F-D-dbe00f4a2e-anomaly0-591 | fire:open | 591 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-591 | fire:open | 591 |  |  |  |
| self_ref | F-D-e95d26b293-anomaly0-592 | fire:open | 592 |  |  |  |
| self_ref | F-D-e95d26b293-anomaly1-592 | fire:open | 592 |  |  |  |
| self_ref | F-D-54cd6ce2de-anomaly0-595 | fire:open | 595 |  |  |  |
| self_ref | F-D-66e55b4eda-anomaly0-595 | fire:open | 595 |  |  |  |
| self_ref | F-D-2b2cd4b0c2-anomaly0-595 | fire:applied | 595 |  |  |  |
| self_ref | F-D-9143a19782-anomaly0-595 | fire:open | 595 |  |  |  |
| self_ref | F-D-8c9cb89fbc-anomaly0-595 | fire:open | 595 |  |  |  |
| self_ref | F-D-ce0f3516d0-anomaly0-595 | fire:open | 595 |  |  |  |
| self_ref | F-D-ce7d1fd453-anomaly0-595 | fire:open | 595 |  |  |  |
| self_ref | F-D-58c8d969ae-anomaly0-597 | fire:open | 597 |  |  |  |
| self_ref | F-D-f24ae5d48d-anomaly0-597 | fire:open | 597 |  |  |  |
| self_ref | F-D-7f722d8a19-anomaly0-597 | fire:open | 597 |  |  |  |
| self_ref | F-D-d876ab334b-anomaly0-597 | fire:open | 597 |  |  |  |
| self_ref | D-34845546cf | admitted | 600 | 600 |  |  |
| self_ref | D-826172aa17 | admitted | 600 | 600 |  |  |
| self_ref | D-644b5adc2d | admitted | 600 | 600 |  |  |
| self_ref | D-9b9766c685 | admitted | 600 | 600 |  |  |
| self_ref | D-01a33d4a6a | admitted | 600 | 600 |  |  |
| self_ref | D-8ad5aca413 | admitted | 600 | 600 |  |  |
| self_ref | D-87f54b4da5 | admitted | 600 | 600 |  |  |
| self_ref | D-b433d5fe44 | admitted | 600 | 600 |  |  |
| self_ref | D-7c00705632 | admitted | 600 | 600 |  |  |
| self_ref | D-6111d862b2 | admitted | 600 | 600 |  |  |
| self_ref | D-2b2cd4b0c2 | converged | 600 | 360 |  |  |
| self_ref | D-2caf9caba7 | converged | 600 | 450 |  |  |
| self_ref | D-0d1a093f24 | converged | 600 | 480 |  |  |
| self_ref | D-6415328b82 | converged | 600 | 540 |  |  |
| self_ref | D-b47496932d | converged | 600 | 570 |  |  |
| self_ref | D-2d3245ec08 | converged | 600 | 570 |  |  |
| self_ref | D-5046171d3e | converged | 600 | 570 |  |  |
| self_ref | D-12e2466893 | converged | 600 | 600 |  |  |
| self_ref | D-adb539834b | converged | 600 | 600 |  |  |
| self_ref | D-66e4fadc45 | converged | 600 | 600 |  |  |
| self_ref | D-5958d98d2e | converged | 600 | 540 |  |  |
| self_ref | D-21357e874b | moot | 600 | 300 |  |  |
| ungated | D-791e7f4f42 | admitted | 120 | 120 |  | Q3_soft_delete |
| ungated | D-918a2f0930 | admitted | 120 | 120 |  |  |
| ungated | F-D-791e7f4f42-unattributed-129 | fire:open | 129 |  |  |  |
| ungated | F-D-79aec5f32f-T-D-79aec5f32f-1-g0 | fire:applied | 141 |  |  |  |
| ungated | D-f44b295b20 | admitted | 150 | 150 |  | Q5_revenue |
| ungated | D-f2c64e1b49 | admitted | 150 | 150 |  |  |
| ungated | F-D-f2c64e1b49-unattributed-151 | fire:open | 151 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-151 | fire:open | 151 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-151 | fire:open | 151 |  |  |  |
| ungated | F-D-f2c64e1b49-anomaly0-151 | fire:open | 151 |  |  |  |
| ungated | F-D-791e7f4f42-anomaly0-151 | fire:open | 151 |  |  |  |
| ungated | F-D-918a2f0930-anomaly0-151 | fire:open | 151 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-169 | fire:open | 169 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-169 | fire:open | 169 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-171 | fire:open | 171 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-171 | fire:open | 171 |  |  |  |
| ungated | D-f7d27c5b0e | admitted | 180 | 180 |  |  |
| ungated | D-35a16085de | admitted | 180 | 180 |  | Q3_soft_delete |
| ungated | F-D-791e7f4f42-unattributed-183 | fire:open | 183 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-186 | fire:open | 186 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-186 | fire:open | 186 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-186 | fire:open | 186 |  |  |  |
| ungated | F-D-35a16085de-unattributed-186 | fire:open | 186 |  |  |  |
| ungated | F-D-35a16085de-unattributed-187 | fire:open | 187 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-190 | fire:open | 190 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-190 | fire:open | 190 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-190 | fire:open | 190 |  |  |  |
| ungated | F-D-35a16085de-unattributed-190 | fire:open | 190 |  |  |  |
| ungated | F-D-35a16085de-unattributed-192 | fire:open | 192 |  |  |  |
| ungated | F-D-35a16085de-unattributed-199 | fire:open | 199 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-207 | fire:open | 207 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-207 | fire:open | 207 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-207 | fire:open | 207 |  |  |  |
| ungated | F-D-35a16085de-unattributed-207 | fire:open | 207 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-209 | fire:open | 209 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-209 | fire:open | 209 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-209 | fire:open | 209 |  |  |  |
| ungated | F-D-35a16085de-unattributed-209 | fire:open | 209 |  |  |  |
| ungated | D-3a3235ea2e | admitted | 210 | 210 |  | Q3_soft_delete |
| ungated | F-D-35a16085de-unattributed-210 | fire:open | 210 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-221 | fire:open | 221 |  |  |  |
| ungated | F-D-35a16085de-unattributed-221 | fire:open | 221 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-223 | fire:open | 223 |  |  |  |
| ungated | F-D-35a16085de-unattributed-223 | fire:open | 223 |  |  |  |
| ungated | F-D-35a16085de-unattributed-224 | fire:open | 224 |  |  |  |
| ungated | F-D-791e7f4f42-T-D-791e7f4f42-1-g0 | fire:open | 237 |  |  |  |
| ungated | F-D-35a16085de-unattributed-238 | fire:open | 238 |  |  |  |
| ungated | F-D-35a16085de-unattributed-243 | fire:open | 243 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-246 | fire:open | 246 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-246 | fire:open | 246 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-246 | fire:open | 246 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-246 | fire:open | 246 |  |  |  |
| ungated | F-D-35a16085de-unattributed-246 | fire:open | 246 |  |  |  |
| ungated | F-D-35a16085de-unattributed-249 | fire:open | 249 |  |  |  |
| ungated | F-D-35a16085de-unattributed-251 | fire:open | 251 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-254 | fire:open | 254 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-254 | fire:open | 254 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-254 | fire:open | 254 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-254 | fire:open | 254 |  |  |  |
| ungated | F-D-35a16085de-unattributed-254 | fire:open | 254 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-255 | fire:open | 255 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-255 | fire:open | 255 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-255 | fire:open | 255 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-255 | fire:open | 255 |  |  |  |
| ungated | F-D-35a16085de-unattributed-255 | fire:open | 255 |  |  |  |
| ungated | F-D-35a16085de-unattributed-257 | fire:open | 257 |  |  |  |
| ungated | F-D-35a16085de-unattributed-259 | fire:open | 259 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-260 | fire:open | 260 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-260 | fire:open | 260 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-260 | fire:open | 260 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-260 | fire:open | 260 |  |  |  |
| ungated | F-D-35a16085de-unattributed-260 | fire:open | 260 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-263 | fire:open | 263 |  |  |  |
| ungated | F-D-35a16085de-unattributed-263 | fire:open | 263 |  |  |  |
| ungated | D-75de4f5c01 | admitted | 270 | 270 |  |  |
| ungated | F-D-35a16085de-unattributed-275 | fire:open | 275 |  |  |  |
| ungated | F-D-35a16085de-unattributed-284 | fire:open | 284 |  |  |  |
| ungated | D-39c727710e | admitted | 300 | 300 |  | P1_claire_rounding |
| ungated | F-D-39c727710e-unattributed-300 | fire:open | 300 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-300 | fire:open | 300 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-300 | fire:open | 300 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-300 | fire:open | 300 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-300 | fire:open | 300 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-300 | fire:open | 300 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-300 | fire:open | 300 |  |  |  |
| ungated | F-D-39c727710e-unattributed-304 | fire:open | 304 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-304 | fire:open | 304 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-304 | fire:open | 304 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-304 | fire:open | 304 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-304 | fire:open | 304 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-304 | fire:open | 304 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-304 | fire:open | 304 |  |  |  |
| ungated | F-D-39c727710e-unattributed-308 | fire:open | 308 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-308 | fire:open | 308 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-308 | fire:open | 308 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-308 | fire:open | 308 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-308 | fire:open | 308 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-308 | fire:open | 308 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-308 | fire:open | 308 |  |  |  |
| ungated | F-D-39c727710e-unattributed-314 | fire:open | 314 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-314 | fire:open | 314 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-314 | fire:open | 314 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-314 | fire:open | 314 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-314 | fire:open | 314 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-314 | fire:open | 314 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-314 | fire:open | 314 |  |  |  |
| ungated | F-D-35a16085de-unattributed-322 | fire:open | 322 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-324 | fire:open | 324 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-345 | fire:open | 345 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-345 | fire:open | 345 |  |  |  |
| ungated | F-D-39c727710e-unattributed-345 | fire:open | 345 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-345 | fire:open | 345 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-345 | fire:open | 345 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-345 | fire:open | 345 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-348 | fire:open | 348 |  |  |  |
| ungated | F-D-39c727710e-unattributed-353 | fire:open | 353 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-353 | fire:open | 353 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-353 | fire:open | 353 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-353 | fire:open | 353 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-353 | fire:open | 353 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-353 | fire:open | 353 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-353 | fire:open | 353 |  |  |  |
| ungated | F-D-35a16085de-unattributed-355 | fire:open | 355 |  |  |  |
| ungated | F-D-39c727710e-unattributed-357 | fire:open | 357 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-357 | fire:open | 357 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-357 | fire:open | 357 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-357 | fire:open | 357 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-357 | fire:open | 357 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-357 | fire:open | 357 |  |  |  |
| ungated | F-D-39c727710e-unattributed-360 | fire:open | 360 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-360 | fire:open | 360 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-360 | fire:open | 360 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-360 | fire:open | 360 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-360 | fire:open | 360 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-360 | fire:open | 360 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-361 | fire:open | 361 |  |  |  |
| ungated | F-D-39c727710e-unattributed-363 | fire:open | 363 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-363 | fire:open | 363 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-363 | fire:open | 363 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-363 | fire:open | 363 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-363 | fire:open | 363 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-363 | fire:open | 363 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-365 | fire:open | 365 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-365 | fire:open | 365 |  |  |  |
| ungated | F-D-39c727710e-unattributed-365 | fire:open | 365 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-365 | fire:open | 365 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-365 | fire:open | 365 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-365 | fire:open | 365 |  |  |  |
| ungated | F-D-35a16085de-unattributed-380 | fire:open | 380 |  |  |  |
| ungated | F-D-35a16085de-unattributed-385 | fire:open | 385 |  |  |  |
| ungated | D-6b50b38199 | admitted | 390 | 390 |  | Q1_active_customer |
| ungated | D-60ed2d6c2c | admitted | 390 | 390 |  | Q6_tech_names |
| ungated | D-79aec5f32f | superseded | 390 | 60 | D-6b50b38199 | Q1_active_customer |
| ungated | F-D-791e7f4f42-unattributed-442 | fire:open | 442 |  |  |  |
| ungated | F-D-791e7f4f42-unattributed-464 | fire:open | 464 |  |  |  |
| ungated | F-D-39c727710e-unattributed-476 | fire:open | 476 |  |  |  |
| ungated | F-D-3a3235ea2e-unattributed-476 | fire:open | 476 |  |  |  |
| ungated | F-D-f2c64e1b49-unattributed-476 | fire:open | 476 |  |  |  |
| ungated | F-D-75de4f5c01-unattributed-476 | fire:open | 476 |  |  |  |
| ungated | F-D-f7d27c5b0e-unattributed-476 | fire:open | 476 |  |  |  |
| ungated | F-D-918a2f0930-unattributed-476 | fire:open | 476 |  |  |  |
| ungated | F-D-6b50b38199-T-D-6b50b38199-1-g0 | fire:open | 535 |  |  |  |

## Spend (list price)

| arm | stage | model | calls | errors | tokens in | tokens out | USD |
|---|---|---|---|---|---|---|---|
| frozen | propose | claude-haiku-5-5 | 760 | 0 | 2043942 | 543973 | 0.4764 |
| governed | embed | voyage-4 | 232 | 0 | 33677 | 0 | 0.0020 |
| governed | nominate | claude-sonnet-5-5 | 98 | 0 | 1122209 | 65847 | 2.9690 |
| governed | observe | claude-haiku-4-5 | 227 | 0 | 350916 | 26493 | 0.4834 |
| governed | propose | claude-haiku-5-5 | 760 | 0 | 2182444 | 633033 | 0.5348 |
| governed | replay | claude-haiku-5-5 | 462 | 0 | 1332574 | 369275 | 0.3179 |
| governed | rerank | rerank-3 | 381 | 0 | 55574 | 0 | 0.0028 |
| governed | retry | claude-haiku-5-5 | 229 | 0 | 666509 | 226826 | 0.1801 |
| naive | embed | voyage-4 | 407 | 0 | 30493 | 0 | 0.0018 |
| naive | lesson | claude-sonnet-5-5 | 201 | 0 | 240142 | 130152 | 1.7818 |
| naive | observe | claude-haiku-4-5 | 268 | 0 | 426494 | 33097 | 0.5920 |
| naive | propose | claude-haiku-5-5 | 760 | 0 | 2851830 | 1215197 | 0.8928 |
| naive | rerank | rerank-3 | 649 | 0 | 458848 | 0 | 0.0229 |
| naive | retry | claude-haiku-5-5 | 334 | 0 | 1266837 | 638304 | 0.4458 |
| self_ref | embed | voyage-4 | 415 | 0 | 26398 | 0 | 0.0016 |
| self_ref | propose | claude-haiku-5-5 | 760 | 0 | 2815424 | 1276900 | 0.9200 |
| self_ref | rerank | rerank-3 | 649 | 0 | 424498 | 0 | 0.0212 |
| self_ref | self_grade | claude-haiku-5-5 | 600 | 0 | 678132 | 359291 | 0.2475 |
| ungated | embed | voyage-4 | 201 | 0 | 27259 | 0 | 0.0016 |
| ungated | nominate | claude-sonnet-5-5 | 94 | 0 | 1334260 | 74116 | 3.4809 |
| ungated | observe | claude-haiku-4-5 | 173 | 0 | 274527 | 20739 | 0.3782 |
| ungated | propose | claude-haiku-5-5 | 761 | 1 | 2524591 | 861436 | 0.6832 |
| ungated | rerank | rerank-3 | 431 | 0 | 236337 | 0 | 0.0118 |
| ungated | retry | claude-haiku-5-5 | 176 | 0 | 558881 | 232133 | 0.1720 |

## Knob diff against run `rehearsal-1`

Forecasts of a run whose knobs moved are that run's own registration (SPEC § 11, pilot rule).

| knob | this run | other run |
|---|---|---|
| conf_dir | "<workspace>/munch-run-a/engine/conf" | "<workspace>/munchhausen/engine/conf" |
| d1_at | 300 | 120 |
| impl_list_sep | "," | null |
| packs_dir | "<workspace>/munch-run-a/engine/packs" | "<workspace>/munchhausen/engine/packs" |
| raindrop_adjudicator_user | "adjudicator" | null |
| raindrop_debug | true | null |
| raindrop_episode_event | "episode" | null |
| raindrop_episode_properties | ["arm", "template", "idx", "stream", "run_id"] | null |
| raindrop_events | ["fire_raised", "admission", "lifecycle.*", "backtest", "draft.written", "draft.adjudicated", "injection.*"] | null |
| raindrop_output_fields | ["verdict", "status", "disposition", "reason"] | null |
| raindrop_redact_keys | ["*key", "*_key_*", "*secret*", "*password*", "*token", "*uri*", "*authorization*", "*gold*", "*truth*", "*credential*"] | null |
| raindrop_redact_values | ["mongodb(\\+srv)?://\\S+", "\\bsk-[A-Za-z0-9_-]{8,}"] | null |
| raindrop_redacted | "[redacted]" | null |
| raindrop_tracing | false | null |
| run_budget_usd | 60.0 | null |
| run_id | "run-a" | "rehearsal-1" |
| status_interval_s | 60 | null |
| status_max_fail_share | 0.05 | null |
| status_stall_s | 240 | null |
| status_window | 30 | null |
| trace_impl | "jsonl,raindrop" | "jsonl" |
| v_every | 150 | 60 |
| v_offset | 75 | 30 |
| git_sha | "5c171151316e6e9cba418117b98cc1bc06ffbfd8" | "8eda73b8209ea743c01eb46dc49197a6cf80eec6" |
| ports | {"frozen": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl,raindrop"}, "self_ref": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl,raindrop"}, "naive": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl,raindrop"}, "ungated": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl,raindrop"}, "governed": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "jev", "memory_sink": "null", "trace": "jsonl,raindrop"}} | {"frozen": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null"}, "self_ref": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null"}, "naive": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null"}, "ungated": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null"}, "governed": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "jev", "memory_sink": "null"}} |
| prompt_hashes | {"lesson": "cf15453811ae8686a6baf1fe04ff1cea9ca4e915cdc30a54dd073fda7d20289b", "nominator": "9464138adb92050b1fdc051a6a5db1d2fa5146819ecbe2dcbcb3e4c142a09048", "observer": "fa03c07f7f01e2606ce85c8bfa879c087f5110639d3396ac61fc27e1579f58be", "planted_map": "1a0b46e1faaf32fdc516e02ed8fcb7c9405a4d9ee38aef5bede635c440b41cd2", "proposer": "e809f6a7ee85ebdda5a68704537ec4113a406f0fd95a62f3c38edff47b448330", "self_grade": "d40336a6beaf5e342fe4fd7764aee6d3fa46f5726094753f967e5156e7a9ca31"} | {"lesson": "cf15453811ae8686a6baf1fe04ff1cea9ca4e915cdc30a54dd073fda7d20289b", "nominator": "a4947cde5caf494b610933fda2cbc5860d371181c49ef04ac18cbea553adc0b1", "observer": "fa03c07f7f01e2606ce85c8bfa879c087f5110639d3396ac61fc27e1579f58be", "planted_map": "1a0b46e1faaf32fdc516e02ed8fcb7c9405a4d9ee38aef5bede635c440b41cd2", "proposer": "e809f6a7ee85ebdda5a68704537ec4113a406f0fd95a62f3c38edff47b448330", "self_grade": "d40336a6beaf5e342fe4fd7764aee6d3fa46f5726094753f967e5156e7a9ca31"} |
| length | 600 | 240 |
