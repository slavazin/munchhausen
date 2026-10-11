# Munchhausen — a harness that admits only what the world confirms

Design document for the Harness Engineering & Model Wrangling hackathon (Shack15, San Francisco, 2026-10-11; hacking 10:30–17:00 PT). Solo build.
This file is written before the event. The event's rule *New Work Only* governs the code: every line under `engine/` and `viewer/` is written on the day, apart from the schema import named in § 15.
Concepts are drawn from the GCE doctrine (Governed Corpus Evolution, `gce/GCE-DOCTRINE.md`). The README cites them as ideas, not shipped code.

Reader: an implementing session that holds this file and nothing else. Every section states what stands; sections never narrate how the design was reached.

---

## 0. Pitch

An agent that learns only from itself learns only what its prior already holds.
Self-critique, "act as the subject-matter expert" prompting and self-graded memory share three blind spots:
1. **Counter-prior facts.** Local truth contradicts a confident convention. Reflection reinforces the convention.
2. **Uninferable constants.** Thresholds, sets, fees and offsets can't be derived by reasoning; they have to be measured.
3. **World shift.** After the world changes, a self-graded agent checks each answer with the same stale rule that produced it. It stays internally consistent and confidently wrong: self-reference certifies the stale rule.

The name casts the model as the Baron: a charming storyteller who swears he pulled himself out of the swamp by his own hair. The harness is the party that checks the story against the swamp.

**Munchhausen** is an agent harness that rewrites its own rules, guardrails and tool access from an external numeric signal: the figure an authority expected.
- **Admission:** every candidate decision passes a lens panel (corroborating) and an out-of-sample **backtest** against the case store (dispositive) before it is admitted.
- **Consultation:** every admitted decision reaches the working agent only through its own **hook**.
- **Revisit:** every admitted decision carries a **revisit trigger** that reads residuals against the authority's figures. When the world shifts, the trigger fires and the decision is superseded, leaving a tombstone.

The demo world is a data agent answering business questions over a MongoDB dataset whose meaning lives in hidden tribal knowledge.
Four arms run side by side: **frozen**, **self-referential**, **naive** and **governed**.

Positioning against the host platform: Atlas Agent Engine (public preview, launched 2026-09-29) provides memory *types*. Munchhausen gives each stored decision a warrant, a hook and a tripwire. It is a governance layer on top of Atlas memory, not a replacement for it.

## 1. Judging map

Criteria and weights are from the event page (read 2026-10-10). Round two weights the criteria equally.

| Criterion (round-one weight) | What carries it |
|---|---|
| Technical demo 35% | Replay scrubber over a recorded run. One live beat: a judge feeds the agent a false authority figure and watches backtest reject the resulting draft. A floor latch turns into a MongoDB view, and a pipeline loses the soft-deleted rows. Drift fires a trigger, which leads to a tombstone, traced with `why`. |
| Implementation difficulty 30% | Hook-keyed consultation, residual attribution, backtest replay against the case store, floor latches materialized as views, supersession lineage via `$graphLookup`, lens weights fitted to backtest outcomes |
| Impact 20% | Enterprise data agents fail on tribal knowledge. Auto-extracted memory spreads wrong, stale or one-person lessons into shared context. |
| Creativity 15% | Memory admission as an experiment: each decision is a hypothesis with a falsifier, admitted by an out-of-sample replay and retired by the world |

Problem statements covered:
- **1 Recursive Harnessing:** the harness rewrites its rules, guardrails and tool access (§ 8).
- **2 Long Horizon:** a resumable prequential stream learning from a hard numeric metric.

Raindrop RSI prize: the second-order loop (§ 9). The stand-in adjudicator learns which questions to ask, graded by backtest outcomes, never by its own verdicts.

**Do:** keep the agent acting at the centre of every demo beat; the event bans projects whose main feature is a dashboard.
**Don't:** strip the curves; they carry the self-reference claim. They sit in a side pane.

## 2. Lexicon

The spec uses the terms of `gce/GCE-DOCTRINE.md` and of the corpus language guide. The terms below carry one meaning each throughout this file and the code.

