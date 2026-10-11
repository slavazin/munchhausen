# Evidence report — run `run-b`

Started 2026-10-11T22:17:21.428000Z, ended 2026-10-11T22:54:01.035000Z; git `60086e49b1409ea16a4782511f56e4389c1adb0a`; isolation `roles`; pack hash `71b9b2113725`; arms read: frozen, naive, ungated, governed.

Anthropic auth mode: `api_key_workspace` (presence only); run length 600; spend rows lost: 0.

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

- stage `embed`: requested voyage-4; served NONE; 987 calls answered; failed: none.
- stage `lesson`: requested claude-sonnet-5-5; served claude-sonnet-5-5; 245 calls answered; failed: none.
- stage `nominate`: requested claude-sonnet-5-5; served claude-sonnet-5-5; 225 calls answered; failed: none.
- stage `observe`: requested claude-haiku-4-5; served claude-haiku-4-5-20251001; 806 calls answered; failed: none.
- stage `propose`: requested claude-haiku-5-5; served claude-haiku-5-5; 3040 calls answered; failed: none.
- stage `replay`: requested claude-haiku-5-5; served claude-haiku-5-5; 568 calls answered; failed: none.
- stage `rerank`: requested rerank-3; served NONE; 1331 calls answered; failed: none.
- stage `retry`: requested claude-haiku-5-5; served claude-haiku-5-5; 836 calls answered; failed: RuntimeError × 1, ValidationError × 1.

Every figure below names the query that produced it (`manifest.json`). A forecast is printed beside its reading; a disagreement stands as one. Forecasts are the ones registered in `runs` at start, not the current `conf/forecasts.yaml`.

## Forecasts beside their readings

### F1

- **Forecast:** an arm holding a pre-D1 Q1 decision shows a calibration gap over D1_AT…D1_AT+150 above its gap over the 150 episodes before D1_AT, until a successor is admitted (margin 0.05 accuracy points (fraction)).
- **Reading:** calibration gap (mean confidence − accuracy) after minus before, per arm; frozen with the stream on is the no-decision reference.
  - `F1.ungated` = +0.130 accuracy points (calibration gap, after − before), 90% interval [+0.023, +0.250]; n = 60; population: stream episodes of arm ungated (harness failures excluded): idx 150…299 (before) vs 300…359 (after); n = smaller window. Note: held: D-a146794e50, D-ad2083cdba. frozen-referenced difference-in-differences +0.101 [-0.004, +0.207], n = 60 paired indices per window (smaller).
  - `F1.governed` = +0.158 accuracy points (calibration gap, after − before), 90% interval [+0.078, +0.233]; n = 150; population: stream episodes of arm governed (harness failures excluded): idx 150…299 (before) vs 300…449 (after); n = smaller window. Note: held: D-5b38827bd9. frozen-referenced difference-in-differences +0.118 [+0.043, +0.193], n = 150 paired indices per window (smaller).
- **Verdict** `F1.ungated`: within the margin: the reading does not resolve the forecast at this margin.
- **Verdict** `F1.governed`: above the margin: the reading agrees with the forecast.

### F2

- **Forecast:** under a 0.20 poison rate, governed admits 0 N1-derived decisions; naive and ungated each admit ≥ 1 (margin 0.0 decisions).
- **Reading:** planted_map N1-derived admitted count per arm.
  - `planted_count.N1.frozen` = 0 decisions; n = 0; population: decisions of arm frozen mapped by the planted-map judge.
  - `planted_count.N1.self_ref` = 0 decisions; n = 0; population: decisions of arm self_ref mapped by the planted-map judge.
  - `planted_count.N1.naive` = 0 decisions; n = 239; population: decisions of arm naive mapped by the planted-map judge.
  - `planted_count.N1.ungated` = 0 decisions; n = 13; population: decisions of arm ungated mapped by the planted-map judge.
  - `planted_count.N1.governed` = 0 decisions; n = 3; population: decisions of arm governed mapped by the planted-map judge.
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
  - `F4.naive-governed` = — episodes; n = 0; population: drift D1 at idx 300; arms naive, governed. Note: governed: 210 (D-5b38827bd9 superseded by D-3c7418b437); naive: — (never held). One drift event per arm: no interval.
  - `F4.ungated-governed` = -150.0 episodes; n = 1; population: drift D1 at idx 300; arms ungated, governed. Note: governed: 210 (D-5b38827bd9 superseded by D-3c7418b437); ungated: 60 (D-ad2083cdba superseded by D-612e7b46e7). One drift event per arm: no interval.
- **Verdict** `F4.naive-governed`: unread: the reading's inputs are missing or an arm did not resolve (see note).
- **Verdict** `F4.ungated-governed`: below the negative margin: the reading disagrees with the forecast.

### F5

- **Forecast:** on quirk-bearing stream questions after round 10, governed accuracy is above naive's (margin 0.05 accuracy (fraction)).
- **Reading:** paired difference governed − naive, same questions by index.
  - `paired_accuracy.governed-naive` = +0.154 accuracy (fraction), 90% interval [+0.102, +0.205]; n = 254; population: quirk-bearing stream questions with idx ≥ 300 (round ≥ 10), paired by idx, same question_id, no harness failure.
- **Verdict** `F5`: above the margin: the reading agrees with the forecast.

### F6

- **Forecast:** on quirk-bearing stream questions after round 10, governed accuracy is above ungated's (the gate's effect) (margin 0.05 accuracy (fraction)).
- **Reading:** paired difference governed − ungated, same questions by index.
  - `paired_accuracy.governed-ungated` = -0.472 accuracy (fraction), 90% interval [-0.524, -0.417]; n = 254; population: quirk-bearing stream questions with idx ≥ 300 (round ≥ 10), paired by idx, same question_id, no harness failure.
- **Verdict** `F6`: below the negative margin: the reading disagrees with the forecast.

### F7

- **Forecast:** on control stream questions after round 10, governed accuracy is above ungated's (poison-derived decisions that ungated admits break questions they should not touch) (margin 0.05 accuracy (fraction)).
- **Reading:** paired difference governed − ungated, same questions by index, controls only.
  - `paired_accuracy.governed-ungated` = +0.000 accuracy (fraction), 90% interval [+0.000, +0.000]; n = 46; population: control stream questions (no quirk template) with idx ≥ 300 (round ≥ 10), paired by idx, same question_id, no harness failure.
- **Verdict** `F7`: within the margin: the reading does not resolve the forecast at this margin.

## Paired difference against `frozen` (rolling, by stream index)

| arm | idx | difference | interval | n pairs |
|---|---|---|---|---|
| naive | 0–29 | +0.000 | [+0.000, +0.000] | 30 |
| naive | 0–59 | +0.050 | [+0.017, +0.100] | 60 |
| naive | 0–89 | +0.056 | [+0.022, +0.100] | 90 |
| naive | 30–119 | +0.056 | [+0.011, +0.111] | 90 |
| naive | 60–149 | +0.011 | [-0.033, +0.056] | 90 |
| naive | 90–179 | +0.011 | [-0.033, +0.056] | 90 |
| naive | 120–209 | +0.067 | [+0.022, +0.122] | 90 |
| naive | 150–239 | +0.122 | [+0.067, +0.178] | 90 |
| naive | 180–269 | +0.111 | [+0.056, +0.167] | 90 |
| naive | 210–299 | +0.078 | [+0.022, +0.133] | 90 |
| naive | 240–329 | +0.056 | [+0.000, +0.111] | 90 |
| naive | 270–359 | +0.056 | [+0.000, +0.111] | 90 |
| naive | 300–389 | +0.033 | [-0.011, +0.078] | 90 |
| naive | 330–419 | +0.033 | [+0.011, +0.067] | 90 |
| naive | 360–449 | +0.056 | [+0.022, +0.100] | 90 |
| naive | 390–479 | +0.089 | [+0.044, +0.144] | 90 |
| naive | 420–509 | +0.067 | [+0.022, +0.111] | 90 |
| naive | 450–539 | +0.033 | [+0.011, +0.067] | 90 |
| naive | 480–569 | +0.000 | [+0.000, +0.000] | 90 |
| naive | 510–599 | +0.022 | [+0.000, +0.056] | 90 |
| ungated | 0–29 | +0.000 | [+0.000, +0.000] | 30 |
| ungated | 0–59 | +0.000 | [+0.000, +0.000] | 60 |
| ungated | 0–89 | +0.033 | [+0.011, +0.067] | 90 |
| ungated | 30–119 | +0.078 | [+0.033, +0.133] | 90 |
| ungated | 60–149 | +0.156 | [+0.078, +0.233] | 90 |
| ungated | 90–179 | +0.233 | [+0.144, +0.322] | 90 |
| ungated | 120–209 | +0.322 | [+0.222, +0.433] | 90 |
| ungated | 150–239 | +0.400 | [+0.300, +0.500] | 90 |
| ungated | 180–269 | +0.456 | [+0.356, +0.556] | 90 |
| ungated | 210–299 | +0.500 | [+0.411, +0.589] | 90 |
| ungated | 240–329 | +0.489 | [+0.400, +0.578] | 90 |
| ungated | 270–359 | +0.389 | [+0.311, +0.478] | 90 |
| ungated | 300–389 | +0.400 | [+0.311, +0.489] | 90 |
| ungated | 330–419 | +0.411 | [+0.322, +0.500] | 90 |
| ungated | 360–449 | +0.578 | [+0.489, +0.667] | 90 |
| ungated | 390–479 | +0.600 | [+0.511, +0.689] | 90 |
| ungated | 420–509 | +0.689 | [+0.600, +0.778] | 90 |
| ungated | 450–539 | +0.700 | [+0.622, +0.778] | 90 |
| ungated | 480–569 | +0.756 | [+0.678, +0.822] | 90 |
| ungated | 510–599 | +0.678 | [+0.600, +0.767] | 90 |
| governed | 0–29 | +0.000 | [+0.000, +0.000] | 30 |
| governed | 0–59 | +0.000 | [+0.000, +0.000] | 60 |
| governed | 0–89 | +0.000 | [+0.000, +0.000] | 90 |
| governed | 30–119 | +0.000 | [+0.000, +0.000] | 90 |
| governed | 60–149 | +0.056 | [+0.022, +0.100] | 90 |
| governed | 90–179 | +0.122 | [+0.067, +0.178] | 90 |
| governed | 120–209 | +0.178 | [+0.122, +0.244] | 90 |
| governed | 150–239 | +0.189 | [+0.122, +0.256] | 90 |
| governed | 180–269 | +0.200 | [+0.133, +0.278] | 90 |
| governed | 210–299 | +0.256 | [+0.178, +0.333] | 90 |
| governed | 240–329 | +0.244 | [+0.167, +0.322] | 90 |
| governed | 270–359 | +0.189 | [+0.122, +0.256] | 90 |
| governed | 300–389 | +0.089 | [+0.044, +0.144] | 90 |
| governed | 330–419 | +0.056 | [+0.022, +0.100] | 90 |
| governed | 360–449 | +0.100 | [+0.056, +0.156] | 90 |
| governed | 390–479 | +0.089 | [+0.044, +0.144] | 90 |
| governed | 420–509 | +0.156 | [+0.100, +0.222] | 90 |
| governed | 450–539 | +0.244 | [+0.178, +0.322] | 90 |
| governed | 480–569 | +0.344 | [+0.267, +0.433] | 90 |
| governed | 510–599 | +0.322 | [+0.244, +0.400] | 90 |

## Observation novelty by round (E8; exploratory, not pre-registered)

novelty(arm, r) = mean over the arm's reducible observations written in round r (disposition ≠ noise, via ≠ injection) of the minimum cosine distance to any of the arm's observations from rounds < r, on the run's registered embedder. Round 0 is undefined. Drifts: {'D1': 300}.

| arm | round | novelty (cosine distance) | n observations | n earlier |
|---|---|---|---|---|
| naive | 1 | 0.1620 | 18 | 12 |
| naive | 2 | 0.2007 | 14 | 30 |
| naive | 3 | 0.1356 | 11 | 44 |
| naive | 4 | 0.1388 | 12 | 55 |
| naive | 5 | 0.1222 | 12 | 67 |
| naive | 6 | 0.0878 | 9 | 79 |
| naive | 7 | 0.0832 | 12 | 88 |
| naive | 8 | 0.0815 | 10 | 100 |
| naive | 9 | 0.0781 | 8 | 110 |
| naive | 10 | 0.0922 | 14 | 118 |
| naive | 11 | 0.1007 | 11 | 132 |
| naive | 12 | 0.1147 | 12 | 143 |
| naive | 13 | 0.1309 | 11 | 155 |
| naive | 14 | 0.0788 | 14 | 166 |
| naive | 15 | 0.0848 | 9 | 180 |
| naive | 16 | 0.0762 | 11 | 189 |
| naive | 17 | 0.0913 | 19 | 200 |
| naive | 18 | 0.0627 | 15 | 219 |
| naive | 19 | 0.0822 | 11 | 234 |
| ungated | 1 | 0.1473 | 21 | 13 |
| ungated | 2 | 0.1896 | 16 | 34 |
| ungated | 3 | 0.1402 | 11 | 50 |
| ungated | 4 | 0.1524 | 8 | 61 |
| ungated | 5 | 0.1018 | 7 | 69 |
| ungated | 6 | 0.1535 | 3 | 76 |
| ungated | 7 | 0.1217 | 2 | 79 |
| ungated | 8 | 0.1868 | 1 | 81 |
| ungated | 9 | 0.1018 | 1 | 82 |
| ungated | 10 | 0.0953 | 6 | 83 |
| ungated | 11 | 0.0815 | 10 | 89 |
| ungated | 12 | 0.1351 | 2 | 99 |
| ungated | 13 | 0.1455 | 1 | 101 |
| ungated | 14 | 0.1346 | 2 | 102 |
| ungated | 15 | 0.0975 | 1 | 104 |
| ungated | 19 | 0.2259 | 2 | 105 |
| governed | 1 | 0.1595 | 19 | 9 |
| governed | 2 | 0.1770 | 17 | 28 |
| governed | 3 | 0.1119 | 14 | 45 |
| governed | 4 | 0.1402 | 9 | 59 |
| governed | 5 | 0.0978 | 10 | 68 |
| governed | 6 | 0.1436 | 13 | 78 |
| governed | 7 | 0.1053 | 9 | 91 |
| governed | 8 | 0.0929 | 8 | 100 |
| governed | 9 | 0.1077 | 7 | 108 |
| governed | 10 | 0.0778 | 14 | 115 |
| governed | 11 | 0.0782 | 12 | 129 |
| governed | 12 | 0.0971 | 17 | 141 |
| governed | 13 | 0.0824 | 13 | 158 |
| governed | 14 | 0.0734 | 13 | 171 |
| governed | 15 | 0.0776 | 15 | 184 |
| governed | 16 | 0.0477 | 14 | 199 |
| governed | 17 | 0.0938 | 8 | 213 |
| governed | 18 | 0.0665 | 12 | 221 |
| governed | 19 | 0.0818 | 9 | 233 |

## Readings