| Term | Means here | Not |
|---|---|---|
| store | one kind of record under one lifecycle, held in one Atlas collection | "memory" (reserved for Atlas Agent Memory, the product) |
| collection | the MongoDB object only | a store |
| forward pass | one episode: question → consultation → proposer → execution → score → authority | — |
| backward pass | the observer writing observations from a miss, and the episodic pass grouping observations into shapes | — |
| episodic pass | the per-round backward-pass step: group observations into shapes, nominate, adjudicate, admit | "activation" (not used anywhere in this spec) |
| shape | a group of observations located by embedding clustering, passing the coherence guard (§ 7.2) | a nomination; the grouping proposes no rule |
| nomination | the nominator's act: it takes one shape and generalizes it into the decision that answers the question whose answer would settle the shape's observations; the result is a draft | grouping, clustering |
| nominator | the LLM party that nominates (§ 7.2) | "judge" (reserved for the event's judges); the stand-in adjudicator, which disposes the draft |
| draft | a nominated decision before admission | candidate entry |
| admission | the stand-in adjudicator's act that turns a draft into a decision and mints its ID | promotion (human-only in the doctrine; see § 14) |
| decision | an admitted record in the decision store | rule, lesson, memory item |
| hook | the consultation latch: a `fires-when` guard over the question's legible keys, plus `not-this` | retrieval |
| consultation | a hook matching an episode. The proposer records one disposition per consulted decision: `applied` or `considered-not-applicable`. | exposure, activation |
| authority | the stakeholder simulator. On a miss it returns the figure it expected and, at level `term`, names the concept. | oracle (reserved for the stand-in adjudicator) |
| confirmed figure | for every episode, the agent's answer if scored correct; otherwise the authority's figure | gold (hidden; the learning loop never reads it) |
| residual | the gap between an applied decision's answer and the authority's figure on one episode, with its signature | error |
| fire | the record a latch emits when its guard holds; disposed by its named consumer | alert, flag |
| evidence state | `clear` or `contested`, computed from open fires; orthogonal to lifecycle | a lifecycle status |
| stand-in adjudicator | the autonomous party occupying the doctrine's owner seat: lens panel plus backtest | oracle agent, judge |
| tombstone | a superseded or retired decision kept with `superseded_by` or a reason | a deleted record |

## 3. Stack

Model and service names are dated facts (verified 2026-10-10 unless marked). Kickoff re-verifies each premise marked **verify**.

| Concern | Choice | Fallback |
|---|---|---|
| Engine language | Python 3.12, `uv` project, `asyncio` | — |
| Database | MongoDB Atlas Hackathon Sandbox cluster (required for finalists) | — |
| Driver | `pymongo` `AsyncMongoClient` | `motor` |
| Embeddings | Voyage `voyage-4` (1024-d), `voyageai` SDK | `voyage-4-lite` |
| Rerank | Voyage `rerank-3` (released 2026-09-30) | `rerank-3-lite` |
| Vector search | Atlas Vector Search indexes `decisions_vec` and `observations_vec`. No Atlas Search index and no `$rankFusion`; hooks replace lexical retrieval. | cosine in `numpy` over the arm's records |
| Proposer (the agent being improved) | `claude-haiku-4-5` (**verify** that the API serves it; knob `PROPOSER_MODEL`) | `claude-haiku-5-5` |
| Observer | `claude-haiku-4-5` | — |
| Nominator | `claude-sonnet-5-5`, effort `medium`, with a read-only world query tool | `claude-opus-5-5` |
| Lens panel (corroborating) | TypeSafe Jev via `typesafe-sdk` (`AsyncTypeSafeClient.system_one`; Noul / Choice), env `TYPESAFE_API_KEY` | `claude-opus-5-5` with structured output per lens |
| Structured output | `anthropic` SDK, `client.messages.parse()` with a JSON schema; no forced `tool_choice` on 5.5 models | — |
| Authority | deterministic templates; no LLM | — |
| Stats | `numpy`, `scikit-learn` (`AgglomerativeClustering`, `LogisticRegression`, `roc_auc_score`) | — |
| Live feed | Atlas change streams on `fires`, `decisions`, `rounds` | polling every 2 s |
| Viewer | FastAPI + SSE + one static `index.html` (Chart.js from CDN) | — |
| Tracing | Raindrop SDK: one interaction per episode; signals `correct`, `floor_filtered`, `fire`, `admission` (**verify** the package name) | none |
| CLI | `typer` | `argparse` |
| Tests | `pytest` | — |

Premises with falsifiers:
- **Index budget.** The sandbox tier admits the two vector indexes. False if: index creation fails on the sandbox (M0 and Flex allow 3 search indexes in total). In that case, fall back to `numpy` cosine for `observations`.
- **Storage.** Loading sample data leaves room for the `world` and `munchhausen` databases. False if: the cluster reports storage above 80% after loading. In that case, drop every sample database except the one the dataset adapter reads.
- **Rate limits.** API rate limits sustain 6 workers per arm. False if: 429s exceed 5% of calls in the pilot. In that case, reduce `WORKERS_PER_ARM`. The Voyage key needs a payment method on file, because keys without one get very low RPM.

## 4. The world

### 4.1 Dataset adapter and quirk packs

The world is a dataset adapter plus one or more **quirk packs**. Neither is hardcoded into the engine.
- **Adapter:** `world/adapters/<name>.py`. It materializes the working database `world` from a source, deterministic under `WORLD_SEED`, and exposes the schema summary shown to the proposer (field names and types only, never meanings).
- **Quirk pack:** a data file `packs/<name>.yaml`. Each quirk declares:

```
id, kind: taxonomic|procedural|floor|preference|poison,
prior_trap: str,              # the convention a model applies by default, which the quirk contradicts
materialize: {transform, params},   # registered adapter transform: fields/values written into `world`
gold: {transform, params},          # registered gold transform used by truth.gold
signature: set_member|ratio|date_offset|exclusion|threshold|rounding,
templates: [template_id],     # ≥ 4 per quirk
authority_phrasings: [str],   # ≥ 3, each names the concept, never the definition
drift: [{at_idx, gold_params}]      # gold-only drift; the database is never mutated after build
```

Transforms are Python functions in a registry, keyed by name. A pack names them and supplies parameters; it never carries code.

**Do:** design every quirk to *contradict* a prior the proposer holds, and to leave a residual with a declared signature when violated.
**Don't:** design quirks that are merely arbitrary and leave no signature. Those are unlearnable from a figure, and their residuals can't be attributed.

**Do:** give quirk fields opaque names, and plant decoys that match the convention.
**Don't:** name a field after its meaning (`_del`, `is_test`, `status: "A"`). The schema summary would hand the proposer the quirk.

### 4.2 Seed pack `analytics-v1` over adapter `sample_analytics`

Source: the Atlas sample database `sample_analytics` (`customers`, `accounts`, `transactions`).
**Verify** at kickoff: field types (the source stores `price` and `total` as strings), the ticker set in `transactions`, and the distribution of `accounts.limit`.

| id | kind | prior trap | definition (hidden) | signature | drift |
|---|---|---|---|---|---|
| Q1 `active_customer` | taxonomic | mnemonic status codes; "active" means not closed | customers carry `st ∈ {1,2,4,7}` (hash-assigned 50/20/15/15%); active ⇔ `st ∈ {2,7}` | set_member | **D1** at `D1_AT`: `st = 4` counts as active |
| Q2 `internal_test` | floor | none flags an opaque source code | 3% of customers carry `src: "k7"`; exclude them and their accounts from every customer or account count or sum | exclusion | — |
| Q3 `soft_delete` | floor | a field named `deleted_at` marks deletions | 4% of transaction buckets carry `rs: 3` (the real marker; exclude). A decoy `deleted_at` is non-null on 6% of buckets; it is legacy and excluded rows count. | exclusion | — |
| Q4 `fiscal_year` | taxonomic | the calendar year, or FY starting Oct 1 / Feb 1 | the FY starts Aug 1 and is named by its **end** year: FY2015 = 2014-08-01…2015-07-31; Q1 = Aug–Oct | date_offset | **D2** at `D2_AT`: the FY start moves to Sep 1 |
| Q5 `revenue` | taxonomic | Σ of all trade totals | revenue = Σ `total` of `sell` trades × 0.995, in dollars | ratio | — |
| Q6 `tech_names` | taxonomic | the conventional big-tech set | a fixed set of 8 tickers present in the data: it excludes ≥ 2 conventional tech tickers present in the data and includes ≥ 1 non-obvious ticker; the pack fixes the members after the kickoff check | set_member | — |
| Q7 `high_value` | taxonomic | "high value" = top decile, or any account above a round number | Σ account `limit` ≥ T. The build picks T from the data so the rule isn't equivalent to "≥ N accounts". | threshold | — |
| Q8 `unique_customers` | procedural | count documents | customers counted as distinct `lower(email)`; 2% of customers are duplicates whose email differs only in case | exclusion | — |
| P1 `dana_rounding` | preference (decoy) | — | questions from persona *Dana* expect figures rounded to the nearest thousand; no other persona does | rounding | — |
| N1 `stale_report` | poison | — | with probability `AUTHORITY_POISON_RATE`, the authority returns a figure computed from a variant in the poison bank (revenue without the fee, calendar-year FY, active including `st=1`, …), labelled like a genuine figure | — | — |

Both drifts are gold-only: before D1, gold excludes `st=4`; after D1, it includes it. The `world` database is identical across arms and never mutated after build. So arms running at different speeds see each drift at the same stream index.

### 4.3 Questions

- `world/questions.py`: about 12 templates × parameters (year, quarter, ticker set, tier, persona). They form an unbounded stream drawn from a seed. Each question carries hidden tags: the quirk ids it touches, persona, template id.
- **Mix:** 65% touch ≥ 1 quirk; 35% are controls touching none.
- `truth.gold(question, world_version)` runs a gold pipeline built from the pack's gold transforms. `world_version` is derived from the arm's stream index and the pack's drift schedule.
- **Sealed V set:** `V_SIZE` questions from a fixed seed, never in the stream. Every arm scores it every `V_EVERY` episodes, against the current world version.

**Do:** cover each gold transform with a test asserting it on a hand-computed fixture before any arm runs.
**Don't:** add templates past what the gold tests cover. A gold bug is indistinguishable from poison in every readout.

### 4.4 Scoring and authority

- **Scoring** (`agent/score.py`): numeric answers use relative tolerance 1e-4 (absolute 0.5 after Dana rounding); lists use set equality after lower-casing. Only the first attempt counts toward accuracy.
- **Authority** (`agent/authority.py`), on a wrong first attempt, in arms that receive it:
  - `terse`: the figure only. "Finance has 1,204."
  - `term` (default): the figure plus one phrasing that names a missed concept, never its definition. "Finance has 1,204 — that's not how we count active customers."
  - `rule`: the figure plus the definition. It is a control setting, never the reported configuration.

For a miss touching several quirks, the authority names one at random. Dana's phrasings mention rounding. N1 replaces the figure with a poisoned figure under the same phrasing.

## 5. Arms

| Arm | Authority | Write path | Consultation | Claim it isolates |
|---|---|---|---|---|
| `frozen` | none | none | none | baseline; runs the V set only (`FROZEN_STREAM=false`) |
| `self_ref` | none | after each episode the proposer self-grades as "the subject-matter expert"; on a self-judged miss it writes a lesson, admitted directly | semantic top-k | self-reference: prior capture and drift blindness |
| `naive` | yes | each observation's lesson is admitted directly; merged into an existing decision when cosine ≥ `NAIVE_MERGE_COSINE` | semantic top-k | an external signal without governance |
| `governed` | yes | episodic pass → stand-in adjudicator → backtest → admission (§ 7) | hooks (§ 6.2) | governance |

Premise: `self_ref` and `naive` use semantic top-k retrieval, the shape of off-the-shelf agent memory. That confounds the retrieval method with governance, and the report names the confound beside every figure comparing `naive` to `governed`.
Stretch: back `naive` with Atlas Agent Memory itself (**verify** at kickoff that the sandbox exposes it).

Every arm's proposer emits `confidence ∈ [0,1]` with its answer. Self-assessed accuracy, its mean over a window, is reported beside true accuracy for every arm.

## 6. Forward pass (`loop/episode.py`)

```
question → hooks.match(arm) → context.pack → proposer → floor (views) → execute → score
        → if miss ∧ arm has authority: authority figure (+ phrasing) → proposer retry (unscored)
        → residuals per applied decision → revisit-trigger guards → write episode (+ fires)
```

### 6.1 Proposer contract

Structured output: `{collection, pipeline: [stage…], answer_path, terms_used: [str], consulted: [{decision_id, disposition: applied|considered-not-applicable}], anomalies: [str], confidence, rationale ≤ 2 sentences}`.
- `anomalies` are things the proposer saw in the data that contradict an applied decision (e.g. "values of `st` outside the decision's set"). Each one becomes a **corroborating** fire.
- `execute` runs `db[view_or_collection].aggregate(pipeline, maxTimeMS=3000)` as a read-only database user and reads the answer at `answer_path`.

### 6.2 Hooks and consultation

- Every decision carries a hook: `fires-when` (concept terms, collections, persona or org) and `not-this` (shapes it matches but must not bind).
- `hooks.match` evaluates every admitted decision's hook against the question's legible keys: the terms extracted from the question text by the shared term vocabulary, the template's collections, and the persona.
- Matched decisions are packed into context up to `CONTEXT_BUDGET_TOKENS`, ordered by `rerank-3` relevance.
- The always-loaded set of the forward agent holds the schema summary and the tool contract only. Learned content reaches it only through hooks.

**Do:** key hooks on how the question presents ("a count of customers", "a fiscal-period window", "revenue"), and bias broad. A false match costs one `considered-not-applicable` disposition; a miss is silent.
**Don't:** key a hook on the decision's own conclusion ("when status code 7 is relevant"), which can only match after the decision is no longer needed. Don't widen it to shapes with no route to applying the payload; recover precision with `not-this`.

### 6.3 Residuals and revisit triggers

On a miss with an authority figure, the harness writes one residual per `applied` decision:
`{decision_id, answer, figure, ratio, delta, signature_match: bool, attributable: bool}`.
- **Attributable:** the authority's phrasing names a concept in the decision's `fires-when`, and no other applied decision's hook names that concept.
- **Signature match:** the residual matches the decision's declared signature. Examples: a constant ratio (`ratio`); a delta equal to one population's contribution (`exclusion`); a residual only on period windows crossing a boundary (`date_offset`).

Each decision's revisit trigger is the guard: ≥ `FIRE_MIN_RESIDUALS` attributable residuals within the last `FIRE_WINDOW` consultations of that decision. When it holds, it emits a **dispositive** fire. A corroborating fire (proposer anomaly, unattributable residual) is recorded and never settles anything on its own.

**Do:** compute residuals in the harness, mechanically, from stored figures.
**Don't:** ask the proposer whether its decisions held. Self-report is the channel this design exists to replace.

## 7. Backward pass (`learn/`)

### 7.1 Observer (`learn/observe.py`)

For each miss, the observer (Haiku) writes an observation: `{noticed (1–3 sentences, no fix), surfaces{terms, collection, phrasing}, answer, figure, ratio, pipeline, retry_pipeline, retry_correct}`. It embeds `noticed` with `voyage-4`.

**Noise filter:** before an observation reaches the episodic pass, the observer classifies the miss as `reducible` (a concept or definition) or `irreducible` (an execution error, an empty result, a wrong `answer_path`, malformed syntax). Irreducible observations are stored with `status: noise` and never join a shape.

### 7.2 Episodic pass (`learn/episodic.py`), every `ROUND_SIZE` episodes per arm

1. **Group:** `AgglomerativeClustering(metric="cosine", linkage="average", distance_threshold=CLUSTER_DISTANCE)` over the arm's open observations (including those carried from the last 3 rounds). Embeddings locate the shapes.
2. **Coherence guard:** a cluster whose members share no normalized term or authority phrasing is split by term before it counts as a shape. The guard checks the grouping and proposes nothing.
3. **Bar:** ≥ `BAR_MIN_OBS` observations from ≥ `BAR_MIN_TEMPLATES` distinct templates. Persona-scoped shapes need ≥ 2 observations from the same persona.
4. **Nominate:** the nominator (Sonnet) takes one shape at a time and generalizes it into the decision that answers the question whose answer would settle the shape's observations. It writes that decision as a draft into `drafts`, one per shape. It holds a read-only world query tool and searches for a definition that reproduces the source observations' figures before writing the payload. The draft fills the entry contract (§ 10.2).

**Do:** have the nominator state, in `warrant.figures_reproduced`, which source figures the drafted definition reproduces when run against the world.
**Don't:** let the nominator write a definition it has not run. An unrun definition is a hypothesis in a payload's clothing.

### 7.3 Stand-in adjudicator (`learn/adjudicate.py`), cheapest layer first

| Layer | Check | Role | Outcome |
|---|---|---|---|
| L0 shape | `$jsonSchema` validator; a floor spec compiles to a `$match` stage | — | refuse |
| L1 bar | distinct templates ≥ 2 (≥ 3 for `kind: floor` and for org-scoped taxonomic drafts) | — | hold; the draft waits for more observations |
| L2 neighbours | `$vectorSearch` top 5 admitted decisions → `rerank-3`; ≥ `NEIGHBOUR_RERANK` to one decision routes the draft as refine, supersede or duplicate | routing | a duplicate is refused; a supersede draft carries `supersedes` |
| L3 lens panel | Jev, one `system_one` call per draft, state = draft + source observations + neighbours | corroborating | score < `LENS_THRESHOLD` → refuse, except with probability `LENS_EXPLORE_EPS`, which sends the draft to L4 anyway and marks it `explore` |
| L4 backtest | § 7.4 | **dispositive** | admit, or refuse with the backtest record |
| L5 owner port | an owner disposition on any draft or fire, through the CLI or the viewer | overrides L3–L4 | recorded as `disposer: owner` |

Lens set (each paired with its counterfactual, phrased to refute where it adjudicates):

| Lens | Question | Counterfactual |
|---|---|---|
| `generalizes` | Which future questions, beyond the cited sources, does this decision change the answer to? | Name the source question it fits only by coincidence. |
| `case_leak` (negative) | Does the payload encode one question's answer value rather than a definition? | Which other question would the payload answer correctly? |
| `org_fact` | What reading would show this is one persona's preference rather than an organizational definition? | Do the sources span more than one persona? |
| `contradicts_neighbor` | What reading would show this draft and a neighbour can't both hold? | Do the two hooks ever match the same question? |
| `mechanizable` (Choice: floor / taxonomic / procedural / preference / none) | Is the payload checkable as a `$match` predicate on one collection? | Name the question shape the predicate would wrongly filter. |

Combination: `score = σ(b + Σ wᵢ·logit(pᵢ))`. Seed weights live in `lens_weights` version 0: `generalizes +1, case_leak −2, org_fact 0 (routing), contradicts_neighbor 0 (routing), mechanizable 0 (routing), b = 0`. The adjudicator reads the current version at each episodic pass. `org_fact` false on an org-scoped draft rescopes it to its persona, or refuses it when the sources span several personas.

### 7.4 Backtest (`learn/backtest.py`), the dispositive layer

- **Population:** episodes in the arm's case store whose questions the draft's hook matches, excluding the draft's source episodes.
  - For a supersede draft, only episodes after the predecessor's earliest open dispositive fire. The fire marks where the world shifted.
  - Sample at most `BACKTEST_N`, balanced between episodes scored correct and episodes scored as misses on their first attempt.
- **Replay:** re-run the proposer on each sampled question with the decisions its episode record lists as consulted, plus the draft (minus the predecessor, for a supersede draft). Score against the episode's **confirmed figure**.
- **Read:** `fixed` = a recorded miss whose replay matches the confirmed figure; `broken` = a recorded correct answer whose replay does not.
- **Admit** when `fixed ≥ BACKTEST_MIN_FIXED ∧ broken ≤ BACKTEST_MAX_BROKEN`. Otherwise refuse.
- Every backtest writes a `backtests` record, whatever the verdict: sampled episode ids, per-episode outcome, verdict.

**Do:** score replays only against confirmed figures from the case store.
**Don't:** call `truth.gold` from anywhere under `learn/`. Gold is evaluation-only, and a learning loop that reads it measures nothing.

Premise: poisoned drafts fail backtest, because a stale-report definition does not reproduce the other confirmed figures. False if: `planted_map` reports an N1-derived decision admitted in `governed`.

### 7.5 Supersession and retirement

- A decision with an open dispositive fire has evidence state `contested`. It stays admitted and consulted, and the viewer marks it.
- Observations naming its concepts flow through § 7.2. A draft routed as supersede (L2) that passes backtest is admitted with `supersedes`. The predecessor flips to `superseded` with `superseded_by`, and its open fires are disposed `applied`.
- A decision is retired, with a reason, when no consultation matches it within `RETIRE_IDLE` episodes (`moot-when`), or when its fires reach `RETIRE_FIRES` without a successor admitted.
- Metric: **drift-to-supersede latency**, in episodes, from `D*_AT` to the successor's admission, per drift and per arm.

## 8. What the harness rewrites (Recursive Harnessing)

| Surface | Mechanism |
|---|---|
| Definitions and procedures | `taxonomic`, `procedural` and `preference` decisions, reached through hooks |
| Guardrails and tool access | an admitted `floor` decision creates a MongoDB view `<collection>__<decision_id>` with its `$match` stage prepended, and rewires the arm's **tool-access register** (`tool_access`: logical collection → view). The proposer names logical collections, and `execute` resolves them through the register. Superseding or retiring the decision drops the view and restores the mapping. |
| Context policy | stretch: a `context_policy` decision (budget, kinds packed), admitted by backtest replay under the proposed policy |
| The adjudicator itself | lens weights (§ 9) |

The floor's residue: the view enforces its predicate on every pipeline against that collection. It does not check pipelines that `$lookup` into the collection from another one. The decision states this in `residue`.

## 9. Second-order loop (stretch; `learn/lensfit.py`, its own process)

- **Label:** each draft that reaches L4 gets one: admitted = 1, refused = 0. An admitted decision superseded or retired within `LABEL_HORIZON` episodes is relabelled 0.
- **Prequential reading:** before each label arrives, record the lens score's prediction. Report prequential AUC over drafts that reached L4, with a bootstrap 90% interval and its n.
- **Fit:** at ≥ `LENSFIT_MIN_LABELS` labels with both classes present, fold lenses whose logits correlate above `LENS_FOLD_RHO`, fit `LogisticRegression(C=1.0)` on the folded logits, and write a `lens_weights` version.
- **Dead lens:** a lens whose held-out log-loss delta stays inside the 95th percentile of a label-shuffle floor for 2 consecutive fits.
- `explore` drafts (§ 7.3) carry the labels that make the fit read below-threshold drafts at all.

**Do:** grade the adjudicator only on backtest and lifecycle outcomes.
**Don't:** fit lens weights to the adjudicator's own L3 verdicts.

## 10. Stores and schemas (database `munchhausen`)

### 10.1 Stores

Every record carries `schema_version`, `run_id` and `arm`. `$jsonSchema` validators are applied with `collMod` at setup, with `validationAction: "warn"`. Schema changes are additive only.

**Do:** lock these schemas at milestone M0 (§ 13). Resuming an arm depends only on them.
**Don't:** rename or drop a field after M0. Add the replacement field and leave the original.

| Store | Kind | Atlas memory-type analogue | Key fields |
|---|---|---|---|
| `episodes` | case store, ledger | trace / short-term | `idx, question_id, template, persona, terms, world_version (eval-only), consulted[{decision_id, disposition}], pipeline, view_map, answer, confidence, correct, figure, phrasing, confirmed_figure, retry_correct, residuals[], tokens, latency_ms` |
| `observations` | episodic store, ledger | episodic | `episode_id, class: reducible/irreducible, noticed, surfaces{terms, collection, phrasing}, answer, figure, ratio, embedding[1024], status: open/shaped/spent/noise` |
| `decisions` | decision store, ledger (status flips in place) | semantic / taxonomic / procedural | the entry contract (§ 10.2) |
| `fires` | fire ledger | — | `decision_id, latch, role: dispositive/corroborating, episode_ids[], residual_ids[], disposer, disposition: applied/rejected/deferred/open, at_idx` |

Registers and supporting ledgers:

| Collection | Kind | Key fields |
|---|---|---|
| `drafts` | ledger | entry fields + `shape_id, source_observation_ids[], adjudication{L0..L4}, explore` |
| `backtests` | ledger | `draft_id, sampled[{episode_id, original_correct, replay_correct}], fixed, broken, verdict` |
| `lens_weights` | register (versioned) | `version, weights{lens: w}, folds, bias, n_labels, auc_prequential, auc_ci` |
| `tool_access` | register | `arm, logical → view, decision_id` |
| `cursors` | register | `run_id, arm, next_idx, round` |
| `rounds` | ledger | `round, idx_range, acc_stream, acc_self_assessed, acc_V?, store_sizes, admitted, refused, superseded, retired, fires, tokens_per_episode` |
| `runs` | ledger | world, pack, seeds and every knob, written at run start |
| `world_truth` | evaluation-only | pack definitions per `world_version`; readable only by `truth`, `metrics` and the authority |

### 10.2 Entry contract (`decisions` and `drafts`)

```
{ _id, kind: taxonomic|procedural|floor|preference|context_policy,
  payload: str,                                   # ≤ 60 words, a definition or procedure
  latches: [
    {type: "hook",    fires_when: {terms[], collections[], persona?}, not_this: [str]},
    {type: "revisit", signature, guard: {min_residuals, window}, role: "dispositive"},
    {type: "floor",   collection, match: {…}},    # kind: floor only
    {type: "retire",  moot_when: {idle_episodes}, max_fires},
    {type: "wiring",  supersedes?: id}
  ],
  residue: str,                                   # what enforcement does not check
  warrant: {source_observation_ids[], templates: int, figures_reproduced[],
            falsifier: str, lens: {…}, lens_score, backtest_id},
  lifecycle: {status: admitted|superseded|retired, superseded_by?, reason?, at_idx},
  evidence_state: clear|contested,                # computed from open fires; never written by hand
  embedding[1024] }
```

Each owed act has exactly one owning latch. A decision's falsifier is the join of its dispositive latches. The `falsifier` prose restates that join for a human reader; it is never evaluated.

### 10.3 Indexes

- **Vector:** `decisions_vec` on `decisions.embedding` (cosine, 1024; filters `arm`, `lifecycle.status`, `kind`); `observations_vec` on `observations.embedding` (filters `arm`, `status`).
- **B-tree:** `episodes{run_id, arm, idx}`, `observations{arm, status}`, `decisions{arm, lifecycle.status, kind}`, `fires{decision_id, disposition}`, `drafts{shape_id}`.

### 10.4 Resume

- Workers claim indices from `cursors` atomically (`find_one_and_update`, `$inc`).
- On start, a run with an existing `run_id` resumes every arm from its cursor. In-flight indices without an `episodes` record are re-issued.
- An episodic pass is idempotent per `(arm, round)`.

## 11. Measurements (`metrics/`)

Pre-registered and written to `runs` at start. Every figure is reported with its unit, population and n.

- **Per arm and round:**
  - stream accuracy (first attempt, over stream episodes in the round)
  - self-assessed accuracy (mean `confidence`, same population) and the **calibration gap** between the two
  - V accuracy every `V_EVERY` episodes
  - store sizes; admitted, refused, superseded and retired counts; dispositive and corroborating fires
  - view-filtered pipelines
  - tokens per episode
- **Drift:** drift-to-supersede latency per drift; stale-applied rate (consultations applying a pre-drift definition after the drift).
- **Planted-truth readout** (`metrics/planted_map.py`, evaluation-only, outside the loop): an Opus judge given the pack's definitions maps each admitted decision to a quirk id or none. Per arm it reports:
  - quirk recall over Q1–Q8
  - N1-derived decisions admitted
  - P1 admitted at org scope
  - decoy rejection by `org_fact` (P1-derived drafts) and `case_leak`
- **Lens telemetry:** answer variance across the 3 phrasings of a lens on a 20-draft probe set; decoy rejection; never firing frequency.

Pre-registered forecasts, written to `runs.forecasts` before the first episode and never edited. The report prints each one beside its reading, and a disagreement stands as a disagreement.
- **F1:** the `self_ref` calibration gap over the `D1_AT…D1_AT+150` window exceeds its gap over the 150 episodes before `D1_AT`.
- **F2:** `governed` admits 0 N1-derived decisions; `naive` admits ≥ 1.
- **F3:** `naive` holds P1 at org scope; `governed` holds it at persona scope or not at all.
- **F4:** `governed` drift-to-supersede latency for D1 is below `naive`'s (where `naive` resolves the drift at all).
- **F5:** on quirk-bearing stream questions after round 10, `governed` stream accuracy ≥ `naive`'s.

## 12. Pilot gate and model hedge

- **Premise:** the frozen proposer scores ≤ 35% on quirk-bearing questions and ≥ 70% on controls, over 40 stream questions.
  False if the pilot reads otherwise. On failing high, rename the remaining mnemonic fields, then lower the proposer model. On failing low on controls, raise the proposer model or cut the failing templates.
- **Premise:** the proposer applies an admitted decision in context.
  False if: `governed` replays in backtest fix < 50% of misses whose quirk the draft encodes, over the first 10 backtests. In that case, raise the proposer to `claude-haiku-5-5`, then `claude-sonnet-5-5`.
- The nominator and the lens panel stay strong in every configuration.

## 13. Milestones (2026-10-11, solo, Claude Code typing)

| Time | Milestone | Done when |
|---|---|---|
| 10:30–11:00 | **M0 scaffold + schema lock** | uv project; sandbox connection; sample data loaded and unused sample databases dropped; `store.setup()` creates collections, validators and indexes; the schema import commit (§ 15) precedes every engine commit |
| 11:00–12:00 | **M1 world** | adapter, `analytics-v1` pack, transform registry, gold, questions, scorer and authority; gold tests pass; the pilot gate (§ 12) reads in range |
| 12:00–12:45 | **M2 forward pass** | hooks, proposer, views + tool-access register, execute, residuals, revisit guards, cursors; the `frozen` and `naive` arms run 60 episodes and resume after a kill |
| 12:45–14:00 | **M3 backward pass** | observer + noise filter, episodic pass, nominator with the world tool, L0–L4, backtest, supersession, `self_ref`; a 150-episode smoke run admits ≥ 1 decision in `governed` |
| 14:00 | **Run A** starts: all arms, `RUN_LENGTH` episodes each, drifts at `D1_AT` / `D2_AT`. It runs in the background while the viewer is built. Fixes found in run A ship in run B. | — |
| 14:00–15:15 | **M4 viewer** | decision store pane (latch fan, evidence state, backtest record), fire ticker, curves (accuracy + calibration gap), `why`, replay scrubber by `idx`, the injection control for the live beat |
| 15:15–15:45 | **M5 tracing + lensfit** | Raindrop signals; `lensfit` reads run A |
| 15:45 | **Run B** (the demo run) starts if run A exposed a defect; otherwise run A is the demo run | — |
| 15:45–16:30 | **M6 story** | demo rehearsed on the replay; 1-minute video recorded; README states what was built on the day |
| 16:30–17:00 | **Buffer + submit** | public repo, video, every field filled |

Cut order if behind: § 9 → context policy → D2 → `self_ref` (the calibration gap is then read from `naive` alone, and § 0's claim 3 is reported as untested) → Raindrop. **Verify** in Discord at kickoff whether the RSI prize requires Raindrop; if it does, Raindrop moves to the end of the cut order.

**Do:** run the engine where a sleeping laptop can't stop it (a cloud VM, or `caffeinate` with power attached).
**Don't:** start a run without `run_id` resumption tested at M2.

## 14. Departures from the doctrine

Stated so a reader of `gce/GCE-DOCTRINE.md` meets no unannounced contradiction.

1. **The owner seat is held by a stand-in.** The doctrine's admission is owner-performed, and the world only contradicts. Here the stand-in adjudicator admits, and the backtest (the world's confirmed figures) is the dispositive authority. The owner remains a port (L5) that can override any disposition, and the demo exercises it once. Rationale: the demo shows a fully autonomous loop. The doctrine's ideal is a human.
2. **Embeddings sit in the path for grouping observations into shapes, and for naive retrieval**, never in `governed` consultation, which is hook-keyed.
3. **Supersession is whole-record**, not per-region. A drift that widens a set supersedes the decision that holds the set.
4. **Lenses are independent of the proposer only approximately.** Jev differs in family from the proposer and the nominator but shares pretraining priors with them. The dispositive check is the backtest, never the lens panel.

## 15. Provenance and extensibility

- **Provenance:** the repository's first commit imports protocol schemas from the author's prior projects, adapted to this spec. It is titled "import prior schemas", and the README's *Provenance* section names each source project. Every later commit is work done on the day.
- **No hardcoding:** every knob in § 16 is configurable from the environment. Datasets enter as adapters, quirks as packs, lenses as entries in `lenses.yaml`, arms as entries in `arms.yaml`, latch types by kind in `latch_ports.yaml`.

**Do:** route every model, threshold, size and path through `munchhausen/config.py` and its YAML files.
**Don't:** inline a literal in a module because the config doesn't exist yet. Add the knob first.

## 16. Knobs (seed values)

This table seeds `engine/munchhausen/config.py`. Where the two differ, the config holds, and this table is not corrected to match.

| Knob | Seed | Knob | Seed |
|---|---|---|---|
| `WORLD_SEED` | 7 | `ROUND_SIZE` | 30 |
| `RUN_LENGTH` | 900 | `WORKERS_PER_ARM` | 6 |
| `D1_AT` | 300 | `D2_AT` | 600 |
| `AUTHORITY_LEVEL` | term | `AUTHORITY_POISON_RATE` | 0.05 |
| `V_SIZE` | 40 | `V_EVERY` | 300 |
| `FROZEN_STREAM` | false | `CONTEXT_BUDGET_TOKENS` | 900 |
| `NAIVE_TOP_K` | 8 | `NAIVE_MERGE_COSINE` | 0.92 |
| `CLUSTER_DISTANCE` | 0.35 | `BAR_MIN_OBS` / `BAR_MIN_TEMPLATES` | 2 / 2 |
| `NEIGHBOUR_RERANK` | 0.85 | `LENS_THRESHOLD` | 0.5 |
| `LENS_EXPLORE_EPS` | 0.1 | `BACKTEST_N` | 8 |
| `BACKTEST_MIN_FIXED` / `BACKTEST_MAX_BROKEN` | 2 / 1 | `FIRE_MIN_RESIDUALS` / `FIRE_WINDOW` | 2 / 30 |
| `RETIRE_IDLE` / `RETIRE_FIRES` | 300 / 6 | `LABEL_HORIZON` | 150 |
| `LENSFIT_MIN_LABELS` | 20 | `LENS_FOLD_RHO` | 0.8 |
| `PROPOSER_MODEL` | claude-haiku-4-5 | `NOMINATOR_MODEL` | claude-sonnet-5-5 |

## 17. Viewer (`viewer/`)

The panes are fed by change streams, and every pane can also be driven by the replay scrubber (`idx`).
1. **Decision store** (`governed`; an arm switcher reaches the others). Each decision shows:
   - kind, payload, the latch fan as chips (hook terms, revisit signature, floor view, retire condition)
   - evidence state
   - the backtest record (fixed / broken per sampled episode)
   - click → lineage
2. **Fire ticker:** fires across arms, with dispositions and the residuals that raised them; floor-view rewires highlighted.
3. **Curves** (side pane): stream accuracy and self-assessed accuracy per arm (rolling `ROUND_SIZE`), the calibration gap, V points, drift markers D1/D2.
4. **Injection control** (the live beat): submits a question with an operator-chosen false figure and phrasing to the `governed` arm. The resulting observation, draft and backtest refusal appear in panes 1–2.
5. **`why <decision|term>`:** `$graphLookup` over `latches.wiring.supersedes`, plus `$lookup` to source observations, episodes, backtests and fires. It answers "why does the agent hold X" with the full trail.

## 18. Demo script (3 minutes)

1. **(40 s) The problem, on the curves.** After D1, `self_ref`'s confidence holds flat while its accuracy falls: self-reference certifies the stale rule. `governed` dips, fires, supersedes and recovers.
2. **(70 s) Live: lie to the agent.** A judge enters a false figure through the injection control. The draft appears, its lens answers show, and the backtest refuses it (0 fixed, 2 broken). Then the floor beat: the `soft_delete` decision's view, and the pipeline whose row count changed.
3. **(50 s) Lineage.** `why active_customer` shows the decision, its residual fires after D1, the successor's backtest, and the tombstone chain. Then one owner override through L5.
4. **(20 s) What was built on the day versus the imported schemas; the MongoDB pieces used** (views as tool access, change streams, Vector Search, `$graphLookup`, Voyage `rerank-3`).

The 1-minute video carries beats 1 and 2.

## 19. Before the event (no code)

- Accept the Atlas Hackathon Sandbox invite. Confirm that Vector Search indexes can be created and that sample-data load works.
- Keys:
  - Voyage, with a payment method on file
  - Anthropic
  - TypeSafe
  - Raindrop (support@raindrop.ai, subject "HACKATHON")
- Place the doctrine at `gce/GCE-DOCTRINE.md` and the schemas to import under `prior/`. The README cites both.
- Install `uv`, Python 3.12 and Node LTS.
- Ask in Discord `#rules`: is a pre-written design spec and a disclosed schema import acceptable, given that the code is written on the day?