- `frozen.stream_accuracy` = 0.325 accuracy (fraction); n = 600; population: stream episodes of arm frozen (0 harness failures excluded).
- `frozen.calibration_gap` = +0.307 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm frozen (0 harness failures excluded).
- `frozen.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm frozen.
- `naive.stream_accuracy` = 0.377 accuracy (fraction); n = 600; population: stream episodes of arm naive (0 harness failures excluded).
- `naive.calibration_gap` = +0.118 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm naive (0 harness failures excluded).
- `naive.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm naive.
- `ungated.stream_accuracy` = 0.748 accuracy (fraction); n = 600; population: stream episodes of arm ungated (0 harness failures excluded).
- `ungated.calibration_gap` = -0.113 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm ungated (0 harness failures excluded).
- `ungated.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm ungated.
- `governed.stream_accuracy` = 0.478 accuracy (fraction); n = 600; population: stream episodes of arm governed (0 harness failures excluded).
- `governed.calibration_gap` = +0.138 accuracy points (mean confidence − accuracy); n = 600; population: stream episodes of arm governed (0 harness failures excluded).
- `governed.errored_episodes` = 0 episodes; n = 600; population: stream episodes of arm governed.
- `stale_applied.ungated` = 0.400 share of episodes; n = 65; population: stream episodes of arm ungated with idx ≥ 300 on Q1_active_customer templates (L11: ≥ LABEL_HORIZON after admission).
- `stale_applied.governed` = 0.631 share of episodes; n = 65; population: stream episodes of arm governed with idx ≥ 300 on Q1_active_customer templates (L11: ≥ LABEL_HORIZON after admission).
- `quirk_recall.frozen` = 0.000 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm frozen.
- `quirk_recall.self_ref` = 0.000 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm self_ref.
- `quirk_recall.naive` = 0.800 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm naive. Note: P1_claire_rounding, Q3_soft_delete, Q5_revenue, Q6_tech_names.
- `quirk_recall.ungated` = 1.000 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm ungated. Note: P1_claire_rounding, Q1_active_customer, Q3_soft_delete, Q5_revenue, Q6_tech_names.
- `quirk_recall.governed` = 0.800 share of template quirks; n = 5; population: template quirks of the pack; decisions of arm governed. Note: P1_claire_rounding, Q1_active_customer, Q3_soft_delete, Q6_tech_names.
- `backtest.admit_rate.governed` = 0.167 share of backtests; n = 18; population: organic backtests of arm governed.
- `backtest.fixed_hist.governed` = {0: 9, 1: 4, 2: 1, 3: 2, 6: 1, 8: 1} backtests per fixed count; n = 18; population: organic backtests of arm governed.
- `backtest.broken_hist.governed` = {0: 15, 1: 1, 3: 2} backtests per broken count; n = 18; population: organic backtests of arm governed.
- `backtest.premise.governed` = 0.246 share of encoded misses fixed; n = 57; population: paired-replay samples whose baseline missed on the draft's quirk, first 10 organic backtests of arm governed. Note: § 12 premise (≥ 50%): unread (proxy); PROXY for 6 of 10 backtests (draft not quirk-mapped): every baseline miss counted.
- `supersession_audit.ungated` = 3 supersessions after a dispositive fire; n = 3; population: superseded decisions of arm ungated.
- `supersession_audit.governed` = 1 supersessions after a dispositive fire; n = 1; population: superseded decisions of arm governed.
- `E9.self_ref-over-ungated` = — share of lead indices; n = 0; population: quirk-bearing stream indices where ungated missed and self_ref hit.
- `E9.self_ref-over-governed` = — share of lead indices; n = 0; population: quirk-bearing stream indices where governed missed and self_ref hit.
- `E9.naive-over-ungated` = 0.353 share of lead indices; n = 17; population: quirk-bearing stream indices where ungated missed and naive hit.
- `E9.naive-over-governed` = 0.229 share of lead indices; n = 35; population: quirk-bearing stream indices where governed missed and naive hit.
- `spend.usd.frozen` = 0.475 USD (list price); n = 760; population: model calls tagged arm frozen.
- `spend.usd_per_episode.frozen` = 0.001 USD per stream episode; n = 600; population: model calls tagged arm frozen / stream episodes.
- `spend.usd.governed` = 7.507 USD (list price); n = 2683; population: model calls tagged arm governed.
- `spend.usd_per_episode.governed` = 0.013 USD per stream episode; n = 600; population: model calls tagged arm governed / stream episodes.
- `spend.usd.naive` = 4.365 USD (list price); n = 2877; population: model calls tagged arm naive. Note: 2 failed calls.
- `spend.usd_per_episode.naive` = 0.007 USD per stream episode; n = 600; population: model calls tagged arm naive / stream episodes.
- `spend.usd.ungated` = 3.183 USD (list price); n = 1720; population: model calls tagged arm ungated.
- `spend.usd_per_episode.ungated` = 0.005 USD per stream episode; n = 600; population: model calls tagged arm ungated / stream episodes.
- `models.served.embed` = ['none'] model ids; n = 987; population: model calls of stage embed. Note: requested voyage-4.
- `models.served.lesson` = ['claude-sonnet-5-5'] model ids; n = 245; population: model calls of stage lesson. Note: requested claude-sonnet-5-5.
- `models.served.nominate` = ['claude-sonnet-5-5'] model ids; n = 225; population: model calls of stage nominate. Note: requested claude-sonnet-5-5.
- `models.served.observe` = ['claude-haiku-4-5-20251001'] model ids; n = 806; population: model calls of stage observe. Note: requested claude-haiku-4-5.
- `models.served.propose` = ['claude-haiku-5-5'] model ids; n = 3040; population: model calls of stage propose. Note: requested claude-haiku-5-5.
- `models.served.replay` = ['claude-haiku-5-5'] model ids; n = 568; population: model calls of stage replay. Note: requested claude-haiku-5-5.
- `models.served.rerank` = ['none'] model ids; n = 1331; population: model calls of stage rerank. Note: requested rerank-3.
- `models.served.retry` = ['claude-haiku-5-5'] model ids; n = 838; population: model calls of stage retry. Note: requested claude-haiku-5-5; failed: RuntimeError × 1, ValidationError × 1.
- `lifecycle.naive` = {'admitted': 88, 'converged': 147, 'moot': 4} decisions per lifecycle status; n = 239; population: decisions of arm naive. Note: converged = merged into a successor; not a supersession, never a drift resolution.
- `lifecycle.ungated` = {'admitted': 10, 'superseded': 3} decisions per lifecycle status; n = 13; population: decisions of arm ungated. Note: converged = merged into a successor; not a supersession, never a drift resolution.
- `lifecycle.governed` = {'admitted': 2, 'superseded': 1} decisions per lifecycle status; n = 3; population: decisions of arm governed. Note: converged = merged into a successor; not a supersession, never a drift resolution.
- `floor.rewires.ungated` = [{'logical': 'transactions', 'view': 'transactions__D-1b6d28e154', 'decision_id': 'D-1b6d28e154'}] rewired collections; n = 1; population: tool_access rows of arm ungated.
- `floor.view_filtered.ungated` = 420 episodes; n = 600; population: stream episodes of arm ungated whose pipeline ran through a view. Note: first at idx 180.
- `floor.rewires.governed` = [{'logical': 'transactions', 'view': 'transactions__D-1a1e0fb937', 'decision_id': 'D-1a1e0fb937'}] rewired collections; n = 1; population: tool_access rows of arm governed.
- `floor.view_filtered.governed` = 420 episodes; n = 600; population: stream episodes of arm governed whose pipeline ran through a view. Note: first at idx 180.
- `injection.drafts` = 0 drafts; n = 0; population: drafts with source injection.
- `injection.backtests` = {} backtests per verdict; n = 0; population: backtests of injection drafts.
- `injection.episodes` = 0 episodes; n = 0; population: episodes with stream injection.
- `injection.events` = {} trace events; n = 0; population: injection.* trace events.
- `sandbox.guard_refusals.frozen` = 0 refused pipelines; n = 760; population: episodes of arm frozen.
- `sandbox.guard_refusals.self_ref` = 0 refused pipelines; n = 0; population: episodes of arm self_ref.
- `sandbox.guard_refusals.naive` = 0 refused pipelines; n = 760; population: episodes of arm naive.
- `sandbox.guard_refusals.ungated` = 0 refused pipelines; n = 760; population: episodes of arm ungated.
- `sandbox.guard_refusals.governed` = 0 refused pipelines; n = 760; population: episodes of arm governed.
- `spend.not_metered` = ['typesafe lens panel'] call kinds; n = 0; population: model calls outside the Anthropic and Voyage call paths. Note: these calls are not metered: spend readings exclude their cost and tokens.
- `E8.lead.naive` = — episodes; n = 0; population: novelty rounds of arm naive; dispositive fires of arm naive on Q1 decisions at idx ≥ 300. Note: exploratory, not pre-registered; no round after the drift exceeds pre-drift mean + 2 SD (0.206).
- `E8.lead.ungated` = -289.0 episodes; n = 1; population: novelty rounds of arm ungated; dispositive fires of arm ungated on Q1 decisions at idx ≥ 300. Note: exploratory, not pre-registered; novelty alarm at round 19 (idx 599, novelty 0.226 > 0.208 = pre-drift mean + 2 SD over 9 rounds); first fire at idx 310.
- `E8.lead.governed` = — episodes; n = 0; population: novelty rounds of arm governed; dispositive fires of arm governed on Q1 decisions at idx ≥ 300. Note: exploratory, not pre-registered; no round after the drift exceeds pre-drift mean + 2 SD (0.186).

## Curves (per arm, per round of stream episodes)

| arm | round | idx | n | accuracy | self-assessed | calibration gap |
|---|---|---|---|---|---|---|
| frozen | 0 | 0–29 | 30 | 0.467 | 0.712 | +0.245 |
| frozen | 1 | 30–59 | 30 | 0.200 | 0.612 | +0.412 |
| frozen | 2 | 60–89 | 30 | 0.267 | 0.565 | +0.298 |
| frozen | 3 | 90–119 | 30 | 0.333 | 0.652 | +0.318 |
| frozen | 4 | 120–149 | 30 | 0.367 | 0.647 | +0.280 |
| frozen | 5 | 150–179 | 30 | 0.267 | 0.618 | +0.352 |
| frozen | 6 | 180–209 | 30 | 0.367 | 0.620 | +0.253 |
| frozen | 7 | 210–239 | 30 | 0.433 | 0.592 | +0.158 |
| frozen | 8 | 240–269 | 30 | 0.367 | 0.642 | +0.275 |
| frozen | 9 | 270–299 | 30 | 0.400 | 0.663 | +0.263 |
| frozen | 10 | 300–329 | 30 | 0.300 | 0.613 | +0.313 |
| frozen | 11 | 330–359 | 30 | 0.400 | 0.667 | +0.267 |
| frozen | 12 | 360–389 | 30 | 0.267 | 0.620 | +0.353 |
| frozen | 13 | 390–419 | 30 | 0.433 | 0.625 | +0.192 |
| frozen | 14 | 420–449 | 30 | 0.233 | 0.613 | +0.380 |
| frozen | 15 | 450–479 | 30 | 0.333 | 0.619 | +0.286 |
| frozen | 16 | 480–509 | 30 | 0.267 | 0.662 | +0.395 |
| frozen | 17 | 510–539 | 30 | 0.267 | 0.677 | +0.410 |
| frozen | 18 | 540–569 | 30 | 0.133 | 0.560 | +0.427 |
| frozen | 19 | 570–599 | 30 | 0.400 | 0.653 | +0.253 |
| naive | 0 | 0–29 | 30 | 0.467 | 0.695 | +0.228 |
| naive | 1 | 30–59 | 30 | 0.300 | 0.445 | +0.145 |
| naive | 2 | 60–89 | 30 | 0.333 | 0.396 | +0.062 |
| naive | 3 | 90–119 | 30 | 0.333 | 0.448 | +0.115 |
| naive | 4 | 120–149 | 30 | 0.333 | 0.489 | +0.156 |
| naive | 5 | 150–179 | 30 | 0.333 | 0.427 | +0.093 |
| naive | 6 | 180–209 | 30 | 0.533 | 0.445 | -0.088 |
| naive | 7 | 210–239 | 30 | 0.567 | 0.474 | -0.093 |
| naive | 8 | 240–269 | 30 | 0.400 | 0.479 | +0.079 |
| naive | 9 | 270–299 | 30 | 0.467 | 0.555 | +0.088 |
| naive | 10 | 300–329 | 30 | 0.367 | 0.497 | +0.130 |
| naive | 11 | 330–359 | 30 | 0.433 | 0.553 | +0.120 |
| naive | 12 | 360–389 | 30 | 0.267 | 0.532 | +0.265 |
| naive | 13 | 390–419 | 30 | 0.500 | 0.518 | +0.018 |
| naive | 14 | 420–449 | 30 | 0.333 | 0.528 | +0.195 |
| naive | 15 | 450–479 | 30 | 0.433 | 0.502 | +0.068 |
| naive | 16 | 480–509 | 30 | 0.267 | 0.477 | +0.210 |
| naive | 17 | 510–539 | 30 | 0.267 | 0.493 | +0.227 |
| naive | 18 | 540–569 | 30 | 0.133 | 0.440 | +0.307 |
| naive | 19 | 570–599 | 30 | 0.467 | 0.495 | +0.028 |
| ungated | 0 | 0–29 | 30 | 0.467 | 0.687 | +0.220 |
| ungated | 1 | 30–59 | 30 | 0.200 | 0.612 | +0.412 |
| ungated | 2 | 60–89 | 30 | 0.367 | 0.562 | +0.195 |
| ungated | 3 | 90–119 | 30 | 0.467 | 0.655 | +0.188 |
| ungated | 4 | 120–149 | 30 | 0.600 | 0.618 | +0.018 |
| ungated | 5 | 150–179 | 30 | 0.600 | 0.620 | +0.020 |
| ungated | 6 | 180–209 | 30 | 0.767 | 0.667 | -0.100 |
| ungated | 7 | 210–239 | 30 | 0.900 | 0.655 | -0.245 |
| ungated | 8 | 240–269 | 30 | 0.867 | 0.638 | -0.228 |
| ungated | 9 | 270–299 | 30 | 0.933 | 0.677 | -0.257 |
| ungated | 10 | 300–329 | 30 | 0.733 | 0.648 | -0.085 |
| ungated | 11 | 330–359 | 30 | 0.600 | 0.622 | +0.022 |
| ungated | 12 | 360–389 | 30 | 0.833 | 0.608 | -0.225 |
| ungated | 13 | 390–419 | 30 | 0.900 | 0.608 | -0.292 |
| ungated | 14 | 420–449 | 30 | 0.933 | 0.632 | -0.302 |
| ungated | 15 | 450–479 | 30 | 0.967 | 0.622 | -0.345 |
| ungated | 16 | 480–509 | 30 | 1.000 | 0.683 | -0.317 |
| ungated | 17 | 510–539 | 30 | 1.000 | 0.643 | -0.357 |
| ungated | 18 | 540–569 | 30 | 0.933 | 0.607 | -0.327 |
| ungated | 19 | 570–599 | 30 | 0.900 | 0.637 | -0.263 |
| governed | 0 | 0–29 | 30 | 0.467 | 0.710 | +0.243 |
| governed | 1 | 30–59 | 30 | 0.200 | 0.608 | +0.408 |
| governed | 2 | 60–89 | 30 | 0.267 | 0.563 | +0.297 |
| governed | 3 | 90–119 | 30 | 0.333 | 0.647 | +0.313 |
| governed | 4 | 120–149 | 30 | 0.533 | 0.637 | +0.103 |
| governed | 5 | 150–179 | 30 | 0.467 | 0.608 | +0.142 |
| governed | 6 | 180–209 | 30 | 0.533 | 0.605 | +0.072 |
| governed | 7 | 210–239 | 30 | 0.633 | 0.582 | -0.052 |
| governed | 8 | 240–269 | 30 | 0.600 | 0.610 | +0.010 |
| governed | 9 | 270–299 | 30 | 0.733 | 0.653 | -0.080 |
| governed | 10 | 300–329 | 30 | 0.467 | 0.585 | +0.118 |
| governed | 11 | 330–359 | 30 | 0.467 | 0.640 | +0.173 |
| governed | 12 | 360–389 | 30 | 0.300 | 0.608 | +0.308 |
| governed | 13 | 390–419 | 30 | 0.500 | 0.622 | +0.122 |
| governed | 14 | 420–449 | 30 | 0.433 | 0.595 | +0.162 |
| governed | 15 | 450–479 | 30 | 0.333 | 0.600 | +0.267 |
| governed | 16 | 480–509 | 30 | 0.533 | 0.652 | +0.118 |
| governed | 17 | 510–539 | 30 | 0.733 | 0.661 | -0.073 |
| governed | 18 | 540–569 | 30 | 0.433 | 0.530 | +0.097 |
| governed | 19 | 570–599 | 30 | 0.600 | 0.613 | +0.013 |

## V accuracy (sealed V set)

- `frozen` at idx 75: 0.350 accuracy (fraction), n = 40 V questions.
- `frozen` at idx 225: 0.350 accuracy (fraction), n = 40 V questions.
- `frozen` at idx 375: 0.350 accuracy (fraction), n = 40 V questions.
- `frozen` at idx 525: 0.350 accuracy (fraction), n = 40 V questions.
- `naive` at idx 75: 0.400 accuracy (fraction), n = 40 V questions.
- `naive` at idx 225: 0.475 accuracy (fraction), n = 40 V questions.
- `naive` at idx 375: 0.350 accuracy (fraction), n = 40 V questions.
- `naive` at idx 525: 0.375 accuracy (fraction), n = 40 V questions.
- `ungated` at idx 75: 0.525 accuracy (fraction), n = 40 V questions.
- `ungated` at idx 225: 0.875 accuracy (fraction), n = 40 V questions.
- `ungated` at idx 375: 0.825 accuracy (fraction), n = 40 V questions.
- `ungated` at idx 525: 0.900 accuracy (fraction), n = 40 V questions.
- `governed` at idx 75: 0.350 accuracy (fraction), n = 40 V questions.
- `governed` at idx 225: 0.625 accuracy (fraction), n = 40 V questions.
- `governed` at idx 375: 0.450 accuracy (fraction), n = 40 V questions.
- `governed` at idx 525: 0.650 accuracy (fraction), n = 40 V questions.

## Lifecycle

| arm | id | status | at idx | admitted idx | superseded by | quirk (planted map) |
|---|---|---|---|---|---|---|
| governed | D-1a1e0fb937 | admitted | 180 | 180 |  | Q3_soft_delete |
| governed | F-D-1a1e0fb937-unattributed-180 | fire:open | 180 |  |  |  |
| governed | F-D-5b38827bd9-T-D-5b38827bd9-1-g0 | fire:applied | 182 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-183 | fire:open | 183 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-186 | fire:open | 186 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-187 | fire:open | 187 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-190 | fire:open | 190 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-192 | fire:open | 192 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-199 | fire:open | 199 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-204 | fire:open | 204 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-206 | fire:open | 206 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-207 | fire:open | 207 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-208 | fire:open | 208 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-209 | fire:open | 209 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-210 | fire:open | 210 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-212 | fire:open | 212 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-218 | fire:open | 218 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-221 | fire:open | 221 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-223 | fire:open | 223 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-224 | fire:open | 224 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-228 | fire:open | 228 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-230 | fire:open | 230 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-237 | fire:open | 237 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-238 | fire:open | 238 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-243 | fire:open | 243 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-246 | fire:open | 246 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-249 | fire:open | 249 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-251 | fire:open | 251 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-254 | fire:open | 254 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-255 | fire:open | 255 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-257 | fire:open | 257 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-259 | fire:open | 259 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-260 | fire:open | 260 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-263 | fire:open | 263 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-265 | fire:open | 265 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-275 | fire:open | 275 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-278 | fire:open | 278 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-280 | fire:open | 280 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-281 | fire:open | 281 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-284 | fire:open | 284 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-300 | fire:open | 300 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-302 | fire:open | 302 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-304 | fire:open | 304 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-308 | fire:open | 308 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-314 | fire:open | 314 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-321 | fire:open | 321 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-322 | fire:open | 322 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-324 | fire:open | 324 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-335 | fire:open | 335 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-341 | fire:open | 341 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-345 | fire:open | 345 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-348 | fire:open | 348 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-352 | fire:open | 352 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-353 | fire:open | 353 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-355 | fire:open | 355 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-357 | fire:open | 357 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-359 | fire:open | 359 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-360 | fire:open | 360 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-361 | fire:open | 361 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-363 | fire:open | 363 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-365 | fire:open | 365 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-366 | fire:open | 366 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-367 | fire:open | 367 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-368 | fire:open | 368 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-369 | fire:open | 369 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-370 | fire:open | 370 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-374 | fire:open | 374 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-380 | fire:open | 380 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-385 | fire:open | 385 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-387 | fire:open | 387 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-395 | fire:open | 395 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-396 | fire:open | 396 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-400 | fire:open | 400 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-402 | fire:open | 402 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-403 | fire:open | 403 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-405 | fire:open | 405 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-416 | fire:open | 416 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-418 | fire:open | 418 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-422 | fire:open | 422 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-425 | fire:open | 425 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-435 | fire:open | 435 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-436 | fire:open | 436 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-438 | fire:open | 438 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-439 | fire:open | 439 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-440 | fire:open | 440 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-442 | fire:open | 442 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-444 | fire:open | 444 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-445 | fire:open | 445 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-447 | fire:open | 447 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-449 | fire:open | 449 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-451 | fire:open | 451 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-452 | fire:open | 452 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-458 | fire:open | 458 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-459 | fire:open | 459 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-463 | fire:open | 463 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-464 | fire:open | 464 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-465 | fire:open | 465 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-466 | fire:open | 466 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-468 | fire:open | 468 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-469 | fire:open | 469 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-476 | fire:open | 476 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-477 | fire:open | 477 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-478 | fire:open | 478 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-483 | fire:open | 483 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-484 | fire:open | 484 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-487 | fire:open | 487 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-496 | fire:open | 496 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-499 | fire:open | 499 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-502 | fire:open | 502 |  |  |  |
| governed | D-3c7418b437 | admitted | 510 | 510 |  | Q1_active_customer |
| governed | D-5b38827bd9 | superseded | 510 | 120 | D-3c7418b437 | Q1_active_customer |
| governed | F-D-1a1e0fb937-unattributed-512 | fire:open | 512 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-518 | fire:open | 518 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-519 | fire:open | 519 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-526 | fire:open | 526 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-536 | fire:open | 536 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-540 | fire:open | 540 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-541 | fire:open | 541 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-542 | fire:open | 542 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-543 | fire:open | 543 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-546 | fire:open | 546 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-551 | fire:open | 551 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-554 | fire:open | 554 |  |  |  |
| governed | F-D-3c7418b437-T-D-3c7418b437-1-g0 | fire:open | 556 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-558 | fire:open | 558 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-564 | fire:open | 564 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-566 | fire:open | 566 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-567 | fire:open | 567 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-568 | fire:open | 568 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-572 | fire:open | 572 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-573 | fire:open | 573 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-575 | fire:open | 575 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-578 | fire:open | 578 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-580 | fire:open | 580 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-585 | fire:open | 585 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-587 | fire:open | 587 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-591 | fire:open | 591 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-593 | fire:open | 593 |  |  |  |
| governed | F-D-1a1e0fb937-unattributed-594 | fire:open | 594 |  |  |  |
| naive | D-a16a859bcf | admitted | 30 | 30 |  |  |
| naive | D-51bdb82345 | converged | 30 | 30 |  | P1_claire_rounding |
| naive | D-77a25e4d84 | converged | 30 | 30 |  | P1_claire_rounding |
| naive | D-d7977a4912 | converged | 30 | 30 |  |  |
| naive | D-3ff1b62582 | converged | 30 | 30 |  |  |
| naive | F-D-d3b9020502-unattributed-33 | fire:open | 33 |  |  |  |
| naive | F-D-39d69e954f-unattributed-33 | fire:applied | 33 |  |  |  |
| naive | F-D-f8f886d216-unattributed-34 | fire:applied | 34 |  |  |  |
| naive | F-D-39d69e954f-unattributed-35 | fire:applied | 35 |  |  |  |
| naive | F-D-d3b9020502-unattributed-35 | fire:open | 35 |  |  |  |
| naive | F-D-5c29fabc33-unattributed-37 | fire:applied | 37 |  |  |  |
| naive | F-D-bb1cf68e82-unattributed-37 | fire:applied | 37 |  |  |  |
| naive | F-D-5c29fabc33-unattributed-38 | fire:applied | 38 |  |  |  |
| naive | F-D-bb1cf68e82-unattributed-38 | fire:applied | 38 |  |  |  |
| naive | F-D-39d69e954f-unattributed-40 | fire:applied | 40 |  |  |  |
| naive | F-D-d3b9020502-unattributed-40 | fire:open | 40 |  |  |  |
| naive | F-D-f8f886d216-unattributed-44 | fire:applied | 44 |  |  |  |
| naive | F-D-39d69e954f-unattributed-45 | fire:applied | 45 |  |  |  |
| naive | F-D-d3b9020502-unattributed-45 | fire:open | 45 |  |  |  |
| naive | F-D-39d69e954f-unattributed-47 | fire:applied | 47 |  |  |  |
| naive | F-D-d3b9020502-unattributed-47 | fire:open | 47 |  |  |  |
| naive | F-D-79444daf09-unattributed-49 | fire:applied | 49 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-49 | fire:open | 49 |  |  |  |
| naive | F-D-5c29fabc33-unattributed-50 | fire:applied | 50 |  |  |  |
| naive | F-D-bb1cf68e82-unattributed-50 | fire:applied | 50 |  |  |  |
| naive | F-D-5c29fabc33-unattributed-54 | fire:applied | 54 |  |  |  |
| naive | F-D-bb1cf68e82-unattributed-54 | fire:applied | 54 |  |  |  |
| naive | F-D-39d69e954f-unattributed-58 | fire:applied | 58 |  |  |  |
| naive | F-D-d3b9020502-unattributed-58 | fire:open | 58 |  |  |  |
| naive | F-D-5c29fabc33-unattributed-59 | fire:applied | 59 |  |  |  |
| naive | F-D-bb1cf68e82-unattributed-59 | fire:applied | 59 |  |  |  |
| naive | D-8c621d1d18 | admitted | 60 | 60 |  |  |
| naive | D-8d3abb82b5 | admitted | 60 | 60 |  |  |
| naive | D-d963adc21b | admitted | 60 | 60 |  |  |
| naive | D-a677ad5583 | admitted | 60 | 60 |  |  |
| naive | D-cf5fb2e0e1 | admitted | 60 | 60 |  |  |
| naive | D-bb1cf68e82 | converged | 60 | 30 |  |  |
| naive | D-5c29fabc33 | converged | 60 | 30 |  |  |
| naive | D-c6f8956c85 | converged | 60 | 60 |  |  |
| naive | D-d1594bf63c | converged | 60 | 60 |  |  |
| naive | F-D-795d19c784-unattributed-61 | fire:applied | 61 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-61 | fire:applied | 61 |  |  |  |
| naive | F-D-39d69e954f-unattributed-61 | fire:applied | 61 |  |  |  |
| naive | F-D-d3b9020502-unattributed-61 | fire:open | 61 |  |  |  |
| naive | F-D-c4734f40ac-unattributed-64 | fire:applied | 64 |  |  |  |
| naive | F-D-795d19c784-unattributed-64 | fire:applied | 64 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-64 | fire:applied | 64 |  |  |  |
| naive | F-D-39d69e954f-unattributed-64 | fire:applied | 64 |  |  |  |
| naive | F-D-d3b9020502-unattributed-64 | fire:open | 64 |  |  |  |
| naive | F-D-c4734f40ac-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-795d19c784-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-65cf4078b6-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-39d69e954f-unattributed-65 | fire:applied | 65 |  |  |  |
| naive | F-D-d3b9020502-unattributed-65 | fire:open | 65 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-67 | fire:applied | 67 |  |  |  |
| naive | F-D-39d69e954f-unattributed-67 | fire:applied | 67 |  |  |  |
| naive | F-D-d3b9020502-unattributed-67 | fire:open | 67 |  |  |  |
| naive | F-D-090415eea9-unattributed-67 | fire:applied | 67 |  |  |  |
| naive | F-D-d963adc21b-unattributed-71 | fire:open | 71 |  |  |  |
| naive | F-D-c4734f40ac-unattributed-72 | fire:applied | 72 |  |  |  |
| naive | F-D-795d19c784-unattributed-72 | fire:applied | 72 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-72 | fire:applied | 72 |  |  |  |
| naive | F-D-39d69e954f-unattributed-72 | fire:applied | 72 |  |  |  |
| naive | F-D-d3b9020502-unattributed-72 | fire:open | 72 |  |  |  |
| naive | F-D-308a429f48-unattributed-74 | fire:applied | 74 |  |  |  |
| naive | F-D-7ebf035508-unattributed-74 | fire:applied | 74 |  |  |  |
| naive | F-D-a677ad5583-unattributed-74 | fire:open | 74 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-74 | fire:open | 74 |  |  |  |
| naive | F-D-a6543213d8-unattributed-74 | fire:applied | 74 |  |  |  |
| naive | F-D-c4734f40ac-unattributed-76 | fire:applied | 76 |  |  |  |
| naive | F-D-795d19c784-unattributed-77 | fire:applied | 77 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-77 | fire:applied | 77 |  |  |  |
| naive | F-D-39d69e954f-unattributed-77 | fire:applied | 77 |  |  |  |
| naive | F-D-d3b9020502-unattributed-77 | fire:open | 77 |  |  |  |
| naive | F-D-65cf4078b6-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-795d19c784-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-d3b9020502-unattributed-78 | fire:open | 78 |  |  |  |
| naive | F-D-39d69e954f-unattributed-78 | fire:applied | 78 |  |  |  |
| naive | F-D-308a429f48-unattributed-79 | fire:applied | 79 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-79 | fire:open | 79 |  |  |  |
| naive | F-D-a6543213d8-unattributed-79 | fire:applied | 79 |  |  |  |
| naive | F-D-795d19c784-unattributed-82 | fire:applied | 82 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-82 | fire:applied | 82 |  |  |  |
| naive | F-D-39d69e954f-unattributed-82 | fire:applied | 82 |  |  |  |
| naive | F-D-d3b9020502-unattributed-82 | fire:open | 82 |  |  |  |
| naive | F-D-308a429f48-unattributed-89 | fire:applied | 89 |  |  |  |
| naive | F-D-7ebf035508-unattributed-89 | fire:applied | 89 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-89 | fire:open | 89 |  |  |  |
| naive | F-D-a677ad5583-unattributed-89 | fire:open | 89 |  |  |  |
| naive | F-D-a6543213d8-unattributed-89 | fire:applied | 89 |  |  |  |
| naive | D-f5abb3b84a | admitted | 90 | 90 |  |  |
| naive | D-0477b14823 | admitted | 90 | 90 |  | Q6_tech_names |
| naive | D-35dcfe8c71 | admitted | 90 | 90 |  | Q6_tech_names |
| naive | D-efbec8c845 | converged | 90 | 90 |  |  |
| naive | D-eb01eaebe1 | converged | 90 | 90 |  |  |
| naive | D-272ef8a5c8 | converged | 90 | 90 |  |  |
| naive | D-469461b28d | converged | 90 | 90 |  |  |
| naive | D-65cf4078b6 | converged | 90 | 60 |  |  |
| naive | D-c4734f40ac | converged | 90 | 60 |  |  |
| naive | D-795d19c784 | converged | 90 | 60 |  |  |
| naive | D-8f7cf89342 | converged | 90 | 90 |  |  |
| naive | F-D-9422b32b8a-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-90 | fire:open | 90 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-7ba62bae19-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-ae1146b400-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-0477b14823-unattributed-90 | fire:open | 90 |  |  |  |
| naive | F-D-39d69e954f-unattributed-90 | fire:applied | 90 |  |  |  |
| naive | F-D-d3b9020502-unattributed-90 | fire:open | 90 |  |  |  |
| naive | F-D-b5431faa4c-unattributed-91 | fire:applied | 91 |  |  |  |
| naive | F-D-b5431faa4c-unattributed-93 | fire:applied | 93 |  |  |  |
| naive | F-D-090415eea9-unattributed-95 | fire:applied | 95 |  |  |  |
| naive | F-D-308a429f48-unattributed-96 | fire:applied | 96 |  |  |  |
| naive | F-D-a6543213d8-unattributed-96 | fire:applied | 96 |  |  |  |
| naive | F-D-d963adc21b-unattributed-98 | fire:open | 98 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-102 | fire:open | 102 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-7ba62bae19-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-ae1146b400-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-0477b14823-unattributed-102 | fire:open | 102 |  |  |  |
| naive | F-D-39d69e954f-unattributed-102 | fire:applied | 102 |  |  |  |
| naive | F-D-d3b9020502-unattributed-102 | fire:open | 102 |  |  |  |
| naive | F-D-308a429f48-unattributed-104 | fire:applied | 104 |  |  |  |
| naive | F-D-7ebf035508-unattributed-104 | fire:applied | 104 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-104 | fire:open | 104 |  |  |  |
| naive | F-D-a677ad5583-unattributed-104 | fire:open | 104 |  |  |  |
| naive | F-D-a6543213d8-unattributed-104 | fire:applied | 104 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-106 | fire:open | 106 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-7ba62bae19-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-0477b14823-unattributed-106 | fire:open | 106 |  |  |  |
| naive | F-D-ae1146b400-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-39d69e954f-unattributed-106 | fire:applied | 106 |  |  |  |
| naive | F-D-d3b9020502-unattributed-106 | fire:open | 106 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-108 | fire:open | 108 |  |  |  |
| naive | F-D-308a429f48-unattributed-109 | fire:applied | 109 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-109 | fire:open | 109 |  |  |  |
| naive | F-D-a677ad5583-unattributed-109 | fire:open | 109 |  |  |  |
| naive | F-D-a6543213d8-unattributed-109 | fire:applied | 109 |  |  |  |
| naive | F-D-090415eea9-unattributed-111 | fire:applied | 111 |  |  |  |
| naive | F-D-d963adc21b-unattributed-112 | fire:open | 112 |  |  |  |
| naive | F-D-f5abb3b84a-unattributed-112 | fire:open | 112 |  |  |  |
| naive | F-D-79444daf09-unattributed-113 | fire:applied | 113 |  |  |  |
| naive | F-D-e3431344d5-unattributed-113 | fire:applied | 113 |  |  |  |
| naive | F-D-b5431faa4c-unattributed-115 | fire:applied | 115 |  |  |  |
| naive | F-D-308a429f48-unattributed-116 | fire:applied | 116 |  |  |  |
| naive | F-D-7ebf035508-unattributed-116 | fire:applied | 116 |  |  |  |
| naive | F-D-a677ad5583-unattributed-116 | fire:open | 116 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-116 | fire:open | 116 |  |  |  |
| naive | F-D-a6543213d8-unattributed-116 | fire:applied | 116 |  |  |  |
| naive | F-D-ae1146b400-unattributed-118 | fire:applied | 118 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-118 | fire:open | 118 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-118 | fire:applied | 118 |  |  |  |
| naive | F-D-7ba62bae19-unattributed-118 | fire:applied | 118 |  |  |  |
| naive | F-D-d3b9020502-unattributed-118 | fire:open | 118 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-118 | fire:applied | 118 |  |  |  |
| naive | F-D-0477b14823-unattributed-118 | fire:open | 118 |  |  |  |
| naive | F-D-39d69e954f-unattributed-118 | fire:applied | 118 |  |  |  |
| naive | D-dec9b7557b | admitted | 120 | 120 |  |  |
| naive | D-23a706ae2a | admitted | 120 | 120 |  |  |
| naive | D-35e11a0d9e | admitted | 120 | 120 |  |  |
| naive | D-0c4f86e26c | converged | 120 | 30 |  | P1_claire_rounding |
| naive | D-308a429f48 | converged | 120 | 60 |  |  |
| naive | D-ae1146b400 | converged | 120 | 90 |  |  |
| naive | D-b5431faa4c | converged | 120 | 90 |  |  |
| naive | F-D-c0e5855357-unattributed-120 | fire:applied | 120 |  |  |  |
| naive | F-D-0477b14823-unattributed-124 | fire:open | 124 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-124 | fire:open | 124 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-124 | fire:applied | 124 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-124 | fire:applied | 124 |  |  |  |
| naive | F-D-7ba62bae19-unattributed-124 | fire:applied | 124 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-124 | fire:applied | 124 |  |  |  |
| naive | F-D-b9c6fbfaaf-unattributed-124 | fire:applied | 124 |  |  |  |
| naive | F-D-39d69e954f-unattributed-124 | fire:applied | 124 |  |  |  |
| naive | F-D-c0e5855357-unattributed-125 | fire:applied | 125 |  |  |  |
| naive | F-D-7ebf035508-unattributed-127 | fire:applied | 127 |  |  |  |
| naive | F-D-a677ad5583-unattributed-127 | fire:open | 127 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-127 | fire:open | 127 |  |  |  |
| naive | F-D-a6543213d8-unattributed-127 | fire:applied | 127 |  |  |  |
| naive | F-D-c0e5855357-unattributed-128 | fire:applied | 128 |  |  |  |
| naive | F-D-0477b14823-unattributed-129 | fire:open | 129 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-129 | fire:open | 129 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-129 | fire:applied | 129 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-129 | fire:applied | 129 |  |  |  |
| naive | F-D-7ba62bae19-unattributed-129 | fire:applied | 129 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-129 | fire:applied | 129 |  |  |  |
| naive | F-D-b9c6fbfaaf-unattributed-129 | fire:applied | 129 |  |  |  |
| naive | F-D-39d69e954f-unattributed-129 | fire:applied | 129 |  |  |  |
| naive | F-D-7ebf035508-unattributed-133 | fire:applied | 133 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-133 | fire:open | 133 |  |  |  |
| naive | F-D-dec9b7557b-unattributed-133 | fire:open | 133 |  |  |  |
| naive | F-D-a677ad5583-unattributed-133 | fire:open | 133 |  |  |  |
| naive | F-D-a6543213d8-unattributed-133 | fire:applied | 133 |  |  |  |
| naive | F-D-7ebf035508-unattributed-135 | fire:applied | 135 |  |  |  |
| naive | F-D-a677ad5583-unattributed-135 | fire:open | 135 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-135 | fire:open | 135 |  |  |  |
| naive | F-D-a6543213d8-unattributed-135 | fire:applied | 135 |  |  |  |
| naive | F-D-e3431344d5-unattributed-135 | fire:applied | 135 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-138 | fire:open | 138 |  |  |  |
| naive | F-D-c0e5855357-unattributed-143 | fire:applied | 143 |  |  |  |
| naive | D-2273209acd | admitted | 150 | 150 |  |  |
| naive | D-0dc61184b3 | admitted | 150 | 150 |  |  |
| naive | D-254911151e | admitted | 150 | 150 |  |  |
| naive | D-19e7820f31 | converged | 150 | 120 |  | P1_claire_rounding |
| naive | D-6062eeb066 | converged | 150 | 150 |  | P1_claire_rounding |
| naive | D-090415eea9 | converged | 150 | 60 |  | Q3_soft_delete |
| naive | D-7ebf035508 | converged | 150 | 60 |  |  |
| naive | D-33817c5866 | converged | 150 | 60 |  |  |
| naive | D-7ba62bae19 | converged | 150 | 90 |  |  |
| naive | D-c6e757209c | converged | 150 | 150 |  |  |
| naive | F-D-2273209acd-unattributed-150 | fire:open | 150 |  |  |  |
| naive | F-D-385c975448-unattributed-150 | fire:applied | 150 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-150 | fire:open | 150 |  |  |  |
| naive | F-D-a6543213d8-unattributed-150 | fire:applied | 150 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-151 | fire:open | 151 |  |  |  |
| naive | F-D-c5d1cdeda7-unattributed-151 | fire:applied | 151 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-151 | fire:applied | 151 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-151 | fire:applied | 151 |  |  |  |
| naive | F-D-0477b14823-unattributed-151 | fire:open | 151 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-151 | fire:applied | 151 |  |  |  |
| naive | F-D-b9c6fbfaaf-unattributed-151 | fire:applied | 151 |  |  |  |
| naive | F-D-39d69e954f-unattributed-151 | fire:applied | 151 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-152 | fire:open | 152 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-153 | fire:open | 153 |  |  |  |
| naive | F-D-254911151e-unattributed-154 | fire:open | 154 |  |  |  |
| naive | F-D-e3431344d5-unattributed-154 | fire:applied | 154 |  |  |  |
| naive | F-D-a677ad5583-unattributed-154 | fire:open | 154 |  |  |  |
| naive | F-D-a67e33a904-unattributed-154 | fire:applied | 154 |  |  |  |
| naive | F-D-4e248455b8-unattributed-155 | fire:applied | 155 |  |  |  |
| naive | F-D-dec9b7557b-unattributed-156 | fire:open | 156 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-156 | fire:open | 156 |  |  |  |
| naive | F-D-a677ad5583-unattributed-156 | fire:open | 156 |  |  |  |
| naive | F-D-a6543213d8-unattributed-156 | fire:applied | 156 |  |  |  |
| naive | F-D-a67e33a904-unattributed-156 | fire:applied | 156 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-157 | fire:applied | 157 |  |  |  |
| naive | F-D-39d69e954f-unattributed-157 | fire:applied | 157 |  |  |  |
| naive | F-D-d3b9020502-unattributed-157 | fire:open | 157 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-158 | fire:open | 158 |  |  |  |
| naive | F-D-2273209acd-unattributed-159 | fire:open | 159 |  |  |  |
| naive | F-D-dec9b7557b-unattributed-159 | fire:open | 159 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-159 | fire:open | 159 |  |  |  |
| naive | F-D-a677ad5583-unattributed-159 | fire:open | 159 |  |  |  |
| naive | F-D-a6543213d8-unattributed-159 | fire:applied | 159 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-160 | fire:open | 160 |  |  |  |
| naive | F-D-2273209acd-unattributed-161 | fire:open | 161 |  |  |  |
| naive | F-D-dec9b7557b-unattributed-161 | fire:open | 161 |  |  |  |
| naive | F-D-a677ad5583-unattributed-161 | fire:open | 161 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-161 | fire:open | 161 |  |  |  |
| naive | F-D-a6543213d8-unattributed-161 | fire:applied | 161 |  |  |  |
| naive | F-D-e3431344d5-unattributed-161 | fire:applied | 161 |  |  |  |
| naive | F-D-70108a608d-unattributed-161 | fire:applied | 161 |  |  |  |
| naive | F-D-a67e33a904-unattributed-161 | fire:applied | 161 |  |  |  |
| naive | F-D-d2ebbb19d8-unattributed-165 | fire:applied | 165 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-169 | fire:open | 169 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-c5d1cdeda7-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-b9c6fbfaaf-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-39d69e954f-unattributed-169 | fire:applied | 169 |  |  |  |
| naive | F-D-d3b9020502-unattributed-169 | fire:open | 169 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-171 | fire:open | 171 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-c5d1cdeda7-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-d3b9020502-unattributed-171 | fire:open | 171 |  |  |  |
| naive | F-D-39d69e954f-unattributed-171 | fire:applied | 171 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-172 | fire:open | 172 |  |  |  |
| naive | F-D-c5d1cdeda7-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-9422b32b8a-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-0477b14823-unattributed-172 | fire:open | 172 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-b9c6fbfaaf-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-39d69e954f-unattributed-172 | fire:applied | 172 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-176 | fire:open | 176 |  |  |  |
| naive | F-D-4e248455b8-unattributed-178 | fire:applied | 178 |  |  |  |
| naive | D-b6b2c9f806 | admitted | 180 | 180 |  |  |
| naive | D-a6543213d8 | converged | 180 | 60 |  |  |
| naive | D-9422b32b8a | converged | 180 | 60 |  |  |
| naive | D-d2ebbb19d8 | converged | 180 | 90 |  |  |
| naive | D-c4911956a4 | converged | 180 | 180 |  |  |
| naive | D-e3431344d5 | converged | 180 | 60 |  |  |
| naive | D-4e248455b8 | converged | 180 | 150 |  |  |
| naive | D-c5d1cdeda7 | converged | 180 | 150 |  |  |
| naive | D-9c97880d66 | converged | 180 | 180 |  |  |
| naive | D-9887435922 | converged | 180 | 180 |  |  |
| naive | F-D-eb366cef0f-unattributed-186 | fire:applied | 186 |  |  |  |
| naive | F-D-fe31962b74-unattributed-186 | fire:applied | 186 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-186 | fire:open | 186 |  |  |  |
| naive | F-D-ebee8a09ef-unattributed-186 | fire:applied | 186 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-186 | fire:applied | 186 |  |  |  |
| naive | F-D-24a6582538-unattributed-186 | fire:applied | 186 |  |  |  |
| naive | F-D-d3b9020502-unattributed-186 | fire:open | 186 |  |  |  |
| naive | F-D-39d69e954f-unattributed-186 | fire:applied | 186 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-fe31962b74-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-ebee8a09ef-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-190 | fire:open | 190 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-d3b9020502-unattributed-190 | fire:open | 190 |  |  |  |
| naive | F-D-39d69e954f-unattributed-190 | fire:applied | 190 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-192 | fire:open | 192 |  |  |  |
| naive | F-D-a677ad5583-unattributed-194 | fire:open | 194 |  |  |  |
| naive | F-D-f7f25636cb-unattributed-194 | fire:applied | 194 |  |  |  |
| naive | F-D-d963adc21b-unattributed-195 | fire:open | 195 |  |  |  |
| naive | F-D-79444daf09-unattributed-197 | fire:applied | 197 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-197 | fire:open | 197 |  |  |  |
| naive | F-D-afd15a9d80-unattributed-197 | fire:applied | 197 |  |  |  |
| naive | F-D-2273209acd-unattributed-201 | fire:open | 201 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-201 | fire:open | 201 |  |  |  |
| naive | F-D-f7f25636cb-unattributed-201 | fire:applied | 201 |  |  |  |
| naive | F-D-254911151e-unattributed-205 | fire:open | 205 |  |  |  |
| naive | F-D-233f5845b9-unattributed-205 | fire:applied | 205 |  |  |  |
| naive | F-D-afd15a9d80-unattributed-205 | fire:applied | 205 |  |  |  |
| naive | F-D-a67e33a904-unattributed-205 | fire:applied | 205 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-207 | fire:open | 207 |  |  |  |
| naive | F-D-24a6582538-unattributed-207 | fire:applied | 207 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-207 | fire:applied | 207 |  |  |  |
| naive | F-D-ebee8a09ef-unattributed-207 | fire:applied | 207 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-207 | fire:applied | 207 |  |  |  |
| naive | F-D-fe31962b74-unattributed-207 | fire:applied | 207 |  |  |  |
| naive | F-D-b9c6fbfaaf-unattributed-207 | fire:applied | 207 |  |  |  |
| naive | F-D-39d69e954f-unattributed-207 | fire:applied | 207 |  |  |  |
| naive | F-D-24a6582538-unattributed-209 | fire:applied | 209 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-209 | fire:open | 209 |  |  |  |
| naive | F-D-b83ce0c6dc-unattributed-209 | fire:applied | 209 |  |  |  |
| naive | F-D-ebee8a09ef-unattributed-209 | fire:applied | 209 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-209 | fire:applied | 209 |  |  |  |
| naive | F-D-fe31962b74-unattributed-209 | fire:applied | 209 |  |  |  |
| naive | F-D-0477b14823-unattributed-209 | fire:open | 209 |  |  |  |
| naive | F-D-39d69e954f-unattributed-209 | fire:applied | 209 |  |  |  |
| naive | D-44af97a8e1 | admitted | 210 | 210 |  |  |
| naive | D-511c1f9bd1 | admitted | 210 | 210 |  |  |
| naive | D-24a6582538 | converged | 210 | 180 |  |  |
| naive | D-79444daf09 | converged | 210 | 30 |  |  |
| naive | D-260c27bc90 | converged | 210 | 90 |  |  |
| naive | D-a67e33a904 | converged | 210 | 150 |  |  |
| naive | D-fe31962b74 | converged | 210 | 180 |  |  |
| naive | D-afd15a9d80 | converged | 210 | 180 |  |  |
| naive | F-D-0477b14823-unattributed-210 | fire:open | 210 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-210 | fire:open | 210 |  |  |  |
| naive | F-D-ebee8a09ef-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-5d80fa02aa-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-9544a423b6-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-64c21078a8-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-39d69e954f-unattributed-210 | fire:applied | 210 |  |  |  |
| naive | F-D-c0e5855357-unattributed-212 | fire:applied | 212 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-213 | fire:open | 213 |  |  |  |
| naive | F-D-4cfba5d89e-unattributed-213 | fire:applied | 213 |  |  |  |
| naive | F-D-2273209acd-unattributed-215 | fire:open | 215 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-215 | fire:open | 215 |  |  |  |
| naive | F-D-dec9b7557b-unattributed-215 | fire:open | 215 |  |  |  |
| naive | F-D-a677ad5583-unattributed-215 | fire:open | 215 |  |  |  |
| naive | F-D-f7f25636cb-unattributed-215 | fire:applied | 215 |  |  |  |
| naive | F-D-3c7503bbd7-unattributed-215 | fire:applied | 215 |  |  |  |
| naive | F-D-4cfba5d89e-unattributed-215 | fire:applied | 215 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-220 | fire:open | 220 |  |  |  |
| naive | F-D-4cfba5d89e-unattributed-220 | fire:applied | 220 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-223 | fire:open | 223 |  |  |  |
| naive | F-D-ebee8a09ef-unattributed-223 | fire:applied | 223 |  |  |  |
| naive | F-D-5d80fa02aa-unattributed-223 | fire:applied | 223 |  |  |  |
| naive | F-D-0477b14823-unattributed-223 | fire:open | 223 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-223 | fire:applied | 223 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-223 | fire:open | 223 |  |  |  |
| naive | F-D-64c21078a8-unattributed-223 | fire:applied | 223 |  |  |  |
| naive | F-D-39d69e954f-unattributed-223 | fire:applied | 223 |  |  |  |
| naive | F-D-2273209acd-unattributed-227 | fire:open | 227 |  |  |  |
| naive | F-D-f7f25636cb-unattributed-227 | fire:applied | 227 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-227 | fire:open | 227 |  |  |  |
| naive | F-D-c0e5855357-unattributed-230 | fire:applied | 230 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-230 | fire:open | 230 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-237 | fire:open | 237 |  |  |  |
| naive | F-D-ebee8a09ef-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-5d80fa02aa-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-0477b14823-unattributed-237 | fire:open | 237 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-237 | fire:open | 237 |  |  |  |
| naive | F-D-64c21078a8-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-39d69e954f-unattributed-237 | fire:applied | 237 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-238 | fire:open | 238 |  |  |  |
| naive | D-265092ac72 | admitted | 240 | 240 |  |  |
| naive | D-8ee5e418da | admitted | 240 | 240 |  |  |
| naive | D-f2f7c34ee9 | admitted | 240 | 240 |  |  |
| naive | D-e0ae1a270a | converged | 240 | 90 |  | P1_claire_rounding |
| naive | D-f7f25636cb | converged | 240 | 180 |  |  |
| naive | D-ebee8a09ef | converged | 240 | 180 |  |  |
| naive | D-b83ce0c6dc | converged | 240 | 60 |  |  |
| naive | D-4cfba5d89e | converged | 240 | 210 |  |  |
| naive | D-9c0537b85a | converged | 240 | 240 |  |  |
| naive | D-a0d733d91d | converged | 240 | 240 |  |  |
| naive | D-2ff84077a9 | converged | 240 | 240 |  |  |
| naive | F-D-76bccd01fe-unattributed-241 | fire:applied | 241 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-241 | fire:open | 241 |  |  |  |
| naive | F-D-3700d18083-unattributed-241 | fire:applied | 241 |  |  |  |
| naive | F-D-2273209acd-unattributed-244 | fire:open | 244 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-244 | fire:open | 244 |  |  |  |
| naive | F-D-76bccd01fe-unattributed-244 | fire:applied | 244 |  |  |  |
| naive | F-D-2273209acd-unattributed-245 | fire:open | 245 |  |  |  |
| naive | F-D-76bccd01fe-unattributed-245 | fire:applied | 245 |  |  |  |
| naive | F-D-3700d18083-unattributed-245 | fire:applied | 245 |  |  |  |
| naive | F-D-64c21078a8-unattributed-246 | fire:applied | 246 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-246 | fire:open | 246 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-246 | fire:applied | 246 |  |  |  |
| naive | F-D-5d80fa02aa-unattributed-246 | fire:applied | 246 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-246 | fire:open | 246 |  |  |  |
| naive | F-D-3aaed019f6-unattributed-246 | fire:applied | 246 |  |  |  |
| naive | F-D-00edfb3dd4-unattributed-246 | fire:applied | 246 |  |  |  |
| naive | F-D-39d69e954f-unattributed-246 | fire:applied | 246 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-249 | fire:open | 249 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-250 | fire:open | 250 |  |  |  |
| naive | F-D-64c21078a8-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-251 | fire:open | 251 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-5d80fa02aa-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-251 | fire:open | 251 |  |  |  |
| naive | F-D-3aaed019f6-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-00edfb3dd4-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-39d69e954f-unattributed-251 | fire:applied | 251 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-252 | fire:open | 252 |  |  |  |
| naive | F-D-76bccd01fe-unattributed-252 | fire:applied | 252 |  |  |  |
| naive | F-D-9544a423b6-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-254 | fire:open | 254 |  |  |  |
| naive | F-D-5d80fa02aa-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-254 | fire:open | 254 |  |  |  |
| naive | F-D-00edfb3dd4-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-3aaed019f6-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-39d69e954f-unattributed-254 | fire:applied | 254 |  |  |  |
| naive | F-D-64c21078a8-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-255 | fire:open | 255 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-5d80fa02aa-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-255 | fire:open | 255 |  |  |  |
| naive | F-D-3aaed019f6-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-00edfb3dd4-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-39d69e954f-unattributed-255 | fire:applied | 255 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-259 | fire:open | 259 |  |  |  |
| naive | F-D-3aaed019f6-unattributed-259 | fire:applied | 259 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-259 | fire:open | 259 |  |  |  |
| naive | F-D-00edfb3dd4-unattributed-259 | fire:applied | 259 |  |  |  |
| naive | F-D-9544a423b6-unattributed-259 | fire:applied | 259 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-259 | fire:applied | 259 |  |  |  |
| naive | F-D-64c21078a8-unattributed-259 | fire:applied | 259 |  |  |  |
| naive | F-D-39d69e954f-unattributed-259 | fire:applied | 259 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-260 | fire:open | 260 |  |  |  |
| naive | F-D-3aaed019f6-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-9544a423b6-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-260 | fire:open | 260 |  |  |  |
| naive | F-D-00edfb3dd4-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-0477b14823-unattributed-260 | fire:open | 260 |  |  |  |
| naive | F-D-64c21078a8-unattributed-260 | fire:applied | 260 |  |  |  |
| naive | F-D-265092ac72-unattributed-263 | fire:open | 263 |  |  |  |
| naive | F-D-2273209acd-unattributed-264 | fire:open | 264 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-264 | fire:open | 264 |  |  |  |
| naive | F-D-76bccd01fe-unattributed-264 | fire:applied | 264 |  |  |  |
| naive | F-D-3700d18083-unattributed-264 | fire:applied | 264 |  |  |  |
| naive | F-D-2273209acd-unattributed-268 | fire:open | 268 |  |  |  |
| naive | F-D-76bccd01fe-unattributed-268 | fire:applied | 268 |  |  |  |
| naive | F-D-2273209acd-unattributed-269 | fire:open | 269 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-269 | fire:open | 269 |  |  |  |
| naive | D-23109b4465 | admitted | 270 | 270 |  |  |
| naive | D-f732729224 | admitted | 270 | 270 |  |  |
| naive | D-0fb9d8b07a | converged | 270 | 240 |  | P1_claire_rounding |
| naive | D-385c975448 | converged | 270 | 120 |  |  |
| naive | D-64c21078a8 | converged | 270 | 210 |  |  |
| naive | D-5d80fa02aa | converged | 270 | 210 |  |  |
| naive | D-3700d18083 | converged | 270 | 240 |  |  |
| naive | F-D-0dc61184b3-unattributed-270 | fire:open | 270 |  |  |  |
| naive | F-D-2273209acd-unattributed-273 | fire:open | 273 |  |  |  |
| naive | F-D-22d419418e-unattributed-273 | fire:applied | 273 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-277 | fire:open | 277 |  |  |  |
| naive | F-D-c0e5855357-unattributed-278 | fire:applied | 278 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-278 | fire:open | 278 |  |  |  |
| naive | F-D-265092ac72-unattributed-281 | fire:open | 281 |  |  |  |
| naive | F-D-d963adc21b-unattributed-282 | fire:open | 282 |  |  |  |
| naive | F-D-22d419418e-unattributed-283 | fire:applied | 283 |  |  |  |
| naive | F-D-3dad0a1847-unattributed-283 | fire:applied | 283 |  |  |  |
| naive | F-D-e0c9047672-unattributed-287 | fire:applied | 287 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-293 | fire:open | 293 |  |  |  |
| naive | F-D-2273209acd-unattributed-296 | fire:open | 296 |  |  |  |
| naive | F-D-22d419418e-unattributed-296 | fire:applied | 296 |  |  |  |
| naive | F-D-2273209acd-unattributed-298 | fire:open | 298 |  |  |  |
| naive | F-D-22d419418e-unattributed-298 | fire:applied | 298 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-298 | fire:open | 298 |  |  |  |
| naive | F-D-76bccd01fe-unattributed-298 | fire:applied | 298 |  |  |  |
| naive | F-D-233f5845b9-unattributed-298 | fire:applied | 298 |  |  |  |
| naive | D-35d7db4c13 | admitted | 300 | 300 |  |  |
| naive | D-24b72c58bf | converged | 300 | 150 |  | P1_claire_rounding |
| naive | D-2746a0a080 | converged | 300 | 120 |  | Q3_soft_delete |
| naive | D-e0c9047672 | converged | 300 | 180 |  |  |
| naive | D-b9c6fbfaaf | converged | 300 | 120 |  |  |
| naive | D-76bccd01fe | converged | 300 | 240 |  |  |
| naive | D-c610354ce1 | converged | 300 | 270 |  |  |
| naive | D-ed1841ae20 | converged | 300 | 300 |  |  |
| naive | F-D-0477b14823-unattributed-300 | fire:open | 300 |  |  |  |
| naive | F-D-265092ac72-unattributed-300 | fire:open | 300 |  |  |  |
| naive | F-D-00edfb3dd4-unattributed-300 | fire:applied | 300 |  |  |  |
| naive | F-D-10bd0f78a7-unattributed-300 | fire:applied | 300 |  |  |  |
| naive | F-D-22d419418e-unattributed-301 | fire:applied | 301 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-301 | fire:open | 301 |  |  |  |
| naive | F-D-f2f7c34ee9-unattributed-301 | fire:open | 301 |  |  |  |
| naive | F-D-65e482376e-unattributed-301 | fire:applied | 301 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-302 | fire:open | 302 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-302 | fire:applied | 302 |  |  |  |
| naive | F-D-f732729224-unattributed-302 | fire:open | 302 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-302 | fire:applied | 302 |  |  |  |
| naive | F-D-3aaed019f6-unattributed-302 | fire:applied | 302 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-304 | fire:open | 304 |  |  |  |
| naive | F-D-265092ac72-unattributed-304 | fire:open | 304 |  |  |  |
| naive | F-D-0477b14823-unattributed-304 | fire:open | 304 |  |  |  |
| naive | F-D-00edfb3dd4-unattributed-304 | fire:applied | 304 |  |  |  |
| naive | F-D-3aaed019f6-unattributed-304 | fire:applied | 304 |  |  |  |
| naive | F-D-f732729224-unattributed-304 | fire:open | 304 |  |  |  |
| naive | F-D-23109b4465-unattributed-304 | fire:open | 304 |  |  |  |
| naive | F-D-10bd0f78a7-unattributed-304 | fire:applied | 304 |  |  |  |
| naive | F-D-254911151e-unattributed-307 | fire:open | 307 |  |  |  |
| naive | F-D-65e482376e-unattributed-307 | fire:applied | 307 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-307 | fire:open | 307 |  |  |  |
| naive | F-D-70108a608d-unattributed-307 | fire:applied | 307 |  |  |  |
| naive | F-D-eac0f2c955-unattributed-307 | fire:applied | 307 |  |  |  |
| naive | F-D-65e482376e-unattributed-309 | fire:applied | 309 |  |  |  |
| naive | F-D-eac0f2c955-unattributed-309 | fire:applied | 309 |  |  |  |
| naive | F-D-2273209acd-unattributed-310 | fire:open | 310 |  |  |  |
| naive | F-D-22d419418e-unattributed-310 | fire:applied | 310 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-312 | fire:open | 312 |  |  |  |
| naive | F-D-65e482376e-unattributed-312 | fire:applied | 312 |  |  |  |
| naive | F-D-eac0f2c955-unattributed-312 | fire:applied | 312 |  |  |  |
| naive | F-D-d963adc21b-unattributed-315 | fire:open | 315 |  |  |  |
| naive | F-D-d963adc21b-unattributed-319 | fire:open | 319 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-320 | fire:open | 320 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-322 | fire:open | 322 |  |  |  |
| naive | F-D-265092ac72-unattributed-324 | fire:open | 324 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-327 | fire:open | 327 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-328 | fire:open | 328 |  |  |  |
| naive | F-D-2273209acd-unattributed-329 | fire:open | 329 |  |  |  |
| naive | F-D-8ee5e418da-unattributed-329 | fire:open | 329 |  |  |  |
| naive | F-D-dec9b7557b-unattributed-329 | fire:open | 329 |  |  |  |
| naive | F-D-a677ad5583-unattributed-329 | fire:open | 329 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-329 | fire:open | 329 |  |  |  |
| naive | F-D-22d419418e-unattributed-329 | fire:applied | 329 |  |  |  |
| naive | F-D-f2f7c34ee9-unattributed-329 | fire:open | 329 |  |  |  |
| naive | D-dc19024842 | admitted | 330 | 330 |  |  |
| naive | D-7060a9e54f | admitted | 330 | 330 |  | Q3_soft_delete |
| naive | D-ad61e4b320 | admitted | 330 | 330 |  |  |
| naive | D-f1cd19802f | converged | 330 | 270 |  |  |
| naive | D-f8f886d216 | converged | 330 | 30 |  |  |
| naive | D-65e482376e | converged | 330 | 300 |  |  |
| naive | D-3c7503bbd7 | converged | 330 | 210 |  |  |
| naive | D-3aaed019f6 | converged | 330 | 240 |  |  |
| naive | D-00edfb3dd4 | converged | 330 | 240 |  |  |
| naive | D-10bd0f78a7 | converged | 330 | 300 |  |  |
| naive | D-be783de17c | converged | 330 | 330 |  |  |
| naive | D-4144009ab3 | converged | 330 | 330 |  |  |
| naive | F-D-22d419418e-unattributed-333 | fire:applied | 333 |  |  |  |
| naive | F-D-2273209acd-unattributed-333 | fire:open | 333 |  |  |  |
| naive | F-D-9dc0df3747-unattributed-333 | fire:applied | 333 |  |  |  |
| naive | F-D-a677ad5583-unattributed-333 | fire:open | 333 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-333 | fire:open | 333 |  |  |  |
| naive | F-D-8ee5e418da-unattributed-333 | fire:open | 333 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-333 | fire:open | 333 |  |  |  |
| naive | F-D-265092ac72-unattributed-335 | fire:open | 335 |  |  |  |
| naive | F-D-233f5845b9-unattributed-337 | fire:applied | 337 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-337 | fire:open | 337 |  |  |  |
| naive | F-D-89b541e882-unattributed-337 | fire:applied | 337 |  |  |  |
| naive | F-D-22d419418e-unattributed-339 | fire:applied | 339 |  |  |  |
| naive | F-D-2273209acd-unattributed-339 | fire:open | 339 |  |  |  |
| naive | F-D-9dc0df3747-unattributed-339 | fire:applied | 339 |  |  |  |
| naive | F-D-a677ad5583-unattributed-339 | fire:open | 339 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-339 | fire:open | 339 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-339 | fire:open | 339 |  |  |  |
| naive | F-D-9dc0df3747-unattributed-340 | fire:applied | 340 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-340 | fire:open | 340 |  |  |  |
| naive | F-D-22d419418e-unattributed-340 | fire:applied | 340 |  |  |  |
| naive | F-D-9dc0df3747-anomaly0-340 | fire:applied | 340 |  |  |  |
| naive | F-D-ad61e4b320-anomaly0-340 | fire:open | 340 |  |  |  |
| naive | F-D-22d419418e-anomaly0-340 | fire:applied | 340 |  |  |  |
| naive | F-D-9dc0df3747-unattributed-342 | fire:applied | 342 |  |  |  |
| naive | F-D-2273209acd-unattributed-342 | fire:open | 342 |  |  |  |
| naive | F-D-8ee5e418da-unattributed-342 | fire:open | 342 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-342 | fire:open | 342 |  |  |  |
| naive | F-D-22d419418e-unattributed-342 | fire:applied | 342 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-342 | fire:open | 342 |  |  |  |
| naive | F-D-a677ad5583-unattributed-342 | fire:open | 342 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-343 | fire:open | 343 |  |  |  |
| naive | F-D-d963adc21b-unattributed-344 | fire:open | 344 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-345 | fire:open | 345 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-345 | fire:applied | 345 |  |  |  |
| naive | F-D-f732729224-unattributed-345 | fire:open | 345 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-345 | fire:applied | 345 |  |  |  |
| naive | F-D-265092ac72-unattributed-348 | fire:open | 348 |  |  |  |
| naive | F-D-c0e5855357-unattributed-349 | fire:applied | 349 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-349 | fire:open | 349 |  |  |  |
| naive | F-D-9dc0df3747-unattributed-351 | fire:applied | 351 |  |  |  |
| naive | F-D-22d419418e-unattributed-351 | fire:applied | 351 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-351 | fire:open | 351 |  |  |  |
| naive | F-D-265092ac72-unattributed-352 | fire:open | 352 |  |  |  |
| naive | F-D-265092ac72-unattributed-353 | fire:open | 353 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-355 | fire:open | 355 |  |  |  |
| naive | F-D-265092ac72-unattributed-359 | fire:open | 359 |  |  |  |
| naive | D-2197516a3f | admitted | 360 | 360 |  |  |
| naive | D-459901d01e | admitted | 360 | 360 |  |  |
| naive | D-b79b8e9be8 | converged | 360 | 300 |  | P1_claire_rounding |
| naive | D-908473c041 | converged | 360 | 360 |  | P1_claire_rounding |
| naive | D-f61ef3ac22 | converged | 360 | 360 |  | P1_claire_rounding |
| naive | D-10f772bfee | converged | 360 | 210 |  |  |
| naive | D-eac0f2c955 | converged | 360 | 300 |  |  |
| naive | D-9dc0df3747 | converged | 360 | 330 |  |  |
| naive | D-4eaf42a517 | converged | 360 | 330 |  |  |
| naive | F-D-35dcfe8c71-unattributed-360 | fire:open | 360 |  |  |  |
| naive | F-D-124cae8933-unattributed-360 | fire:applied | 360 |  |  |  |
| naive | F-D-265092ac72-unattributed-361 | fire:open | 361 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-362 | fire:open | 362 |  |  |  |
| naive | F-D-cf94cb1126-unattributed-362 | fire:applied | 362 |  |  |  |
| naive | F-D-89b541e882-unattributed-362 | fire:applied | 362 |  |  |  |
| naive | F-D-2273209acd-unattributed-364 | fire:open | 364 |  |  |  |
| naive | F-D-22d419418e-unattributed-364 | fire:applied | 364 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-364 | fire:open | 364 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-365 | fire:open | 365 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-f732729224-unattributed-365 | fire:open | 365 |  |  |  |
| naive | F-D-2f9b0a91bb-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-23109b4465-unattributed-365 | fire:open | 365 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-124cae8933-unattributed-365 | fire:applied | 365 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-365 | fire:open | 365 |  |  |  |
| naive | F-D-44af97a8e1-anomaly0-365 | fire:open | 365 |  |  |  |
| naive | F-D-eb366cef0f-anomaly0-365 | fire:applied | 365 |  |  |  |
| naive | F-D-f732729224-anomaly0-365 | fire:open | 365 |  |  |  |
| naive | F-D-2f9b0a91bb-anomaly0-365 | fire:applied | 365 |  |  |  |
| naive | F-D-23109b4465-anomaly0-365 | fire:open | 365 |  |  |  |
| naive | F-D-2a6d6ea44b-anomaly0-365 | fire:applied | 365 |  |  |  |
| naive | F-D-124cae8933-anomaly0-365 | fire:applied | 365 |  |  |  |
| naive | F-D-35dcfe8c71-anomaly0-365 | fire:open | 365 |  |  |  |
| naive | F-D-265092ac72-unattributed-366 | fire:open | 366 |  |  |  |
| naive | F-D-97f6d68e41-unattributed-367 | fire:applied | 367 |  |  |  |
| naive | F-D-c0e5855357-unattributed-367 | fire:applied | 367 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-368 | fire:open | 368 |  |  |  |
| naive | F-D-97f6d68e41-unattributed-368 | fire:applied | 368 |  |  |  |
| naive | F-D-c0e5855357-unattributed-368 | fire:applied | 368 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-368 | fire:open | 368 |  |  |  |
| naive | F-D-97f6d68e41-unattributed-369 | fire:applied | 369 |  |  |  |
| naive | F-D-c0e5855357-unattributed-369 | fire:applied | 369 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-369 | fire:open | 369 |  |  |  |
| naive | F-D-265092ac72-unattributed-370 | fire:open | 370 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-374 | fire:open | 374 |  |  |  |
| naive | F-D-97f6d68e41-unattributed-374 | fire:applied | 374 |  |  |  |
| naive | F-D-c0e5855357-unattributed-374 | fire:applied | 374 |  |  |  |
| naive | F-D-dc19024842-unattributed-375 | fire:open | 375 |  |  |  |
| naive | F-D-909085365e-unattributed-375 | fire:applied | 375 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-378 | fire:open | 378 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-380 | fire:open | 380 |  |  |  |
| naive | F-D-97f6d68e41-unattributed-383 | fire:applied | 383 |  |  |  |
| naive | F-D-c0e5855357-unattributed-383 | fire:applied | 383 |  |  |  |
| naive | F-D-22d419418e-unattributed-384 | fire:applied | 384 |  |  |  |
| naive | F-D-2273209acd-unattributed-384 | fire:open | 384 |  |  |  |
| naive | F-D-cf97e6ba9f-unattributed-384 | fire:applied | 384 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-384 | fire:open | 384 |  |  |  |
| naive | F-D-97f6d68e41-unattributed-387 | fire:applied | 387 |  |  |  |
| naive | F-D-c0e5855357-unattributed-387 | fire:applied | 387 |  |  |  |
| naive | F-D-2273209acd-unattributed-388 | fire:open | 388 |  |  |  |
| naive | F-D-22d419418e-unattributed-388 | fire:applied | 388 |  |  |  |
| naive | F-D-cf97e6ba9f-unattributed-388 | fire:applied | 388 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-388 | fire:open | 388 |  |  |  |
| naive | F-D-2273209acd-unattributed-389 | fire:open | 389 |  |  |  |
| naive | F-D-22d419418e-unattributed-389 | fire:applied | 389 |  |  |  |
| naive | F-D-cf97e6ba9f-unattributed-389 | fire:applied | 389 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-389 | fire:open | 389 |  |  |  |
| naive | D-2bd836fdd3 | admitted | 390 | 390 |  |  |
| naive | D-54a1e6bcd3 | admitted | 390 | 390 |  |  |
| naive | D-ef23240613 | admitted | 390 | 390 |  |  |
| naive | D-7df012efc2 | admitted | 390 | 390 |  |  |
| naive | D-ac0569b2c0 | converged | 390 | 330 |  |  |
| naive | D-d9a6b07e38 | converged | 390 | 360 |  | P1_claire_rounding |
| naive | D-233f5845b9 | converged | 390 | 180 |  |  |
| naive | D-89b541e882 | converged | 390 | 330 |  |  |
| naive | D-cf97e6ba9f | converged | 390 | 360 |  |  |
| naive | D-0c67e14a42 | converged | 390 | 390 |  | Q5_revenue |
| naive | D-18288fc446 | converged | 390 | 390 |  | Q5_revenue |
| naive | D-baa1633656 | converged | 390 | 150 |  | Q5_revenue |
| naive | D-97f6d68e41 | converged | 390 | 360 |  |  |
| naive | F-D-0b1f3f3777-unattributed-391 | fire:applied | 391 |  |  |  |
| naive | F-D-22d419418e-unattributed-391 | fire:applied | 391 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-393 | fire:open | 393 |  |  |  |
| naive | F-D-265092ac72-unattributed-396 | fire:open | 396 |  |  |  |
| naive | F-D-ac1d13eebd-unattributed-396 | fire:applied | 396 |  |  |  |
| naive | F-D-c0e5855357-unattributed-398 | fire:applied | 398 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-400 | fire:applied | 400 |  |  |  |
| naive | F-D-c0e5855357-unattributed-400 | fire:applied | 400 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-400 | fire:open | 400 |  |  |  |
| naive | F-D-7df012efc2-unattributed-400 | fire:open | 400 |  |  |  |
| naive | F-D-23109b4465-unattributed-403 | fire:open | 403 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-403 | fire:open | 403 |  |  |  |
| naive | F-D-a5ada3ed0c-unattributed-403 | fire:applied | 403 |  |  |  |
| naive | F-D-0477b14823-unattributed-403 | fire:open | 403 |  |  |  |
| naive | F-D-124cae8933-unattributed-403 | fire:applied | 403 |  |  |  |
| naive | F-D-f732729224-unattributed-403 | fire:open | 403 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-403 | fire:applied | 403 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-403 | fire:open | 403 |  |  |  |
| naive | F-D-22d419418e-unattributed-404 | fire:applied | 404 |  |  |  |
| naive | F-D-2273209acd-unattributed-404 | fire:open | 404 |  |  |  |
| naive | F-D-e87775e541-unattributed-404 | fire:applied | 404 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-404 | fire:open | 404 |  |  |  |
| naive | F-D-2273209acd-unattributed-407 | fire:open | 407 |  |  |  |
| naive | F-D-22d419418e-unattributed-407 | fire:applied | 407 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-407 | fire:open | 407 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-409 | fire:open | 409 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-411 | fire:open | 411 |  |  |  |
| naive | F-D-dc19024842-unattributed-411 | fire:open | 411 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-412 | fire:applied | 412 |  |  |  |
| naive | F-D-7df012efc2-unattributed-412 | fire:open | 412 |  |  |  |
| naive | F-D-c0e5855357-unattributed-412 | fire:applied | 412 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-412 | fire:open | 412 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-416 | fire:open | 416 |  |  |  |
| naive | F-D-a5ada3ed0c-unattributed-416 | fire:applied | 416 |  |  |  |
| naive | F-D-f732729224-unattributed-416 | fire:open | 416 |  |  |  |
| naive | F-D-124cae8933-unattributed-416 | fire:applied | 416 |  |  |  |
| naive | F-D-eb366cef0f-unattributed-416 | fire:applied | 416 |  |  |  |
| naive | F-D-23109b4465-unattributed-416 | fire:open | 416 |  |  |  |
| naive | F-D-2f9b0a91bb-unattributed-416 | fire:applied | 416 |  |  |  |
| naive | F-D-39d69e954f-unattributed-416 | fire:applied | 416 |  |  |  |
| naive | D-87b34a38df | admitted | 420 | 420 |  | P1_claire_rounding |
| naive | D-cb35bd47b5 | admitted | 420 | 420 |  |  |
| naive | D-a86e33fa06 | admitted | 420 | 420 |  |  |
| naive | D-6fde6c87b6 | admitted | 420 | 420 |  |  |
| naive | D-fd8dc27ecb | admitted | 420 | 420 |  |  |
| naive | D-b45a05c589 | admitted | 420 | 420 |  |  |
| naive | D-7c0335b3c7 | admitted | 420 | 420 |  |  |
| naive | D-c0e5855357 | converged | 420 | 120 |  |  |
| naive | D-eb366cef0f | converged | 420 | 120 |  | Q6_tech_names |
| naive | D-a5ada3ed0c | converged | 420 | 330 |  |  |
| naive | D-5b690c196d | converged | 420 | 330 |  |  |
| naive | F-D-54be80051c-unattributed-420 | fire:applied | 420 |  |  |  |
| naive | F-D-23109b4465-unattributed-422 | fire:open | 422 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-422 | fire:open | 422 |  |  |  |
| naive | F-D-54a1e6bcd3-unattributed-422 | fire:open | 422 |  |  |  |
| naive | F-D-124cae8933-unattributed-422 | fire:applied | 422 |  |  |  |
| naive | F-D-02abc947b2-unattributed-422 | fire:applied | 422 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-422 | fire:open | 422 |  |  |  |
| naive | F-D-7c0335b3c7-unattributed-422 | fire:open | 422 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-422 | fire:applied | 422 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-423 | fire:open | 423 |  |  |  |
| naive | F-D-fd8dc27ecb-unattributed-423 | fire:open | 423 |  |  |  |
| naive | F-D-9544a423b6-unattributed-425 | fire:applied | 425 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-425 | fire:open | 425 |  |  |  |
| naive | F-D-459901d01e-unattributed-425 | fire:open | 425 |  |  |  |
| naive | F-D-23109b4465-unattributed-425 | fire:open | 425 |  |  |  |
| naive | F-D-2f9b0a91bb-unattributed-425 | fire:applied | 425 |  |  |  |
| naive | F-D-39d69e954f-unattributed-425 | fire:applied | 425 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-426 | fire:open | 426 |  |  |  |
| naive | F-D-fd8dc27ecb-unattributed-426 | fire:open | 426 |  |  |  |
| naive | F-D-22d419418e-unattributed-430 | fire:applied | 430 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-430 | fire:open | 430 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-430 | fire:open | 430 |  |  |  |
| naive | F-D-fe3b50d1bf-unattributed-430 | fire:applied | 430 |  |  |  |
| naive | F-D-d963adc21b-unattributed-431 | fire:open | 431 |  |  |  |
| naive | F-D-d963adc21b-unattributed-432 | fire:open | 432 |  |  |  |
| naive | F-D-f5abb3b84a-unattributed-432 | fire:open | 432 |  |  |  |
| naive | F-D-7df012efc2-unattributed-435 | fire:open | 435 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-435 | fire:applied | 435 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-435 | fire:open | 435 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-436 | fire:open | 436 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-436 | fire:open | 436 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-437 | fire:open | 437 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-437 | fire:open | 437 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-438 | fire:applied | 438 |  |  |  |
| naive | F-D-7df012efc2-unattributed-438 | fire:open | 438 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-438 | fire:open | 438 |  |  |  |
| naive | F-D-6fde6c87b6-unattributed-438 | fire:open | 438 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-441 | fire:open | 441 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-441 | fire:open | 441 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-443 | fire:open | 443 |  |  |  |
| naive | F-D-fe3b50d1bf-unattributed-443 | fire:applied | 443 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-443 | fire:open | 443 |  |  |  |
| naive | F-D-a677ad5583-unattributed-443 | fire:open | 443 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-444 | fire:applied | 444 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-444 | fire:open | 444 |  |  |  |
| naive | F-D-7df012efc2-unattributed-444 | fire:open | 444 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-445 | fire:open | 445 |  |  |  |
| naive | F-D-cb35bd47b5-unattributed-445 | fire:open | 445 |  |  |  |
| naive | F-D-2f9b0a91bb-unattributed-445 | fire:applied | 445 |  |  |  |
| naive | F-D-f732729224-unattributed-445 | fire:open | 445 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-445 | fire:applied | 445 |  |  |  |
| naive | F-D-d963adc21b-unattributed-446 | fire:open | 446 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-447 | fire:applied | 447 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-447 | fire:open | 447 |  |  |  |
| naive | F-D-7df012efc2-unattributed-447 | fire:open | 447 |  |  |  |
| naive | F-D-d963adc21b-unattributed-448 | fire:open | 448 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-449 | fire:applied | 449 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-449 | fire:open | 449 |  |  |  |
| naive | F-D-7df012efc2-unattributed-449 | fire:open | 449 |  |  |  |
| naive | D-43e5b7f5c0 | admitted | 450 | 450 |  |  |
| naive | D-1cc4b91ad4 | admitted | 450 | 450 |  |  |
| naive | D-d78bbadf31 | admitted | 450 | 450 |  |  |
| naive | D-74619aed11 | admitted | 450 | 450 |  |  |
| naive | D-09a569e0d2 | admitted | 450 | 450 |  |  |
| naive | D-0e1e18cc9b | admitted | 450 | 450 |  | Q3_soft_delete |
| naive | D-18aadadff9 | admitted | 450 | 450 |  |  |
| naive | D-6d2e6c5cd3 | admitted | 450 | 450 |  |  |
| naive | D-9544a423b6 | converged | 450 | 210 |  | Q6_tech_names |
| naive | D-e45fc9214c | converged | 450 | 300 |  |  |
| naive | D-54be80051c | converged | 450 | 420 |  |  |
| naive | D-2fd8284bbb | converged | 450 | 450 |  |  |
| naive | D-2cd1bd6c25 | converged | 450 | 150 |  |  |
| naive | D-d590a2d801 | converged | 450 | 180 |  |  |
| naive | D-0b1f3f3777 | converged | 450 | 360 |  |  |
| naive | D-605aa06066 | converged | 450 | 450 |  |  |
| naive | F-D-51ac1cbcfc-unattributed-450 | fire:applied | 450 |  |  |  |
| naive | F-D-6fde6c87b6-unattributed-450 | fire:open | 450 |  |  |  |
| naive | F-D-7df012efc2-unattributed-450 | fire:open | 450 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-451 | fire:open | 451 |  |  |  |
| naive | F-D-448c925102-unattributed-454 | fire:applied | 454 |  |  |  |
| naive | F-D-2273209acd-unattributed-454 | fire:open | 454 |  |  |  |
| naive | F-D-22d419418e-unattributed-454 | fire:applied | 454 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-454 | fire:open | 454 |  |  |  |
| naive | F-D-448c925102-anomaly0-454 | fire:applied | 454 |  |  |  |
| naive | F-D-2273209acd-anomaly0-454 | fire:open | 454 |  |  |  |
| naive | F-D-22d419418e-anomaly0-454 | fire:applied | 454 |  |  |  |
| naive | F-D-8d3abb82b5-anomaly0-454 | fire:open | 454 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-458 | fire:open | 458 |  |  |  |
| naive | F-D-1cc4b91ad4-unattributed-458 | fire:open | 458 |  |  |  |
| naive | F-D-459901d01e-unattributed-458 | fire:open | 458 |  |  |  |
| naive | F-D-265092ac72-unattributed-459 | fire:open | 459 |  |  |  |
| naive | F-D-ac1d13eebd-unattributed-459 | fire:applied | 459 |  |  |  |
| naive | F-D-7df012efc2-unattributed-460 | fire:open | 460 |  |  |  |
| naive | F-D-6fde6c87b6-unattributed-460 | fire:open | 460 |  |  |  |
| naive | F-D-265092ac72-unattributed-464 | fire:open | 464 |  |  |  |
| naive | F-D-ac1d13eebd-unattributed-464 | fire:applied | 464 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-466 | fire:applied | 466 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-466 | fire:open | 466 |  |  |  |
| naive | F-D-7df012efc2-unattributed-466 | fire:open | 466 |  |  |  |
| naive | F-D-448c925102-unattributed-467 | fire:applied | 467 |  |  |  |
| naive | F-D-22d419418e-unattributed-467 | fire:applied | 467 |  |  |  |
| naive | F-D-2273209acd-unattributed-467 | fire:open | 467 |  |  |  |
| naive | F-D-a677ad5583-unattributed-467 | fire:open | 467 |  |  |  |
| naive | F-D-e87775e541-unattributed-467 | fire:applied | 467 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-467 | fire:open | 467 |  |  |  |
| naive | F-D-265092ac72-unattributed-468 | fire:open | 468 |  |  |  |
| naive | F-D-ac1d13eebd-unattributed-468 | fire:applied | 468 |  |  |  |
| naive | F-D-7c0335b3c7-unattributed-468 | fire:open | 468 |  |  |  |
| naive | F-D-448c925102-unattributed-470 | fire:applied | 470 |  |  |  |
| naive | F-D-2273209acd-unattributed-470 | fire:open | 470 |  |  |  |
| naive | F-D-22d419418e-unattributed-470 | fire:applied | 470 |  |  |  |
| naive | F-D-448c925102-unattributed-471 | fire:applied | 471 |  |  |  |
| naive | F-D-22d419418e-unattributed-471 | fire:applied | 471 |  |  |  |
| naive | F-D-2273209acd-unattributed-471 | fire:open | 471 |  |  |  |
| naive | F-D-a677ad5583-unattributed-471 | fire:open | 471 |  |  |  |
| naive | F-D-e87775e541-unattributed-471 | fire:applied | 471 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-471 | fire:open | 471 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-477 | fire:applied | 477 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-477 | fire:open | 477 |  |  |  |
| naive | F-D-7df012efc2-unattributed-477 | fire:open | 477 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-478 | fire:open | 478 |  |  |  |
| naive | F-D-cb35bd47b5-unattributed-478 | fire:open | 478 |  |  |  |
| naive | F-D-2f9b0a91bb-unattributed-478 | fire:applied | 478 |  |  |  |
| naive | F-D-f732729224-unattributed-478 | fire:open | 478 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-478 | fire:applied | 478 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-478 | fire:open | 478 |  |  |  |
| naive | D-35b04addb8 | admitted | 480 | 480 |  |  |
| naive | D-3ea552f5d2 | admitted | 480 | 480 |  |  |
| naive | D-6436c26208 | admitted | 480 | 480 |  |  |
| naive | D-fe3b50d1bf | converged | 480 | 420 |  |  |
| naive | D-b8cd6b0830 | converged | 480 | 450 |  | Q5_revenue |
| naive | D-49f6e57bd6 | converged | 480 | 480 |  | Q5_revenue |
| naive | D-2f9b0a91bb | converged | 480 | 360 |  |  |
| naive | D-3f5ad36afd | converged | 480 | 420 |  |  |
| naive | F-D-7a1d2a7c87-unattributed-481 | fire:applied | 481 |  |  |  |
| naive | F-D-7df012efc2-unattributed-484 | fire:open | 484 |  |  |  |
| naive | F-D-448c925102-unattributed-485 | fire:applied | 485 |  |  |  |
| naive | F-D-22d419418e-unattributed-485 | fire:applied | 485 |  |  |  |
| naive | F-D-2273209acd-unattributed-485 | fire:open | 485 |  |  |  |
| naive | F-D-a677ad5583-unattributed-485 | fire:open | 485 |  |  |  |
| naive | F-D-e87775e541-unattributed-485 | fire:applied | 485 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-485 | fire:open | 485 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-489 | fire:open | 489 |  |  |  |
| naive | F-D-7a1d2a7c87-unattributed-490 | fire:applied | 490 |  |  |  |
| naive | F-D-ef23240613-unattributed-490 | fire:open | 490 |  |  |  |
| naive | F-D-940c3fa057-unattributed-490 | fire:applied | 490 |  |  |  |
| naive | F-D-0dc61184b3-unattributed-490 | fire:open | 490 |  |  |  |
| naive | F-D-e87775e541-unattributed-493 | fire:applied | 493 |  |  |  |
| naive | F-D-22d419418e-unattributed-493 | fire:applied | 493 |  |  |  |
| naive | F-D-a677ad5583-unattributed-493 | fire:open | 493 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-493 | fire:open | 493 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-493 | fire:open | 493 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-494 | fire:open | 494 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-494 | fire:open | 494 |  |  |  |
| naive | F-D-448c925102-unattributed-495 | fire:applied | 495 |  |  |  |
| naive | F-D-2273209acd-unattributed-495 | fire:open | 495 |  |  |  |
| naive | F-D-22d419418e-unattributed-495 | fire:applied | 495 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-496 | fire:applied | 496 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-496 | fire:open | 496 |  |  |  |
| naive | F-D-7df012efc2-unattributed-496 | fire:open | 496 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-499 | fire:open | 499 |  |  |  |
| naive | F-D-7c0335b3c7-unattributed-499 | fire:open | 499 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-503 | fire:open | 503 |  |  |  |
| naive | F-D-d963adc21b-unattributed-504 | fire:open | 504 |  |  |  |
| naive | F-D-f5abb3b84a-unattributed-504 | fire:open | 504 |  |  |  |
| naive | F-D-d963adc21b-unattributed-505 | fire:open | 505 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-506 | fire:open | 506 |  |  |  |
| naive | F-D-fd8dc27ecb-unattributed-506 | fire:open | 506 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-507 | fire:open | 507 |  |  |  |
| naive | F-D-cf94cb1126-unattributed-507 | fire:applied | 507 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-509 | fire:open | 509 |  |  |  |
| naive | D-b4a2018cc5 | admitted | 510 | 510 |  |  |
| naive | D-6f594e5b5a | admitted | 510 | 510 |  |  |
| naive | D-f208a8a65a | admitted | 510 | 510 |  |  |
| naive | D-1ee7c84cd2 | admitted | 510 | 510 |  |  |
| naive | D-113d3a9b74 | admitted | 510 | 510 |  |  |
| naive | D-37ecb15fbb | admitted | 510 | 510 |  |  |
| naive | D-4af7bd7e8d | admitted | 510 | 510 |  |  |
| naive | D-70108a608d | converged | 510 | 120 |  |  |
| naive | D-e87775e541 | converged | 510 | 390 |  |  |
| naive | D-39d69e954f | converged | 510 | 30 |  |  |
| naive | D-02abc947b2 | converged | 510 | 420 |  |  |
| naive | D-448c925102 | converged | 510 | 450 |  |  |
| naive | D-7a1d2a7c87 | converged | 510 | 450 |  |  |
| naive | D-ad09add38e | converged | 510 | 480 |  |  |
| naive | D-cd2ed31c62 | converged | 510 | 480 |  |  |
| naive | D-8014fd81c9 | converged | 510 | 510 |  |  |
| naive | F-D-74619aed11-unattributed-510 | fire:open | 510 |  |  |  |
| naive | F-D-113d3a9b74-unattributed-510 | fire:open | 510 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-510 | fire:open | 510 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-510 | fire:open | 510 |  |  |  |
| naive | F-D-265092ac72-unattributed-512 | fire:open | 512 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-513 | fire:open | 513 |  |  |  |
| naive | F-D-fd8dc27ecb-unattributed-513 | fire:open | 513 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-514 | fire:applied | 514 |  |  |  |
| naive | F-D-7df012efc2-unattributed-514 | fire:open | 514 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-515 | fire:applied | 515 |  |  |  |
| naive | F-D-74619aed11-unattributed-515 | fire:open | 515 |  |  |  |
| naive | F-D-113d3a9b74-unattributed-515 | fire:open | 515 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-515 | fire:open | 515 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-515 | fire:open | 515 |  |  |  |
| naive | F-D-a677ad5583-unattributed-515 | fire:open | 515 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-517 | fire:applied | 517 |  |  |  |
| naive | F-D-22d419418e-unattributed-517 | fire:applied | 517 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-519 | fire:applied | 519 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-519 | fire:open | 519 |  |  |  |
| naive | F-D-18aadadff9-unattributed-519 | fire:open | 519 |  |  |  |
| naive | F-D-7df012efc2-unattributed-519 | fire:open | 519 |  |  |  |
| naive | F-D-1ee7c84cd2-unattributed-519 | fire:open | 519 |  |  |  |
| naive | F-D-254911151e-unattributed-522 | fire:open | 522 |  |  |  |
| naive | F-D-a37b29c4f6-unattributed-522 | fire:applied | 522 |  |  |  |
| naive | F-D-4af7bd7e8d-unattributed-522 | fire:open | 522 |  |  |  |
| naive | F-D-feb9fce382-unattributed-522 | fire:applied | 522 |  |  |  |
| naive | F-D-6d2e6c5cd3-unattributed-522 | fire:open | 522 |  |  |  |
| naive | F-D-22d419418e-unattributed-523 | fire:applied | 523 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-523 | fire:applied | 523 |  |  |  |
| naive | F-D-2273209acd-unattributed-523 | fire:open | 523 |  |  |  |
| naive | F-D-a677ad5583-unattributed-523 | fire:open | 523 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-523 | fire:open | 523 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-523 | fire:open | 523 |  |  |  |
| naive | F-D-1ee7c84cd2-unattributed-524 | fire:open | 524 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-524 | fire:open | 524 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-526 | fire:applied | 526 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-526 | fire:open | 526 |  |  |  |
| naive | F-D-18aadadff9-unattributed-526 | fire:open | 526 |  |  |  |
| naive | F-D-7df012efc2-unattributed-526 | fire:open | 526 |  |  |  |
| naive | F-D-1ee7c84cd2-unattributed-526 | fire:open | 526 |  |  |  |
| naive | F-D-74619aed11-unattributed-527 | fire:open | 527 |  |  |  |
| naive | F-D-113d3a9b74-unattributed-527 | fire:open | 527 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-527 | fire:open | 527 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-527 | fire:open | 527 |  |  |  |
| naive | F-D-a16a859bcf-unattributed-528 | fire:open | 528 |  |  |  |
| naive | F-D-4af7bd7e8d-unattributed-528 | fire:open | 528 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-530 | fire:applied | 530 |  |  |  |
| naive | F-D-74619aed11-unattributed-530 | fire:open | 530 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-530 | fire:open | 530 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-530 | fire:open | 530 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-532 | fire:applied | 532 |  |  |  |
| naive | F-D-74619aed11-unattributed-532 | fire:open | 532 |  |  |  |
| naive | F-D-113d3a9b74-unattributed-532 | fire:open | 532 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-532 | fire:open | 532 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-532 | fire:open | 532 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-533 | fire:applied | 533 |  |  |  |
| naive | F-D-22d419418e-unattributed-533 | fire:applied | 533 |  |  |  |
| naive | F-D-a677ad5583-unattributed-533 | fire:open | 533 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-533 | fire:open | 533 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-533 | fire:open | 533 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-535 | fire:open | 535 |  |  |  |
| naive | F-D-fd8dc27ecb-unattributed-535 | fire:open | 535 |  |  |  |
| naive | F-D-94ee280161-unattributed-536 | fire:applied | 536 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-536 | fire:open | 536 |  |  |  |
| naive | F-D-cb35bd47b5-unattributed-536 | fire:open | 536 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-536 | fire:applied | 536 |  |  |  |
| naive | F-D-e004669ffb-unattributed-536 | fire:applied | 536 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-536 | fire:open | 536 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-537 | fire:open | 537 |  |  |  |
| naive | F-D-b4a2018cc5-unattributed-539 | fire:open | 539 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-539 | fire:open | 539 |  |  |  |
| naive | D-88b29f439d | admitted | 540 | 540 |  |  |
| naive | D-90e294510d | admitted | 540 | 540 |  |  |
| naive | D-66668dd360 | admitted | 540 | 540 |  |  |
| naive | D-681e65cb2c | admitted | 540 | 540 |  |  |
| naive | D-8bb208a309 | admitted | 540 | 540 |  |  |
| naive | D-16a67ef60b | admitted | 540 | 540 |  |  |
| naive | D-fb7f50a025 | admitted | 540 | 540 |  |  |
| naive | D-11679b3dfd | admitted | 540 | 540 |  | Q5_revenue |
| naive | D-9040c674e5 | admitted | 540 | 540 |  |  |
| naive | D-8ee74b2c82 | admitted | 540 | 540 |  |  |
| naive | D-30dc65bde2 | admitted | 540 | 540 |  |  |
| naive | D-ac1d13eebd | converged | 540 | 390 |  |  |
| naive | D-22d419418e | converged | 540 | 270 |  |  |
| naive | D-ed66d7b960 | converged | 540 | 480 |  | Q5_revenue |
| naive | D-6ac5c97138 | converged | 540 | 540 |  |  |
| naive | D-637b237111 | converged | 540 | 540 |  | Q5_revenue |
| naive | D-8d82971ce7 | converged | 540 | 360 |  |  |
| naive | D-a37b29c4f6 | converged | 540 | 390 |  |  |
| naive | D-f56fcdf369 | converged | 540 | 480 |  | Q5_revenue |
| naive | D-94ee280161 | converged | 540 | 510 |  |  |
| naive | D-feb9fce382 | converged | 540 | 510 |  |  |
| naive | D-15970a99a6 | converged | 540 | 540 |  |  |
| naive | D-72a2c1199c | converged | 540 | 540 |  |  |
| naive | D-d3b9020502 | moot | 540 | 30 |  |  |
| naive | F-D-265092ac72-unattributed-540 | fire:open | 540 |  |  |  |
| naive | F-D-88b29f439d-unattributed-540 | fire:open | 540 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-541 | fire:open | 541 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-541 | fire:applied | 541 |  |  |  |
| naive | F-D-7df012efc2-unattributed-541 | fire:open | 541 |  |  |  |
| naive | F-D-43e5b7f5c0-unattributed-542 | fire:open | 542 |  |  |  |
| naive | F-D-54a1e6bcd3-unattributed-542 | fire:open | 542 |  |  |  |
| naive | F-D-7df012efc2-unattributed-543 | fire:open | 543 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-543 | fire:applied | 543 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-543 | fire:open | 543 |  |  |  |
| naive | F-D-1ee7c84cd2-unattributed-543 | fire:open | 543 |  |  |  |
| naive | F-D-cf5fb2e0e1-unattributed-544 | fire:open | 544 |  |  |  |
| naive | F-D-fd8dc27ecb-unattributed-544 | fire:open | 544 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-545 | fire:applied | 545 |  |  |  |
| naive | F-D-74619aed11-unattributed-545 | fire:open | 545 |  |  |  |
| naive | F-D-8bb208a309-unattributed-545 | fire:open | 545 |  |  |  |
| naive | F-D-a677ad5583-unattributed-545 | fire:open | 545 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-545 | fire:open | 545 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-546 | fire:open | 546 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-546 | fire:open | 546 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-549 | fire:applied | 549 |  |  |  |
| naive | F-D-8bb208a309-unattributed-549 | fire:open | 549 |  |  |  |
| naive | F-D-74619aed11-unattributed-549 | fire:open | 549 |  |  |  |
| naive | F-D-a677ad5583-unattributed-549 | fire:open | 549 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-549 | fire:open | 549 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-549 | fire:open | 549 |  |  |  |
| naive | F-D-b4a2018cc5-unattributed-550 | fire:open | 550 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-550 | fire:open | 550 |  |  |  |
| naive | F-D-2273209acd-unattributed-553 | fire:open | 553 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-553 | fire:applied | 553 |  |  |  |
| naive | F-D-74619aed11-unattributed-553 | fire:open | 553 |  |  |  |
| naive | F-D-a677ad5583-unattributed-553 | fire:open | 553 |  |  |  |
| naive | F-D-8bb208a309-unattributed-553 | fire:open | 553 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-1cc4b91ad4-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-e004669ffb-unattributed-554 | fire:applied | 554 |  |  |  |
| naive | F-D-43e5b7f5c0-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-459901d01e-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-30dc65bde2-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-23109b4465-unattributed-554 | fire:open | 554 |  |  |  |
| naive | F-D-7df012efc2-unattributed-555 | fire:open | 555 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-557 | fire:applied | 557 |  |  |  |
| naive | F-D-7df012efc2-unattributed-557 | fire:open | 557 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-557 | fire:open | 557 |  |  |  |
| naive | F-D-1cc4b91ad4-anomaly0-558 | fire:open | 558 |  |  |  |
| naive | F-D-6fde6c87b6-unattributed-559 | fire:open | 559 |  |  |  |
| naive | F-D-7df012efc2-unattributed-559 | fire:open | 559 |  |  |  |
| naive | F-D-2273209acd-unattributed-560 | fire:open | 560 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-560 | fire:applied | 560 |  |  |  |
| naive | F-D-74619aed11-unattributed-560 | fire:open | 560 |  |  |  |
| naive | F-D-a677ad5583-unattributed-560 | fire:open | 560 |  |  |  |
| naive | F-D-8bb208a309-unattributed-560 | fire:open | 560 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-560 | fire:open | 560 |  |  |  |
| naive | F-D-51ac1cbcfc-unattributed-561 | fire:applied | 561 |  |  |  |
| naive | F-D-7df012efc2-unattributed-561 | fire:open | 561 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-561 | fire:open | 561 |  |  |  |
| naive | F-D-265092ac72-unattributed-564 | fire:open | 564 |  |  |  |
| naive | F-D-2bd836fdd3-unattributed-564 | fire:open | 564 |  |  |  |
| naive | F-D-0fdacc793e-unattributed-565 | fire:applied | 565 |  |  |  |
| naive | F-D-8bb208a309-unattributed-565 | fire:open | 565 |  |  |  |
| naive | F-D-74619aed11-unattributed-565 | fire:open | 565 |  |  |  |
| naive | F-D-a677ad5583-unattributed-565 | fire:open | 565 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-565 | fire:open | 565 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-565 | fire:open | 565 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-567 | fire:open | 567 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-567 | fire:open | 567 |  |  |  |
| naive | F-D-7df012efc2-unattributed-568 | fire:open | 568 |  |  |  |
| naive | F-D-b4a2018cc5-unattributed-569 | fire:open | 569 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-569 | fire:open | 569 |  |  |  |
| naive | D-28895e33ef | admitted | 570 | 570 |  |  |
| naive | D-b5bdf3d2ff | admitted | 570 | 570 |  |  |
| naive | D-04907133f2 | admitted | 570 | 570 |  |  |
| naive | D-ae71687f9f | admitted | 570 | 570 |  | Q5_revenue |
| naive | D-60cf0303fc | admitted | 570 | 570 |  |  |
| naive | D-2dccd7eaa9 | admitted | 570 | 570 |  |  |
| naive | D-48ddf36dc1 | admitted | 570 | 570 |  |  |
| naive | D-5c71f9a2c8 | admitted | 570 | 570 |  |  |
| naive | D-0b93c13be4 | admitted | 570 | 570 |  |  |
| naive | D-4a6d5f3ebb | admitted | 570 | 570 |  |  |
| naive | D-135f2f64d6 | converged | 570 | 540 |  |  |
| naive | D-3dad0a1847 | converged | 570 | 270 |  |  |
| naive | D-124cae8933 | converged | 570 | 330 |  |  |
| naive | D-909085365e | converged | 570 | 360 |  |  |
| naive | D-51ac1cbcfc | converged | 570 | 390 |  |  |
| naive | D-1df3823589 | converged | 570 | 390 |  |  |
| naive | D-dce5ea39b3 | converged | 570 | 450 |  |  |
| naive | D-e004669ffb | converged | 570 | 480 |  |  |
| naive | D-0fdacc793e | converged | 570 | 510 |  |  |
| naive | D-1df4451beb | converged | 570 | 540 |  | Q5_revenue |
| naive | D-cba0b0c76e | converged | 570 | 540 |  |  |
| naive | D-05a900ce25 | converged | 570 | 570 |  |  |
| naive | D-3968769949 | converged | 570 | 570 |  |  |
| naive | D-26885b1989 | converged | 570 | 570 |  |  |
| naive | D-7705d158ed | moot | 570 | 270 |  |  |
| naive | D-cce5cad77e | moot | 570 | 270 |  |  |
| naive | F-D-a16a859bcf-unattributed-570 | fire:open | 570 |  |  |  |
| naive | F-D-9040c674e5-unattributed-570 | fire:open | 570 |  |  |  |
| naive | F-D-43e5b7f5c0-unattributed-572 | fire:open | 572 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-572 | fire:open | 572 |  |  |  |
| naive | F-D-b5bdf3d2ff-anomaly0-573 | fire:open | 573 |  |  |  |
| naive | F-D-11679b3dfd-anomaly0-573 | fire:open | 573 |  |  |  |
| naive | F-D-b6b2c9f806-anomaly0-573 | fire:open | 573 |  |  |  |
| naive | F-D-18aadadff9-anomaly0-573 | fire:open | 573 |  |  |  |
| naive | F-D-1ee7c84cd2-anomaly0-573 | fire:open | 573 |  |  |  |
| naive | F-D-ae71687f9f-anomaly0-573 | fire:open | 573 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-30dc65bde2-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-cb35bd47b5-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-f732729224-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-575 | fire:applied | 575 |  |  |  |
| naive | F-D-4a6d5f3ebb-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-7c0335b3c7-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-23109b4465-unattributed-575 | fire:open | 575 |  |  |  |
| naive | F-D-b5bdf3d2ff-unattributed-578 | fire:open | 578 |  |  |  |
| naive | F-D-7df012efc2-unattributed-578 | fire:open | 578 |  |  |  |
| naive | F-D-b6b2c9f806-unattributed-578 | fire:open | 578 |  |  |  |
| naive | F-D-1ee7c84cd2-unattributed-578 | fire:open | 578 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-580 | fire:open | 580 |  |  |  |
| naive | F-D-16a67ef60b-unattributed-580 | fire:open | 580 |  |  |  |
| naive | F-D-43e5b7f5c0-unattributed-585 | fire:open | 585 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-585 | fire:open | 585 |  |  |  |
| naive | F-D-5c71f9a2c8-unattributed-585 | fire:open | 585 |  |  |  |
| naive | F-D-4a6d5f3ebb-unattributed-585 | fire:open | 585 |  |  |  |
| naive | F-D-44af97a8e1-unattributed-585 | fire:open | 585 |  |  |  |
| naive | F-D-23109b4465-unattributed-585 | fire:open | 585 |  |  |  |
| naive | F-D-30dc65bde2-unattributed-585 | fire:open | 585 |  |  |  |
| naive | F-D-2a6d6ea44b-unattributed-585 | fire:applied | 585 |  |  |  |
| naive | F-D-6fde6c87b6-unattributed-586 | fire:open | 586 |  |  |  |
| naive | F-D-7df012efc2-unattributed-586 | fire:open | 586 |  |  |  |
| naive | F-D-7c0335b3c7-unattributed-587 | fire:open | 587 |  |  |  |
| naive | F-D-4a6d5f3ebb-unattributed-587 | fire:open | 587 |  |  |  |
| naive | F-D-8bb208a309-unattributed-588 | fire:open | 588 |  |  |  |
| naive | F-D-74619aed11-unattributed-588 | fire:open | 588 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-588 | fire:open | 588 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-588 | fire:open | 588 |  |  |  |
| naive | F-D-d963adc21b-unattributed-592 | fire:open | 592 |  |  |  |
| naive | F-D-f5abb3b84a-unattributed-592 | fire:open | 592 |  |  |  |
| naive | F-D-35dcfe8c71-unattributed-593 | fire:open | 593 |  |  |  |
| naive | F-D-7c0335b3c7-unattributed-593 | fire:open | 593 |  |  |  |
| naive | F-D-0477b14823-unattributed-593 | fire:open | 593 |  |  |  |
| naive | F-D-4a6d5f3ebb-unattributed-593 | fire:open | 593 |  |  |  |
| naive | F-D-a86e33fa06-unattributed-594 | fire:open | 594 |  |  |  |
| naive | F-D-35d7db4c13-unattributed-594 | fire:open | 594 |  |  |  |
| naive | F-D-7df012efc2-unattributed-595 | fire:open | 595 |  |  |  |
| naive | F-D-6fde6c87b6-unattributed-595 | fire:open | 595 |  |  |  |
| naive | F-D-8bb208a309-unattributed-597 | fire:open | 597 |  |  |  |
| naive | F-D-74619aed11-unattributed-597 | fire:open | 597 |  |  |  |
| naive | F-D-28895e33ef-unattributed-597 | fire:open | 597 |  |  |  |
| naive | F-D-ad61e4b320-unattributed-597 | fire:open | 597 |  |  |  |
| naive | F-D-8d3abb82b5-unattributed-597 | fire:open | 597 |  |  |  |
| naive | D-27ab6a982d | admitted | 600 | 600 |  | P1_claire_rounding |
| naive | D-8653a5f110 | admitted | 600 | 600 |  | Q3_soft_delete |
| naive | D-9d3004794b | admitted | 600 | 600 |  |  |
| naive | D-01b883a729 | admitted | 600 | 600 |  |  |
| naive | D-b7a6aaa2d7 | admitted | 600 | 600 |  |  |
| naive | D-5bb75eb887 | admitted | 600 | 600 |  | Q5_revenue |
| naive | D-3d94bb38d6 | admitted | 600 | 600 |  |  |
| naive | D-fbf468ed43 | admitted | 600 | 600 |  |  |
| naive | D-2fc700a1e7 | admitted | 600 | 600 |  |  |
| naive | D-a6047fe879 | converged | 600 | 570 |  | P1_claire_rounding |
| naive | D-f8479d6db8 | converged | 600 | 240 |  | Q5_revenue |
| naive | D-2a6d6ea44b | converged | 600 | 270 |  |  |
| naive | D-cf94cb1126 | converged | 600 | 330 |  |  |
| naive | D-940c3fa057 | converged | 600 | 330 |  |  |
| naive | D-d7823d0024 | converged | 600 | 570 |  |  |
| naive | D-c98efda48a | converged | 600 | 600 |  |  |
| naive | D-4582a3d5d8 | converged | 600 | 600 |  |  |
| naive | D-6d15d23767 | moot | 600 | 300 |  |  |
| ungated | D-bc34ed6086 | admitted | 120 | 120 |  | P1_claire_rounding |
| ungated | D-a146794e50 | admitted | 120 | 120 |  | Q1_active_customer |
| ungated | F-D-bc34ed6086-unattributed-123 | fire:open | 123 |  |  |  |
| ungated | F-D-bc34ed6086-unattributed-129 | fire:open | 129 |  |  |  |
| ungated | F-D-bc34ed6086-unattributed-139 | fire:open | 139 |  |  |  |
| ungated | F-D-bc34ed6086-unattributed-146 | fire:open | 146 |  |  |  |
| ungated | D-03cfefa728 | admitted | 150 | 150 |  | Q5_revenue |
| ungated | F-D-bc34ed6086-unattributed-151 | fire:open | 151 |  |  |  |
| ungated | F-D-c732b0c227-T-D-c732b0c227-1-g0 | fire:applied | 151 |  |  |  |
| ungated | F-D-bc34ed6086-unattributed-168 | fire:open | 168 |  |  |  |
| ungated | F-D-bc34ed6086-unattributed-172 | fire:open | 172 |  |  |  |
| ungated | D-1b6d28e154 | admitted | 180 | 180 |  | Q3_soft_delete |
| ungated | D-c732b0c227 | superseded | 180 | 150 | D-c7affcab3a |  |
| ungated | F-D-1b6d28e154-unattributed-187 | fire:open | 187 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-192 | fire:open | 192 |  |  |  |
| ungated | F-D-c7affcab3a-unattributed-196 | fire:applied | 196 |  |  |  |
| ungated | F-D-bc34ed6086-unattributed-196 | fire:open | 196 |  |  |  |
| ungated | F-D-bc34ed6086-unattributed-198 | fire:open | 198 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-199 | fire:open | 199 |  |  |  |
| ungated | F-D-bc34ed6086-unattributed-200 | fire:open | 200 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-209 | fire:open | 209 |  |  |  |
| ungated | D-0aa448a8b9 | admitted | 210 | 210 |  |  |
| ungated | F-D-0aa448a8b9-unattributed-221 | fire:open | 221 |  |  |  |
| ungated | F-D-c7affcab3a-T-D-c7affcab3a-1-g0 | fire:applied | 224 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-224 | fire:open | 224 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-238 | fire:open | 238 |  |  |  |
| ungated | D-3d96d341a6 | admitted | 240 | 240 |  | Q6_tech_names |
| ungated | D-c7affcab3a | superseded | 240 | 180 | D-3d96d341a6 |  |
| ungated | F-D-1b6d28e154-unattributed-243 | fire:open | 243 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-249 | fire:open | 249 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-257 | fire:open | 257 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-263 | fire:open | 263 |  |  |  |
| ungated | D-fe6669e8b7 | admitted | 270 | 270 |  | Q6_tech_names |
| ungated | F-D-0aa448a8b9-unattributed-281 | fire:open | 281 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-284 | fire:open | 284 |  |  |  |
| ungated | F-D-a146794e50-unattributed-307 | fire:open | 307 |  |  |  |
| ungated | F-D-ad2083cdba-unattributed-307 | fire:applied | 307 |  |  |  |
| ungated | F-D-a146794e50-unattributed-309 | fire:open | 309 |  |  |  |
| ungated | F-D-ad2083cdba-unattributed-309 | fire:applied | 309 |  |  |  |
| ungated | F-D-ad2083cdba-T-D-ad2083cdba-1-g0 | fire:applied | 310 |  |  |  |
| ungated | F-D-a146794e50-unattributed-312 | fire:open | 312 |  |  |  |
| ungated | F-D-ad2083cdba-unattributed-312 | fire:applied | 312 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-322 | fire:open | 322 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-324 | fire:open | 324 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-335 | fire:open | 335 |  |  |  |
| ungated | F-D-a146794e50-unattributed-337 | fire:open | 337 |  |  |  |
| ungated | F-D-ad2083cdba-unattributed-337 | fire:applied | 337 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-348 | fire:open | 348 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-352 | fire:open | 352 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-353 | fire:open | 353 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-355 | fire:open | 355 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-359 | fire:open | 359 |  |  |  |
| ungated | D-612e7b46e7 | admitted | 360 | 360 |  | Q1_active_customer |
| ungated | D-ad2083cdba | superseded | 360 | 60 | D-612e7b46e7 | Q1_active_customer |
| ungated | F-D-0aa448a8b9-unattributed-361 | fire:open | 361 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-366 | fire:open | 366 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-370 | fire:open | 370 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-380 | fire:open | 380 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-385 | fire:open | 385 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-396 | fire:open | 396 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-405 | fire:open | 405 |  |  |  |
| ungated | F-D-0aa448a8b9-unattributed-418 | fire:open | 418 |  |  |  |
| ungated | D-f5ab0f9dce | admitted | 420 | 420 |  |  |
| ungated | F-D-bc34ed6086-unattributed-427 | fire:open | 427 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-436 | fire:open | 436 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-451 | fire:open | 451 |  |  |  |
| ungated | D-8bbc072689 | admitted | 480 | 480 |  |  |
| ungated | F-D-8bbc072689-unattributed-546 | fire:open | 546 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-546 | fire:open | 546 |  |  |  |
| ungated | F-D-8bbc072689-unattributed-567 | fire:open | 567 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-567 | fire:open | 567 |  |  |  |
| ungated | F-D-8bbc072689-unattributed-580 | fire:open | 580 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-580 | fire:open | 580 |  |  |  |
| ungated | F-D-8bbc072689-unattributed-594 | fire:open | 594 |  |  |  |
| ungated | F-D-1b6d28e154-unattributed-594 | fire:open | 594 |  |  |  |

## Spend (list price)

| arm | stage | model | calls | errors | tokens in | tokens out | USD |
|---|---|---|---|---|---|---|---|
| frozen | propose | claude-haiku-5-5 | 760 | 0 | 2043942 | 540228 | 0.4745 |
| governed | embed | voyage-4 | 320 | 0 | 68221 | 0 | 0.0041 |
| governed | nominate | claude-sonnet-5-5 | 150 | 0 | 2140285 | 122242 | 5.6042 |
| governed | observe | claude-haiku-4-5 | 307 | 0 | 491280 | 35193 | 0.6672 |
| governed | propose | claude-haiku-5-5 | 760 | 0 | 2123271 | 637016 | 0.5308 |
| governed | replay | claude-haiku-5-5 | 568 | 0 | 1630456 | 542298 | 0.4342 |
| governed | rerank | rerank-3 | 265 | 0 | 23124 | 0 | 0.0012 |
| governed | retry | claude-haiku-5-5 | 313 | 0 | 888753 | 352586 | 0.2652 |
| naive | embed | voyage-4 | 490 | 0 | 38716 | 0 | 0.0023 |
| naive | lesson | claude-sonnet-5-5 | 245 | 0 | 292902 | 159748 | 2.1833 |
| naive | observe | claude-haiku-4-5 | 351 | 0 | 557428 | 43062 | 0.7727 |
| naive | propose | claude-haiku-5-5 | 760 | 0 | 2856064 | 1203606 | 0.8874 |
| naive | rerank | rerank-3 | 657 | 0 | 467210 | 0 | 0.0234 |
| naive | retry | claude-haiku-5-5 | 374 | 2 | 1419264 | 708156 | 0.4960 |
| ungated | embed | voyage-4 | 177 | 0 | 23061 | 0 | 0.0014 |
| ungated | nominate | claude-sonnet-5-5 | 75 | 0 | 742398 | 52340 | 2.0588 |
| ungated | observe | claude-haiku-4-5 | 148 | 0 | 233303 | 17062 | 0.3186 |
| ungated | propose | claude-haiku-5-5 | 760 | 0 | 2386097 | 843129 | 0.6602 |
| ungated | rerank | rerank-3 | 409 | 0 | 140133 | 0 | 0.0070 |
| ungated | retry | claude-haiku-5-5 | 151 | 0 | 453722 | 183199 | 0.1370 |

## Knob diff against run `run-a`

Forecasts of a run whose knobs moved are that run's own registration (SPEC § 11, pilot rule).

| knob | this run | other run |
|---|---|---|
| authority_poison_rate | 0.2 | 0.05 |
| backtest_concurrency | 8 | 4 |
| backtest_n | 16 | 8 |
| backtest_sample | "random" | "hashed" |
| bar_min_templates_floor | 2 | 3 |
| conf_dir | "<workspace>/munch-run-b/engine/conf/run-b" | "<workspace>/munch-run-a/engine/conf" |
| direct_concurrency | 6 | null |
| packs_dir | "<workspace>/munch-run-b/engine/packs" | "<workspace>/munch-run-a/engine/packs" |
| run_id | "run-b" | "run-a" |
| trace_impl | "jsonl" | "jsonl,raindrop" |
| workers_per_arm | 10 | 6 |
| git_sha | "60086e49b1409ea16a4782511f56e4389c1adb0a" | "5c171151316e6e9cba418117b98cc1bc06ffbfd8" |
| ports | {"frozen": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl"}, "self_ref": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl"}, "naive": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl"}, "ungated": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl"}, "governed": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "jev", "memory_sink": "null", "trace": "jsonl"}} | {"frozen": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl,raindrop"}, "self_ref": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl,raindrop"}, "naive": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl,raindrop"}, "ungated": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "none", "memory_sink": "null", "trace": "jsonl,raindrop"}, "governed": {"representation": "voyage-4", "reranker": "rerank-3", "similarity": "atlas-vector", "grouper": "agglomerative", "lens_panel": "jev", "memory_sink": "null", "trace": "jsonl,raindrop"}} |
| forecast_register | {"F1": {"claim": "an arm holding a pre-D1 Q1 decision shows a calibration gap over D1_AT\u2026D1_AT+150 above its gap over the 150 episodes before D1_AT, until a successor is admitted", "reading": "calibration gap (mean confidence \u2212 accuracy) after minus before, per arm; frozen with the stream on is the no-decision reference", "margin": 0.05, "unit": "accuracy points (fraction)", "read": {"kind": "drift_calibration", "drift": "D1", "quirk_prefix": "Q1", "reference": "frozen"}}, "F2": {"claim": "under a 0.20 poison rate, governed admits 0 N1-derived decisions; naive and ungated each admit \u2265 1", "reading": "planted_map N1-derived admitted count per arm", "margin": 0, "unit": "decisions", "read": {"kind": "planted_count", "quirk_prefix": "N1", "expect": {"governed": {"max": 0}, "naive": {"min": 1}, "ungated": {"min": 1}}}}, "F3": {"claim": "naive holds P1 at org scope; governed holds it at persona scope or not at all", "reading": "planted_map P1 scope per arm", "margin": 0, "unit": "decisions", "read": {"kind": "planted_scope", "quirk_prefix": "P1", "expect": {"naive": ["org"], "governed": ["persona", "none"]}}}, "F4": {"claim": "governed drift-to-supersede latency for D1 is below naive's and below ungated's, where those arms resolve the drift at all", "reading": "latency difference (other \u2212 governed); a single drift event per arm, so the verdict is the sign beyond the margin, with no interval", "margin": 30, "unit": "episodes (one ROUND_SIZE)", "read": {"kind": "drift_latency", "drift": "D1", "quirk_prefix": "Q1", "a": "governed", "others": ["naive", "ungated"]}}, "F5": {"claim": "on quirk-bearing stream questions after round 10, governed accuracy is above naive's", "reading": "paired difference governed \u2212 naive, same questions by index", "margin": 0.05, "unit": "accuracy (fraction)", "read": {"kind": "paired_accuracy", "a": "governed", "b": "naive", "population": "quirk_bearing", "after_round": 10}}, "F6": {"claim": "on quirk-bearing stream questions after round 10, governed accuracy is above ungated's (the gate's effect)", "reading": "paired difference governed \u2212 ungated, same questions by index", "margin": 0.05, "unit": "accuracy (fraction)", "read": {"kind": "paired_accuracy", "a": "governed", "b": "ungated", "population": "quirk_bearing", "after_round": 10}}, "F7": {"claim": "on control stream questions after round 10, governed accuracy is above ungated's (poison-derived decisions that ungated admits break questions they should not touch)", "reading": "paired difference governed \u2212 ungated, same questions by index, controls only", "margin": 0.05, "unit": "accuracy (fraction)", "read": {"kind": "paired_accuracy", "a": "governed", "b": "ungated", "population": "controls", "after_round": 10}}} | {"F1": {"claim": "an arm holding a pre-D1 Q1 decision shows a calibration gap over D1_AT\u2026D1_AT+150 above its gap over the 150 episodes before D1_AT, until a successor is admitted", "reading": "calibration gap (mean confidence \u2212 accuracy) after minus before, per arm; frozen with the stream on is the no-decision reference", "margin": 0.05, "unit": "accuracy points (fraction)", "read": {"kind": "drift_calibration", "drift": "D1", "quirk_prefix": "Q1", "reference": "frozen"}}, "F2": {"claim": "sanity check, not a finding: governed admits 0 N1-derived decisions; naive admits \u2265 1", "reading": "planted_map N1-derived admitted count per arm", "margin": 0, "unit": "decisions", "read": {"kind": "planted_count", "quirk_prefix": "N1", "expect": {"governed": {"max": 0}, "naive": {"min": 1}}}}, "F3": {"claim": "naive holds P1 at org scope; governed holds it at persona scope or not at all", "reading": "planted_map P1 scope per arm", "margin": 0, "unit": "decisions", "read": {"kind": "planted_scope", "quirk_prefix": "P1", "expect": {"naive": ["org"], "governed": ["persona", "none"]}}}, "F4": {"claim": "governed drift-to-supersede latency for D1 is below naive's and below ungated's, where those arms resolve the drift at all", "reading": "latency difference (other \u2212 governed); a single drift event per arm, so the verdict is the sign beyond the margin, with no interval", "margin": 30, "unit": "episodes (one ROUND_SIZE)", "read": {"kind": "drift_latency", "drift": "D1", "quirk_prefix": "Q1", "a": "governed", "others": ["naive", "ungated"]}}, "F5": {"claim": "on quirk-bearing stream questions after round 10, governed accuracy is above naive's", "reading": "paired difference governed \u2212 naive, same questions by index", "margin": 0.05, "unit": "accuracy (fraction)", "read": {"kind": "paired_accuracy", "a": "governed", "b": "naive", "population": "quirk_bearing", "after_round": 10}}, "F6": {"claim": "on quirk-bearing stream questions after round 10, governed accuracy is above ungated's (the gate's effect)", "reading": "paired difference governed \u2212 ungated, same questions by index", "margin": 0.05, "unit": "accuracy (fraction)", "read": {"kind": "paired_accuracy", "a": "governed", "b": "ungated", "population": "quirk_bearing", "after_round": 10}}} |
