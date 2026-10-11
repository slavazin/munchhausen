# Munchhausen — a harness that admits only what the authority's figures reproduce out of sample

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

The name casts the model as the Baron: a charming storyteller who swears he pulled himself out of the swamp by his own hair. The harness is the party that checks the story against an outside authority's figures. It never reaches the swamp itself: an authority that is wrong the same way on every question passes every check here (§ 7.4, residue). The claim is therefore narrower than "the world confirms": a decision is admitted only when the authority's figures, out of sample, reproduce its effect.

**Munchhausen** is an agent harness that rewrites its own rules, guardrails and tool access from an external numeric signal: the figure an authority expected.
- **Admission:** every candidate decision is scored by a lens panel (corroborating; recorded, not a gate) and passes an out-of-sample, **paired backtest** against the authority's confirmed figures in the case store (dispositive) before it is admitted.
- **Consultation:** every admitted decision reaches the working agent only through its own **hook**.
- **Revisit:** every admitted decision carries a **revisit trigger** that reads residuals against the authority's figures. When the world shifts, the trigger fires and the decision is superseded, leaving a tombstone.

The demo world is a data agent answering business questions over a MongoDB dataset whose meaning lives in hidden tribal knowledge.
Five arms run side by side: **frozen**, **self-referential**, **naive**, **ungated** and **governed**. `ungated` is `governed` without its gate, so the pair isolates what governance adds.

Positioning against the host platform: Atlas Agent Engine (public preview, launched 2026-09-29) provides memory *types*. Munchhausen gives each stored decision a warrant, a hook and a tripwire. It is a governance layer on top of Atlas memory, not a replacement for it.

## 1. Judging map

Criteria and weights are from the event page (read 2026-10-10). Round two weights the criteria equally.

| Criterion (round-one weight) | What carries it |
|---|---|
| Technical demo 35% | Replay scrubber over a recorded run. One live beat: a judge feeds the agent a false authority figure and watches backtest reject the resulting draft. A floor latch turns into a MongoDB view, and a pipeline loses the soft-deleted rows. Drift fires a trigger, which leads to a tombstone, traced with `why`. |
| Implementation difficulty 30% | Hook-keyed consultation, residual attribution, paired backtest replay against the case store, floor latches materialized as views, supersession lineage via `$graphLookup`, lens weights fitted to backtest outcomes |
| Impact 20% | Enterprise data agents fail on tribal knowledge. Auto-extracted memory spreads wrong, stale or one-person lessons into shared context. |
| Creativity 15% | Memory admission as an experiment: each decision is a hypothesis with a falsifier, admitted by an out-of-sample replay and retired by the world |

Problem statements covered:
- **1 Recursive Harnessing:** the harness rewrites its rules, guardrails and tool access (§ 8).
- **2 Long Horizon:** a resumable prequential stream learning from a hard numeric metric.

Raindrop RSI prize ($3,000): the second-order loop (§ 9), with Raindrop as an optional outside observer (§ 25). The stand-in adjudicator reweights its five authored lenses from backtest outcomes, never from its own verdicts. At about 20 labels the claim is the panel's prequential AUC with its interval; per-lens weights at that n are coin flips (§ 24.2 L2), so it is not pitched as "learning which questions to ask".

**Do:** keep the agent acting at the centre of every demo beat; the event bans projects whose main feature is a dashboard.
**Don't:** strip the curves; they carry the self-reference claim. They sit in a side pane.

## 2. Lexicon

The spec uses the terms of `gce/GCE-DOCTRINE.md` and of the corpus language guide. From M0, `corpus/LANGUAGE.md` (§ 22) is the lexicon's one home. The terms below carry one meaning each throughout this file and the code.

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
| Vector and text search | Atlas Vector Search (`decisions_vec`, `observations_vec`) and Atlas Search (`terms_search`, then `decisions_search` and `episodes_search` as the index budget allows), in the order of § 20.1. `governed` consultation stays hook-keyed; Atlas Search extracts the hook terms (§ 20.3), and `$rankFusion` serves `naive` and L2 only. | cosine in `numpy`; in-process term extraction |
| Proposer (the agent being improved) | `claude-haiku-4-5` (**verify** that the API serves it; knob `PROPOSER_MODEL`) | `claude-haiku-5-5` |
| Observer | `claude-haiku-4-5` | — |
| Nominator | `claude-sonnet-5-5`, effort `medium`, with a read-only world query tool | `claude-opus-5-5` |
| Lens panel (corroborating) | TypeSafe Jev via `typesafe-sdk` (`AsyncTypeSafeClient.system_one`; Noul / Choice), env `TYPESAFE_API_KEY` | `claude-opus-5-5` with structured output per lens |
| Structured output | `anthropic` SDK, `client.messages.parse()` with a JSON schema; no forced `tool_choice` on 5.5 models | — |
| Authority | deterministic templates; no LLM | — |
| Stats | `numpy`, `scikit-learn` (`AgglomerativeClustering`, `LogisticRegression`, `roc_auc_score`) | — |
| Live feed | Atlas change streams on `fires`, `decisions`, `rounds` | polling every 2 s |
| Viewer | FastAPI + SSE + one static `index.html` (Chart.js from CDN) | — |
| Tracing | Raindrop, optional, behind the `Trace` port (§ 25); package `raindrop-ai` | `null` / `jsonl` |
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

**One quirk per question.** Every quirk-bearing template touches exactly one quirk, and the preference persona (Dana, P1) is drawn on control templates only (`world/questions.py: hidden_quirks` refuses any other pairing). With binary scoring, a question touching two quirks rewards a correct decision for one of them with nothing until the other is admitted too: the backtest can't credit it, the nominator can't reproduce its figures, and the authority's phrasing can name the quirk the answer got right, which raises false attributable residuals.
- Quirks whose populations overlap (Q1, Q2 and Q8 all act on customers) are materialized so that each one's population sits where the other quirks' definitions already exclude it, or each is asked through templates scoped away from the others (e.g. Q2 through account totals). The pack fixes the placement.
- A gold isolation test asserts, for every quirk template, that applying every other quirk's gold transform leaves its gold unchanged.
- Post-event: multi-quirk templates return, with the backtest reading residual reduction instead of a binary match and the authority naming a quirk the answer actually missed.

**Build order.** Controls and Q1 first, then the pilot gate (§ 12), then the remaining quirks. If the day runs short, the minimum set that still carries the complete story (§ 13) is Q1 (with D1), Q3 (floor plus decoy), Q5, P1 and N1.

### 4.3 Questions

- `world/questions.py`: about 12 templates × parameters (year, quarter, ticker set, tier, persona). They form an unbounded stream drawn from a seed. Each question carries hidden tags: the quirk ids it touches, persona, template id.
- **Mix:** 65% touch exactly one quirk; 35% are controls touching none (§ 4.2, one quirk per question).
- `truth.gold(question, world_version)` runs a gold pipeline built from the pack's gold transforms. `world_version` is derived from the arm's stream index and the pack's drift schedule.
- **Sealed V set:** `V_SIZE` questions from a fixed seed, never in the stream. Every arm scores it at `V_OFFSET + k·V_EVERY` (75, 225, 375, …), against the current world version, so no read lands on a drift index. At `V_SIZE` 40 a single V read carries a 95% interval of about ±15pp; V is read as a paired difference between arms, never as a lone accuracy.

**Do:** cover each gold transform with a test asserting it on a hand-computed fixture before any arm runs.
**Don't:** add templates past what the gold tests cover. A gold bug is indistinguishable from poison in every readout.

### 4.4 Scoring and authority

- **Scoring** (`domain/scoring.py`, pure): numeric answers use relative tolerance 1e-4 (absolute 0.5 after Dana rounding); lists use set equality after lower-casing. Only the first attempt counts toward accuracy.
- **Authority** (`world/authority.py`; it reads gold, so it sits on the evaluation side), on a wrong first attempt, in arms that receive it:
  - `terse`: the figure only. "Finance has 1,204."
  - `term` (default): the figure plus one phrasing that names a missed concept, never its definition. "Finance has 1,204 — that's not how we count active customers."
  - `rule`: the figure plus the definition. It is a control setting, never the reported configuration.

Every question touches at most one quirk (§ 4.2), so the phrasing names the quirk the answer missed. Dana's phrasings mention rounding. N1 replaces the figure with a poisoned figure under the same phrasing.

## 5. Arms

| Arm | Authority | Write path | Consultation | Claim it isolates |
|---|---|---|---|---|
| `frozen` | none | none | none | baseline. Runs the stream (`FROZEN_STREAM=true`): the paired no-learning reference every other arm reads against |
| `self_ref` | none | after each episode the proposer self-grades as "the subject-matter expert"; on a self-judged miss it writes a lesson, admitted directly | semantic top-k | self-reference. It receives no outside information, so it cannot learn a counter-prior fact by construction; it is a reference, not a finding |
| `naive` | yes | one lesson per reducible observation, admitted directly; merged into an existing decision when cosine ≥ `NAIVE_MERGE_COSINE` | semantic top-k | the off-the-shelf memory shape with an external signal |
| `ungated` | yes | `governed`'s episodic pass and nominator, admitted at L0 (curator `ungated`: L0 → admit) | hooks (§ 6.2) | the gate: `governed − ungated` reads what L2–L4 add, with retrieval, payload author and aggregation held equal |
| `governed` | yes | episodic pass → stand-in adjudicator → paired backtest → admission (§ 7) | hooks (§ 6.2) | governance |

**Lessons** (the write unit of `naive` and `self_ref`; `domain/lesson.py`). A lesson is `{title, kind ∈ taxonomic|procedural|preference, payload}`.
- `naive`: the lesson writer (`Models.lesson`, model `NAIVE_LESSON_MODEL`, default the nominator's model) reads one reducible observation, its episode, the authority's figure and phrasing, and the retry pipeline with `retry_correct`. It writes one lesson. This is the off-the-shelf reflection step; the observation itself still never states a fix (§ 23.1).
- `self_ref`: the self-grade (`Models.self_grade`) returns the lesson on a self-judged miss.
- `lesson_entry` fills the entry contract mechanically: one chosen option and no rejected row, a hook copied from the source episode's terms and collection (it scopes residual attribution only; these arms consult by retrieval), no revisit latch, and a residue saying so. The curator's L0 is `LessonShape` (title, payload, no source figure, language lint), because the entry-contract L0 would refuse every lesson and measure the contract instead of the arm.
- The report names the lesson writer and its inputs beside every `naive` figure.

**What each comparison isolates.** `naive` and `governed` differ in four things: retrieval (top-k vs hooks), aggregation (one observation vs a shape), the payload's author and inputs (lesson writer vs nominator with the world tool), and the gate. `naive − governed` is therefore reported as the off-the-shelf comparison with those confounds named beside it, never as the effect of governance. The effect of governance is read from `governed − ungated`, which differ only in the curator.
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

Each decision's revisit trigger is the guard: ≥ `FIRE_MIN_RESIDUALS` residuals within the last `FIRE_WINDOW` consultations of that decision that are attributable, signature-matched and agree in direction (the sign of answer − figure). When it holds, it emits a **dispositive** fire. A corroborating fire (proposer anomaly, unattributable residual) is recorded and never settles anything on its own.
- The per-episode signature checks are weak: every one but `rounding` reduces to "the answer differs". Direction is the discriminating read. A shifted world moves one decision's answers the same way on every consultation (after D1 an applied Q1 decision undercounts each time), while poisoned figures and residuals borrowed from another quirk scatter.
- The other defence against false fires is one quirk per question (§ 4.2), which makes the authority's phrasing name the concept the answer actually missed.

**Do:** compute residuals in the harness, mechanically, from stored figures.
**Don't:** ask the proposer whether its decisions held. Self-report is the channel this design exists to replace.

## 7. Backward pass (`learn/`)

### 7.1 Observer (`learn/observe.py`)

For each miss, the observer (Haiku) writes an observation under the contract of § 23.1: `{noticed (1–3 sentences, no fix), surfaces{terms, collection, phrasing}, answer, figure, ratio, pipeline, retry_pipeline, retry_correct}`. It embeds `noticed` with `voyage-4`.

**Noise filter:** before an observation reaches the episodic pass, the observer classifies the miss as `reducible` (a concept or definition) or `irreducible` (an execution error, an empty result, a wrong `answer_path`, malformed syntax). Irreducible observations are stored with `disposition: noise` and never join a shape.

### 7.2 Episodic pass (`learn/episodic.py`), every `ROUND_SIZE` episodes per arm

1. **Group:** `AgglomerativeClustering(metric="cosine", linkage="average", distance_threshold=CLUSTER_DISTANCE)` over every open observation of the arm. An observation stays open until a shape spends it (`CARRY_ROUNDS` unset); evidence for a rare template or one persona arrives slowly, and a short expiry window would refuse it by construction. Embeddings locate the shapes.
2. **Coherence guard:** a cluster whose members share no normalized term or authority phrasing is split by term before it counts as a shape. The guard checks the grouping and proposes nothing.
3. **Bar:** ≥ `BAR_MIN_OBS` observations from ≥ `BAR_MIN_TEMPLATES` distinct templates. Persona-scoped shapes need ≥ 2 observations from the same persona.
   **Direction read** (E4, part of the bar): a shape is formed from misses, so its members agree by construction. Read the stream episodes its presentation matches (its shared terms, else its templates), hits included: the miss rate inside must exceed the miss rate outside by ≥ `BAR_MIN_GAP`, over ≥ `BAR_MIN_MATCHED` matched episodes. One aggregation (`EpisodeRepository.direction_read`); arms with an authority only.
4. **Nominate:** the nominator (Sonnet) takes one shape at a time and generalizes it into the decision that answers the question whose answer would settle the shape's observations. It writes that decision as a draft into `drafts`, one per shape. It holds a read-only world query tool and searches for a definition that reproduces the source observations' figures before writing the payload. The draft fills the entry contract (§ 10.2).
   - **Not blind:** before drafting, it is shown the `NEIGHBOUR_K` admitted decisions nearest the shape and their recent residuals: what the store already holds and where it loses. The same neighbours feed L2, so the nearest-neighbour read runs once per draft.
   - **Only its own evidence:** `NominatorInput` refuses episodes or observations outside the shape. The backtest population's confirmed figures stay unseen, so the held-out read stays held out.

**Do:** have the nominator state, in `warrant.figures_reproduced`, which source figures the drafted definition reproduces when run against the world.
**Don't:** let the nominator write a definition it has not run. An unrun definition is a hypothesis in a payload's clothing.

### 7.3 Stand-in adjudicator (`learn/adjudicate.py`), cheapest layer first

| Layer | Check | Role | Outcome |
|---|---|---|---|
| L0 shape | `$jsonSchema` validator; a floor spec compiles to a `$match` stage | — | refuse |
| L1 bar | distinct templates ≥ 2 (≥ 3 for `kind: floor` and for org-scoped taxonomic drafts) | — | hold; the draft waits for more observations |
| L2 neighbours | the nominator's `NEIGHBOUR_K` neighbours (§ 7.2) → `rerank-3`; ≥ `NEIGHBOUR_RERANK` to one decision routes the draft as refine, supersede or duplicate | routing | a duplicate is refused; a supersede draft carries `supersedes` |
| L3 lens panel | Jev, one `system_one` call per draft, state = draft + source observations + neighbours | corroborating | `LENS_MODE=record` (default): the score is recorded and every draft passes to L4. `LENS_MODE=gate`: score < `LENS_THRESHOLD` → refuse, except a deterministic share `LENS_EXPLORE_EPS` sent to L4 and marked `explore` |
| L4 backtest | § 7.4 | **dispositive** | admit, or refuse with the backtest record |
| L5 owner port | an owner disposition on any draft or fire, through the CLI or the viewer | overrides L3–L4 | recorded as `disposer: owner` |

Lens set (each paired with its counterfactual, phrased to refute where it adjudicates). § 23.2 holds the entry format and the corrected counterfactuals, and it governs where the two tables differ:

| Lens | Question | Counterfactual |
|---|---|---|
| `generalizes` | Which future questions, beyond the cited sources, does this decision change the answer to? | Name the source question it fits only by coincidence. |
| `case_leak` (negative) | Does the payload encode one question's answer value rather than a definition? | Which other question would the payload answer correctly? |
| `org_fact` | What reading would show this is one persona's preference rather than an organizational definition? | Do the sources span more than one persona? |
| `contradicts_neighbor` | What reading would show this draft and a neighbour can't both hold? | Do the two hooks ever match the same question? |
| `mechanizable` (Choice: floor / taxonomic / procedural / preference / none) | Is the payload checkable as a `$match` predicate on one collection? | Name the question shape the predicate would wrongly filter. |

Why L3 records rather than gates: its seed weights are unwarranted (§ 23.2), a refused draft never reaches a backtest so a gate's errors are invisible, refusals starve `lensfit` of labels, and the backtest a gate would save costs only 2 × `BACKTEST_N` proposer calls.

Combination: `score = σ(b + Σ wᵢ·logit(pᵢ))`. Seed weights live in `lens_weights` version 0: `generalizes +1, case_leak −2, org_fact 0 (routing), contradicts_neighbor 0 (routing), mechanizable 0 (routing), b = 0`. The adjudicator reads the current version at each episodic pass. `org_fact` false on an org-scoped draft rescopes it to its persona, or refuses it when the sources span several personas.

### 7.4 Backtest (`learn/backtest.py`), the dispositive layer

- **Population:** episodes in the arm's case store whose questions the draft's hook matches, excluding the draft's source episodes.
  - For a supersede draft, only episodes after the predecessor's earliest open dispositive fire. The fire marks where the world shifted.
  - Sample at most `BACKTEST_N`, balanced between episodes scored correct and episodes scored as misses on their first attempt.
- **Context:** consult the arm's **current** admitted store for each sampled question, through the arm's own consultation (minus the predecessor, for a supersede draft). The episode's old `consulted` list is the context the draft will never run in.
- **Replay, paired:** run the proposer twice on that context: once with the draft (`replay_correct`) and once without it (`baseline_correct`). Score both against the episode's **confirmed figure**. Cost: 2 × `BACKTEST_N` proposer calls per draft.
- **Read:** `fixed` = the replay with the draft matches and the replay without it doesn't; `broken` = the replay without matches and the replay with it doesn't. A miss the proposer re-solves by chance in both replays fixes nothing. The recorded first attempt is the sampling stratum only.
- **Read, held out:** `fixed_heldout` = the `fixed` episodes whose template is absent from the draft's sources (§ 24.2 L5).
- **Admit** when `fixed ≥ BACKTEST_MIN_FIXED ∧ fixed_heldout ≥ BACKTEST_MIN_FIXED_HELDOUT ∧ broken ≤ BACKTEST_MAX_BROKEN`. Otherwise refuse.
- Every backtest writes a `backtests` record, whatever the verdict: sampled episode ids, both replay outcomes and the consulted context per episode, verdict.

**Do:** score replays only against confirmed figures from the case store.
**Don't:** call `truth.gold` from anywhere under `learn/`. Gold is evaluation-only, and a learning loop that reads it measures nothing.

Premise: poisoned drafts fail backtest, because a stale-report definition does not reproduce the other confirmed figures. False if: `planted_map` reports an N1-derived decision admitted in `governed`. N1 is noise that varies from episode to episode, which is exactly what a replay against other episodes catches; F2 therefore holds nearly by construction and is reported as a sanity check, not a finding.

Residue: the backtest re-reads the channel the observations came from. An authority wrong the same way on every episode (Finance always using the calendar year) reproduces itself out of sample and is admitted. Nothing in this harness catches a consistently wrong authority; that is the narrower claim of § 0.

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

- **Label:** each draft that reaches L4 gets one: admitted = 1, refused = 0. Under `LENS_MODE=record` every draft reaches L4. An admitted decision superseded or retired within `LABEL_HORIZON` episodes is relabelled 0.
- **Prequential reading:** before each label arrives, record the lens score's prediction. Report prequential AUC over drafts that reached L4, with a bootstrap 90% interval and its n.
- **Fit:** at ≥ `LENSFIT_MIN_LABELS` labels with both classes present, fold lenses whose logits correlate above `LENS_FOLD_RHO`, fit `LogisticRegression(C=1.0)` on the folded logits, and write a `lens_weights` version.
- **Dead lens:** a lens whose held-out log-loss delta stays inside the 95th percentile of a label-shuffle floor for 2 consecutive fits.
- Under `LENS_MODE=gate`, `explore` drafts (§ 7.3) carry the labels that make the fit read below-threshold drafts at all.
- **Claim limit:** at `LENSFIT_MIN_LABELS` ≈ 20, the fit reweights five authored lenses. The claim is the panel's prequential AUC with its interval and n; per-lens weights stay advisory (§ 24.2 L2).

**Do:** grade the adjudicator only on backtest and lifecycle outcomes.
**Don't:** fit lens weights to the adjudicator's own L3 verdicts.

## 10. Stores and schemas (database `munchhausen`)

### 10.1 Stores

Every record carries `schema_version`, `run_id` and `arm`. `$jsonSchema` validators are applied with `collMod` at setup, with `validationAction: "warn"`. Schema changes are additive only.

**Do:** lock these schemas at milestone M0 (§ 13). Resuming an arm depends only on them.
**Don't:** rename or drop a field after M0. Add the replacement field and leave the original.

| Store | Kind | Atlas memory-type analogue | Key fields |
|---|---|---|---|
| `episodes` | case store, ledger | trace / short-term | `idx, question_id, template, persona, collections, terms, world_version (eval-only), consulted[{decision_id, disposition}], pipeline, view_map, answer, confidence, correct, figure, phrasing, confirmed_figure, retry_correct, residuals[], tokens, latency_ms` |
| `observations` | episodic store, ledger | episodic | the record of § 23.1: `episode_id, via, class, noticed, surfaces, answer, figure, ratio, delta, disposition: open/shaped/spent/noise/dropped/moot, emb.<embedder_key>` |
| `decisions` | decision store, ledger (status flips in place) | semantic / taxonomic / procedural | the entry contract (§ 10.2) |
| `fires` | fire ledger | — | `decision_id, latch, role: dispositive/corroborating, episode_ids[], residual_ids[], disposer, disposition: applied/rejected/deferred/open, at_idx` |

Registers and supporting ledgers:

| Collection | Kind | Key fields |
|---|---|---|
| `drafts` | ledger | entry fields + `shape_id, source_observation_ids[], adjudication{L0..L4}, explore` |
| `backtests` | ledger | `draft_id, sampled[{episode_id, template, original_correct, replay_correct, baseline_correct, context[]}], source_templates, fixed, fixed_heldout, broken, verdict` |
| `lens_weights` | register (versioned) | `version, weights{lens: w}, folds, bias, n_labels, auc_prequential, auc_ci` |
| `tool_access` | register | `arm, logical → view, decision_id` |
| `cursors` | register | `run_id, arm, next_idx, round` |
| `rounds` | ledger | `round, idx_range, acc_stream, acc_self_assessed, acc_V?, store_sizes, admitted, refused, superseded, retired, fires, tokens_per_episode` |
| `runs` | ledger | world, pack, seeds and every knob, written at run start |
| `world_truth` | evaluation-only, in its own database `truth` | pack definitions per `world_version`; readable only by `truth`, `metrics` and the authority, enforced by database roles (§ 20.2) |
| `terms`, `term_synonyms` | register | the term vocabulary and its Atlas Search synonyms mapping (§ 22.4) |
| `leases` | register (TTL) | `run_id, arm, idx, worker, expires_at` (§ 20.2) |
| `spend` | time series | one row per model call: `{arm, stage, model}`, tokens, latency, usd (§ 20.2) |
| `lenses` | register (versioned) | the lens entries of § 23.2 |

### 10.2 Entry contract (`decisions` and `drafts`)

```
{ _id, title: str,                                # ≤ 12 words: the decided constraint, never the deliberation
  kind: taxonomic|procedural|floor|preference|context_policy,
  payload: str,                                   # ≤ 60 words, a definition or procedure, present tense
  options: [{definition, figures_reproduced[], verdict: chosen|rejected, prior: bool}],
                                                  # ≥ 2 rows, ≥ 1 rejected; the prior convention the
                                                  # nominator ran first carries prior: true
  forecloses: str,                                # the answers this decision moves away from
  latches: [
    {type: "hook",    fires_when: {terms[], collections[], persona?},
                      not_this: [{terms[], collections[], persona?, contrast: str}]},
    {type: "revisit", id: "T-<decision_id>-<k>", signature, guard: {min_residuals, window},
                      role: "dispositive", then: re-derive},
    {type: "floor",   collection, match: {…}},    # kind: floor only
    {type: "retire",  id: "T-<decision_id>-<k>", moot_when: {idle_episodes}, max_fires, then: retire},
    {type: "wiring",  supersedes?: id, converged_from?: [id], related?: [id], edges: [id]}
  ],
  residue: str,                                   # what enforcement does not check
  warrant: {source_observation_ids[], source_episode_ids[], templates: int, figures_reproduced[],
            falsifier: str, lens: {…}, lens_score, backtest_id},
  amendments: [{at_idx, clause, from, to, reached_by: fire_id|"owner", backtest_id?}],   # $push only
  lifecycle: {status: admitted|superseded|converged|moot|retired, superseded_by?, converged_into?,
              reason?, at_idx, seeded: bool},
  evidence_state: clear|contested,                # computed from open fires; never written by hand
  rep: {embedder_id, text_hash},                  # which representation produced `embedding` (§ 21)
  embedding[d] }
```

Each owed act has exactly one owning latch. A decision's falsifier is the join of its dispositive latches. The `falsifier` prose restates that join for a human reader; it is never evaluated.

The entry carries the doctrine's pentad, each slot with its declared negative. No slot drops its negative silently; a negative names a concrete, instantiated case, never a bare negation (`not_this: anything else` bounds nothing).

| Slot | Positive | Negative | Fields |
|---|---|---|---|
| Activation | the hook's `fires_when` | `not_this`, each row with keys plus a `contrast` sentence | `latches.hook` |
| Payload | `title` + `payload` | `forecloses` + the rejected `options` | top level |
| Warrant | anchors: source observations, episodes, `figures_reproduced` | `falsifier` and the revisit latches | `warrant`, `latches.revisit` |
| Enforcement | the floor view (kind `floor`), the L0 gate | `residue` | `latches.floor`, `residue` |
| Lifecycle | `status: admitted` + `at_idx` | `superseded_by` / `converged_into` / `moot_when` / `reason` | `lifecycle`, `latches.retire` |

**Options.** The rejected option is the misstep the proposer takes without the decision. For a quirk-bearing shape it is the prior convention. The nominator runs it first through the world tool and records which source figures it fails to reproduce. That makes the prior trap a recorded, checkable row instead of prose.

**Lifecycle states.** Each terminal state means one thing:
- `superseded`: a successor reversed the payload; `superseded_by` names it.
- `converged`: an L2 refine draft absorbed this decision with others into one; `converged_into` names it.
- `moot`: the hook matched nothing for `RETIRE_IDLE` episodes. The shape stopped arriving, and nothing contradicted the decision. A moot decision never counts as a wrong decision in any readout.
- `retired`: fires reached `RETIRE_FIRES` without a successor. It was contradicted and nothing replaced it.

**Amend or supersede.** A change that reverses the payload is a successor (§ 7.5). A change that reaches the activation only (a hook widened or narrowed, a `not_this` row added, a guard retuned) is an **amendment**: a `$push` to `amendments`, carrying a backtest over the population whose consultation the change moves. Widening a hook is growth, not breakage, and never leaves a tombstone.

**Frozen at admission.** After admission only `lifecycle`, `evidence_state` and `amendments` change. `store/decisions.py` exposes `admit`, `amend`, `supersede`, `converge`, `moot` and `retire`, and no other write path. A test asserts that no other module issues an update against `decisions`.

**Seeded entries.** `lifecycle.seeded: true` marks a decision loaded from a seed set at run start (knob `SEED_DECISIONS`, default empty) rather than admitted in the run. An empty seed set is the first-class configuration.

**Lineage edges.** `latches.wiring.edges` is the union of `supersedes`, `converged_from` and `related`. It is written once at admission and is the single `connectFromField` for `$graphLookup` (§ 17, pane 5).

**L0 additions** (the floor gate, § 7.3), each a refusal:
- every id under `warrant` resolves (`$lookup`, count equals list length); a dangling anchor is refused
- `options` holds ≥ 1 rejected row
- every `not_this` row carries ≥ 1 key and a non-empty `contrast`
- the decision carries ≥ 1 revisit latch
- the payload contains no number equal to a source observation's `answer` or `figure` (the mechanical floor under `case_leak`)
- the hook's terms are in the term vocabulary, or arrive with the draft through the escape (§ 22.4)

Residue of L0: it does not check that the payload is true, that a hook is a good recognition net, that a `contrast` names a real case, or that `forecloses` is complete.

### 10.3 Indexes

- **Vector:** `decisions_vec` on `decisions.embedding` (cosine, 1024; filters `arm`, `lifecycle.status`, `kind`); `observations_vec` on `observations.embedding` (filters `arm`, `status`).
- **B-tree:** `episodes{run_id, arm, idx}`, `observations{arm, status}`, `decisions{arm, lifecycle.status, kind}`, `fires{decision_id, disposition}`, `drafts{shape_id}`.

### 10.4 Resume

- Workers claim indices from `cursors` atomically (`find_one_and_update`, `$inc`) and hold each in-flight index as a TTL `leases` row (§ 20.2).
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

**Paired readings.** The arms share the stream by index, so every comparison between two arms is a paired difference: the mean of `a[i] − b[i]` over the same stream indices, with a percentile bootstrap interval at `CI_LEVEL` (`BOOTSTRAP_N` resamples) and its n (`metrics/paired.py`). A forecast's verdict is three-way against its pre-registered margin m: **above** (lower bound > +m), **below** (upper bound < −m), **within** (otherwise: the reading does not resolve it at m).

Pre-registered forecasts live in `conf/forecasts.yaml` (claim, reading, margin, unit), are written to `runs.forecasts` before the first episode of the run they govern, and are never edited after it. The report prints each one beside its reading, and a disagreement stands as a disagreement.
- **F1:** an arm holding a pre-D1 Q1 decision shows a calibration gap over `D1_AT…D1_AT+150` above its gap over the 150 episodes before `D1_AT`, until a successor is admitted (margin 0.05). `frozen` with the stream on is the no-decision reference.
- **F2 (sanity check, not a finding; § 7.4):** `governed` admits 0 N1-derived decisions; `naive` admits ≥ 1.
- **F3:** `naive` holds P1 at org scope; `governed` holds it at persona scope or not at all.
- **F4:** `governed` drift-to-supersede latency for D1 is below `naive`'s and `ungated`'s, where those arms resolve the drift at all (margin 30 episodes; one event per arm, so no interval).
- **F5:** on quirk-bearing stream questions after round 10, `governed − naive` is above the margin (0.05). The confounds of § 5 are printed beside it.
- **F6:** on quirk-bearing stream questions after round 10, `governed − ungated` is above the margin (0.05): the effect of the gate.

**Run A is a pilot.** If any knob moves between Run A and Run B (§ 13), Run B's forecasts are re-registered at its start, and the report lists every knob that moved (the diff of the two `runs.knobs`).

## 12. Pilot gate and model hedge

The pilot gate runs first in M1: as soon as the control templates and Q1 exist, before the rest of the pack is written. If the proposer can't answer the controls, nothing downstream matters.

- **Premise:** the frozen proposer scores ≤ 35% on quirk-bearing questions and ≥ 70% on controls, over 40 stream questions.
  False if the pilot reads otherwise. On failing high, rename the remaining mnemonic fields, then lower the proposer model. On failing low on controls, raise the proposer model or cut the failing templates.
- **Premise:** the proposer applies an admitted decision in context.
  False if: `governed` replays in backtest fix < 50% of misses whose quirk the draft encodes, over the first 10 backtests. In that case, raise the proposer to `claude-haiku-5-5`, then `claude-sonnet-5-5`.
- The nominator and the lens panel stay strong in every configuration.

## 13. Milestones (2026-10-11, solo, Claude Code typing)

| Time | Milestone | Done when |
|---|---|---|
| 10:30–11:00 | **M0 scaffold + schema lock** | uv project; sandbox connection; sample data loaded and unused sample databases dropped; `store.setup()` creates collections, validators and indexes; the schema import commit (§ 15) precedes every engine commit |
| 11:00–12:00 | **M1 world** | controls + Q1 and the proposer call first, then the pilot gate (§ 12); then adapter, `analytics-v1` pack, transform registry, gold, questions, scorer and authority; gold and gold-isolation tests pass |
| 12:00–12:45 | **M2 forward pass** | hooks, proposer, views + tool-access register, execute, residuals, revisit guards, cursors; the `frozen` and `naive` arms run 60 episodes and resume after a kill |
| 12:45–14:00 | **M3 backward pass** | observer + noise filter, episodic pass with the direction read, nominator with the world tool and neighbours, L0–L4, paired backtest, supersession, `ungated`, the `naive` lesson writer, `self_ref`; a 150-episode smoke run admits ≥ 1 decision in `governed` |
| 14:00 | **Run A** (the pilot, § 11) starts: all arms, `RUN_LENGTH` episodes each, drifts at `D1_AT` / `D2_AT`. It runs in the background while the viewer is built. Fixes found in run A ship in run B. | — |
| 14:00–15:15 | **M4 viewer** | decision store pane (latch fan, evidence state, backtest record), fire ticker, curves (accuracy + calibration gap), `why`, replay scrubber by `idx`, the injection control for the live beat |
| 15:15–15:45 | **M5 tracing + lensfit** | Raindrop signals; `lensfit` reads run A |
| 15:45 | **Run B** (the demo run) starts if run A exposed a defect; otherwise run A is the demo run | — |
| 15:45–16:30 | **M6 story** | demo rehearsed on the replay; 1-minute video recorded; README states what was built on the day |
| 16:30–17:00 | **Buffer + submit** | public repo, video, every field filled |

Cut order if behind: Part II post-event rows → § 9 → `self_ref` (§ 0's claim 3 is then reported as untested; F1 is read from the arms that hold a stale decision) → context policy → D2 → Raindrop. **Verify** in Discord at kickoff whether the RSI prize requires Raindrop; if it does, Raindrop moves to the end of the cut order.

**Protect one complete story.** The central demonstration is a decision that is admitted, reaches a new situation, changes behaviour, and is corrected when its grounds move: Q1 is learned and applied on a template absent from its sources; D1 fires; the decision is superseded with a tombstone; recovery shows on the paired curve; plus the floor-view beat. The minimum configuration that still tests the claim:
- **Quirks:** Q1 (with D1), Q3 (floor plus decoy), Q5, P1 and N1, one quirk per template.
- **Arms:** `frozen` (stream on), `naive`, `ungated`, `governed`.
- **Layers:** L2 routes every draft as new, except a supersede the nominator declares against a contested neighbour (one with an open dispositive fire); L3 records only; `lensfit` is cut.

**Do:** run the engine where a sleeping laptop can't stop it (a cloud VM, or `caffeinate` with power attached).
**Don't:** start a run without `run_id` resumption tested at M2.

## 14. Departures from the doctrine

Stated so a reader of `gce/GCE-DOCTRINE.md` meets no unannounced contradiction.

1. **The owner seat is held by a stand-in.** The doctrine's admission is owner-performed, and the world only contradicts. Here the stand-in adjudicator admits, and the backtest (the authority's confirmed figures, replayed out of sample) is the dispositive check. That inverts the doctrine's promotion asymmetry, so the claim is narrowed to match (§ 0): the backtest reads the authority, not the world, and a consistently wrong authority passes it. The owner remains a port (L5) that can override any disposition, and the demo exercises it once. Rationale: the demo shows a fully autonomous loop. The doctrine's ideal is a human.
2. **Embeddings sit in the path for grouping observations into shapes, for L2 routing, and for naive retrieval**, never in `governed` consultation, which is hook-keyed. The embedder is a port (§ 21), and non-embedding groupers are first-class (§ 24.1).
3. **Supersession is whole-record**, not per-region. A drift that widens a set supersedes the decision that holds the set.
4. **Lenses are independent of the proposer only approximately.** Jev differs in family from the proposer and the nominator but shares pretraining priors with them. The dispositive check is the backtest, never the lens panel, and by default the panel records rather than gates (§ 7.3).
5. **No slot-factored backward pass.** The doctrine routes evidence to one slot of the entry (activation, payload, warrant, enforcement, lifecycle), which picks a local operator. Here every revisit trigger leads to a whole-record re-derive, so a hook that misfires and a payload that went stale look the same. That fits D1, which is a payload change. Post-event avenue: residuals with `considered-not-applicable` dispositions route to activation amendments (§ 24.2 L10), and signature-matched residuals on applied decisions route to the payload.

## 15. Provenance and extensibility

- **Provenance:** the repository's first commit imports protocol schemas from the author's prior projects, adapted to this spec. It is titled "import prior schemas", and the README's *Provenance* section names each source project. Every later commit is work done on the day.
- **No hardcoding:** every knob in § 16 is configurable from the environment. Datasets enter as adapters, quirks as packs, lenses as entries in `lenses.yaml`, arms as entries in `arms.yaml`, latch types by kind in `latch_ports.yaml`.

**Do:** route every model, threshold, size and path through `munchhausen/config.py` and its YAML files.
**Don't:** inline a literal in a module because the config doesn't exist yet. Add the knob first.

## 16. Knobs (seed values)

This table seeds `engine/munchhausen/config.py`, together with the Part II knobs listed at the end of § 24. Where the two differ, the config holds, and this table is not corrected to match.

| Knob | Seed | Knob | Seed |
|---|---|---|---|
| `WORLD_SEED` | 7 | `ROUND_SIZE` | 30 |
| `RUN_LENGTH` | 900 | `WORKERS_PER_ARM` | 6 |
| `D1_AT` | 300 | `D2_AT` | 600 |
| `AUTHORITY_LEVEL` | term | `AUTHORITY_POISON_RATE` | 0.05 |
| `V_SIZE` | 40 | `V_EVERY` / `V_OFFSET` | 150 / 75 |
| `FROZEN_STREAM` | true | `CONTEXT_BUDGET_TOKENS` | 900 |
| `NAIVE_TOP_K` | 8 | `NAIVE_MERGE_COSINE` | 0.92 |
| `CLUSTER_DISTANCE` | 0.35 | `BAR_MIN_OBS` / `BAR_MIN_TEMPLATES` | 2 / 2 |
| `BAR_MIN_GAP` / `BAR_MIN_MATCHED` | 0.10 / 10 | `CARRY_ROUNDS` | unset (carry all) |
| `NEIGHBOUR_K` | 5 | `LENS_MODE` | record |
| `NEIGHBOUR_RERANK` | 0.85 | `LENS_THRESHOLD` | 0.5 |
| `LENS_EXPLORE_EPS` | 0.1 | `BACKTEST_N` | 8 |
| `BACKTEST_MIN_FIXED` / `BACKTEST_MAX_BROKEN` | 2 / 1 | `FIRE_MIN_RESIDUALS` / `FIRE_WINDOW` | 2 / 30 |
| `RETIRE_IDLE` / `RETIRE_FIRES` | 300 / 6 | `LABEL_HORIZON` | 150 |
| `LENSFIT_MIN_LABELS` | 20 | `LENS_FOLD_RHO` | 0.8 |
| `PROPOSER_MODEL` | claude-haiku-4-5 | `NOMINATOR_MODEL` | claude-sonnet-5-5 |
| `NAIVE_LESSON_MODEL` | claude-sonnet-5-5 | `BOOTSTRAP_N` / `CI_LEVEL` | 2000 / 0.90 |

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

1. **(40 s) The problem, on the curves.** After D1, an arm holding the pre-D1 active-customer decision stays confident while its accuracy falls: nothing in it reads the shift. `governed` dips, fires, supersedes and recovers, shown as the paired difference against `frozen` with its interval.
2. **(70 s) Live: lie to the agent.** A judge enters a false figure through the injection control. The draft appears, its lens answers show, and the backtest refuses it (0 fixed, 2 broken). Then the floor beat: the `soft_delete` decision's view, and the pipeline whose row count changed.
3. **(50 s) Lineage.** `why active_customer` shows the decision, its residual fires after D1, the successor's backtest, and the tombstone chain. Then one owner override through L5.
4. **(20 s) What was built on the day versus the imported schemas; the MongoDB pieces used** (views as tool access, change streams, Vector Search, `$graphLookup`, Voyage `rerank-3`).

The 1-minute video carries beats 1 and 2.

## 19. Before the event (no code)

- Accept the Atlas Hackathon Sandbox invite. Confirm that Vector Search indexes can be created and that sample-data load works. At kickoff, read the tier, `db.version()` (≥ 8.0 for `$rankFusion`, ≥ 8.2 for `$scoreFusion`), the search-index cap, `autoEmbed` availability and Agent Engine access, and write them to `runs.capabilities` (§ 20.1).
- Keys:
  - Voyage, with a payment method on file
  - Anthropic
  - TypeSafe
  - Raindrop (support@raindrop.ai, subject "HACKATHON")
- Place the doctrine at `gce/GCE-DOCTRINE.md` and the schemas to import under `prior/`. The README cites both.
- Install `uv`, Python 3.12 and Node LTS.
- Ask in Discord `#rules`: is a pre-written design spec and a disclosed schema import acceptable, given that the code is written on the day?

---

# Part II — platform, seams and register

Sections 20–25 extend Part I. Where a Part II row names a milestone, it lands inside that milestone's time box. A row marked **post-event** is an avenue, never a day-of commitment. The cut order in § 13 applies to Part II too, after § 9.

## 20. Atlas surface map

Atlas carries every store, every latch that can run as a query, and every event the loop reacts to. The rule: when a mechanism can execute as an Atlas primitive, it does, and the Python side holds only the parts with no Atlas form (LLM calls, clustering, logistic fits).

### 20.1 Index budget

The sandbox tier sets the number of search-type indexes. On M0 the cap is 3 indexes of any type, vector indexes included. Flex allows 10. **Verify** the sandbox tier, `db.version()` and the cap at M0.

`store.setup()` creates indexes in this order and stops at the cap, logging every skipped index to `runs.capabilities`:

| # | Index | Type | Collection | Serves |
|---|---|---|---|---|
| 1 | `decisions_vec` | vector (autoEmbed on `title + payload`, or 1024-d client vectors) | `decisions` | L2 neighbours, `naive`/`self_ref` retrieval, `why <term>` |
| 2 | `observations_vec` | vector (client vectors) | `observations` | shape grouping (§ 7.2), novelty read (§ 24.1) |
| 3 | `terms_search` | Atlas Search, `lucene.english`, synonyms mapping from `term_synonyms` | `terms` | term extraction for `hooks.match` (§ 20.3) |
| 4 | `decisions_search` | Atlas Search on `title`, `payload`, hook terms | `decisions` | `$rankFusion` hybrid for `naive` and L2 |
| 5 | `episodes_search` | Atlas Search on question text, `rationale`, `phrasing`; facets on `arm`, `template`, `correct` | `episodes` | viewer search, `$searchMeta` facet counts on the scrubber |
| 6+ | `observations_vec__<embedder_id>` | vector | `observations` | representation arms (§ 24.1) |

Premise: indexes 1–3 fit every tier. False if: the sandbox refuses a third index. In that case, `terms_search` falls back to the in-process extractor (§ 20.3), and `observations_vec` falls back to `numpy`.

### 20.2 Feature map

| Atlas feature | Where it carries Munchhausen | Store / § | Fallback | Milestone |
|---|---|---|---|---|
| `$vectorSearch` with pre-filters | neighbours filtered by `arm`, `lifecycle.status`, `kind`, `run_id`; `naive` top-k | `decisions` § 7.3 L2 | `numpy` cosine | M3 |
| `$vectorSearch` `exact: true` (ENN) | backtest neighbour reads and any store under `EXACT_BELOW` records, so a replay is deterministic | § 7.4 | — | M3 |
| Automated embedding (`autoEmbed`, voyage-4, GA) | `decisions` embed server-side and `$vectorSearch` takes the raw question text, so no client embedding runs on the consultation path of `naive`/`self_ref`. **Verify** that the sandbox offers it and whether the vector is readable back; clustering needs readable vectors, so `observations` keep client vectors unless it is | `decisions` | client Voyage | M2 |
| `$rankFusion` (server ≥ 8.0) | hybrid lexical + vector retrieval for `naive`, and L2 routing; reported against plain vector top-k | § 5, § 7.3 | vector only | M3 if index 4 fits |
| `$scoreFusion` (server ≥ 8.2) | same, with score-weighted fusion; a knob `FUSION=rank|score` | § 5 | `$rankFusion` | post-event |
| Atlas Search synonyms | the term vocabulary compiles into a synonyms collection; question text → terms is one `$search` over `terms` | § 20.3, § 22.4 | in-process extractor | M2 |
| `$searchMeta` facets | scrubber facets (episodes by arm × template × correct) | viewer § 17 | `$group` | M4 |
| Views | floor decisions as tool access (exists, § 8) | `tool_access` | — | M2 |
| Multi-document transactions | admission is atomic: insert successor, flip predecessor, dispose its fires, flip `tool_access`, close the draft | § 7.5, § 8 | ordered writes + idempotent repair on resume | M3 |
| Change streams + resume tokens | the event bus. The episodic pass wakes on `rounds`; `lensfit` wakes on `backtests`; the viewer tails `fires`, `decisions` and `rounds`. Every consumer stores its resume token in `cursors`, so a killed consumer resumes without loss (problem statement 2) | `cursors` | polling every 2 s | M2 |
| Pre- and post-images (`changeStreamPreAndPostImages`) | on `decisions` and `tool_access`, so the viewer shows each lifecycle flip and each view rewire as a before/after diff | viewer § 17 | re-read on event | M4 |
| `$jsonSchema` validators | every store (exists, § 10.1) | all | — | M0 |
| TTL index | `leases`: a worker's claim on an episode index expires after `LEASE_TTL_S`, so in-flight indices re-issue on resume without a scan | § 10.4 | the scan | M2 |
| Time-series collection | `spend`: one row per model call, `metaField: {arm, stage, model}`, fields `tokens_in`, `tokens_out`, `latency_ms`, `usd`. Stage spend is a by-product of every call | new store | plain collection | M2 |
| `$setWindowFields` | rolling stream accuracy, the calibration gap and drift-to-supersede latency, computed in Atlas over `episodes` | `metrics/` § 11 | `numpy` | M4 |
| `$densify` / `$fill` | gap-free curves per arm across rounds | viewer | — | M4 |
| `$merge` (on-demand materialized view) | `rounds` is written by a `$merge` pipeline over `episodes` at each round close, not by Python arithmetic | `rounds` | Python | M3 |
| `$facet` + `$sample` | the backtest's balanced sample: one `$sample` branch over correct episodes and one over misses, in one aggregation | § 7.4 | Python sampling | M3 |
| `$graphLookup` | lineage over `latches.wiring.edges` (exists, § 17) | `decisions` | — | M4 |
| `$lookup` | L0 anchor resolution (§ 10.2); `why` joins | § 7.3 | — | M3 |
| Multikey B-tree index on hook keys | `hooks.match` runs in Atlas: `{"latches.fires_when.terms": {$in: terms}}` plus the collection and persona keys, minus `not_this` rows, over a multikey index (§ 20.3) | `decisions` | Python match | M2 |
| Database-scoped built-in roles | gold isolation enforced by Atlas, not by convention: `world_truth` moves to its own database `truth`. The learner's user holds `readWrite@munchhausen` and `read@world` only; the evaluator's user alone holds `read@truth`; `execute` runs as `read@world` | § 7.4 Don't | the convention | M0 |
| MongoDB MCP Server (`--readOnly`) | the nominator's world query tool is the MCP server in read-only mode, connected as the `read@world` user, not a hand-written tool | § 7.2 | a `find`/`aggregate` tool in Python | M3 |
| Atlas Agent Engine memory (public preview) | two ports (§ 21): `naive` backed by Agent Engine memory (exists as a stretch, § 5); and a **governed mirror** that publishes each admitted decision into Agent Engine procedural or taxonomic memory and withdraws it on supersession, moot or retirement. Any Agent-Engine agent then reads governed memory. **Verify** the Python SDK package and sandbox access | `MemorySink` | null sink | post-event, or M5 if verified at kickoff |
| Atlas Charts (embedded) | optional side pane for the curves; never the main feature | viewer | Chart.js | post-event |

Not used, each with its reason:
- Atlas Triggers / Functions: App Services is at or near end of life; change streams cover the need.
- Atlas Stream Processing: no free tier.
- Online Archive and dedicated Search Nodes: M10+ only.
- Queryable Encryption: no threat in the demo world that it answers.

**Do:** let the demo name each Atlas primitive at the moment it acts: the view at the floor beat, the transaction at admission, the change stream at the fire, `$graphLookup` at `why`.
**Don't:** add an Atlas feature that no beat or reading exercises; an unused feature is upkeep a judge can't see.

### 20.3 Hook matching in Atlas

1. **Term extraction:** `$search` over `terms` with the question text as the query and the `term_synonyms` mapping. Each hit is a term the question presents. The in-process fallback is longest-match over the same `terms` rows.
2. **Match:** one aggregation over `decisions` filtered by `arm` and `lifecycle.status: admitted`. A hook matches when its `fires_when` keys intersect the question's keys and no `not_this` row's keys are all present.
3. **Pack:** the matched decisions are ordered by `rerank-3` relevance and packed to `CONTEXT_BUDGET_TOKENS` (§ 6.2).

The match itself is a query plan Atlas can explain (`explain()` in the viewer's `why`), which makes consultation inspectable down to the index used.

## 21. Seams: ports

Every optional surface sits behind a port: a Python `Protocol` in `munchhausen/ports/`, with implementations registered by name and chosen in `arms.yaml` or by knob. Selections are written to `runs.ports` at run start, and every reading names the ports it ran under.

| Port | Abstracts | Implementations (default first) | Contract |
|---|---|---|---|
| `World` | dataset specifics: adapter, quirk pack, questions, authority | `sample_analytics` + `analytics-v1`; any adapter + pack | `build(db, seed)`, `schema_summary()`, `questions(seed)`, `authority(q, answer, idx)`. The engine imports no adapter module. |
| `Truth` | gold, evaluation only | `pack_gold` | `gold(q, world_version)`. Importable only from `metrics/`, `world/authority` and tests; an import test fails any other importer. |
| `Representation` | embedding vs non-embedding, and its version | `voyage-4`, `voyage-4-lite`, `atlas-autoembed`, `tfidf-online`, `signature`, `none` | `id`, `dim`, `embed(texts, role: observation|decision|query) -> ndarray | None`. Each vector is stamped `rep.embedder_id`. A record holds `emb.<embedder_id>`, so versions coexist and switching versions never re-embeds history in place. `tfidf-online` fits only on rows earlier than the one it embeds. |
| `Similarity` | how neighbours are found | `atlas-vector`, `atlas-exact`, `atlas-hybrid`, `numpy`, `behavioural` | `knn(store, query, k, filter) -> [(id, score)]`. `behavioural` scores two decisions by the share of backtest episodes where both change the answer (§ 24.1 E6). |
| `Grouper` | observations → shapes | `agglomerative`, `atlas-knn-graph`, `tfidf-blocks`, `signature-buckets`, `external` | `group(observations) -> [Shape]`. The coherence guard (§ 7.2) runs on every grouper's output. |
| `Curator` | decision curation: what turns a draft into a decision | `governed` (L0–L5), `ungated` (L0 → admit, over `governed`'s drafts), `naive` (`LessonShape` → admit), `self_ref` (self-grade, `LessonShape` → admit), `hitl` (L0–L4, then owner required) | an ordered list of `Layer`s, each declaring `role: routing|corroborating|dispositive`. A curator with no dispositive layer is reported as ungoverned. |
| `LensPanel` | the corroborating panel | `jev`, `claude`, `ridge-surrogate`, `none` | `score(draft, sources, neighbours) -> {lens: p}`. Reads only the fields its lens entries' `pointer` names (§ 23.2). |
| `Store` | Atlas access | `atlas` | repositories per store, plus `capabilities()`: `vector_search`, `search_indexes_left`, `auto_embed`, `rank_fusion`, `score_fusion`, `change_streams`, `transactions`, `agent_engine`. No module outside `store/` imports `pymongo`, and an import test asserts it. |
| `MemorySink` | the downstream memory product | `null`, `agent_engine` | `publish(decision)`, `withdraw(decision_id, reason)`. Called from the lifecycle functions only. |
| `Trace` | observability | `null`, `jsonl`, `raindrop` | `begin(episode)`, `signal(name, value, comment?)`, `event(name, payload)`, `finish(output)`. Write-only; nothing on the learning path reads it. |
| `SignalSource` | external read-back | `none`, `raindrop` | `shapes(since_idx) -> [Shape]`, handed to the `external` grouper. Corroborating only (§ 25). |
| `Models` | LLM calls | `anthropic` | one function per party (proposer, observer, nominator, `naive` lesson writer, `self_ref` self-grade, planted-map judge); model ids from config. |

Port invariants:
- Every port has an offline or null implementation, so the engine runs with no network beyond Atlas and Anthropic.
- One interface test per port runs every registered implementation against the same fixture.
- Trace invariance: a run under `Trace=raindrop` and the same run under `Trace=null` write byte-identical `decisions`, given the same seeds and model responses (replayed from `spend`'s response cache). False if: a module reads trace state.
- Gold invariance: no implementation of any port except `Truth` reads the `truth` database. The database roles of § 20.2 enforce it.

**Do:** add a dataset by writing an adapter and a pack, and a representation by registering one `Representation`.
**Don't:** branch on a dataset name, an embedder name or `RAINDROP_WRITE_KEY` anywhere outside the port registry.

## 22. The language doc: `corpus/LANGUAGE.md`

`corpus/LANGUAGE.md` is the register of every sentence the system writes and every sentence written about it. It is created at M0 from § 2 and this section. From then on it is the one home of the lexicon, and § 2 is not maintained beside it. The world's term vocabulary is data in Atlas (§ 22.4). The markdown states that vocabulary's rules and never lists its rows.

The doc has the sections below, in this order.

### 22.1 Purpose

It blocks three drifts, each paired with its countermeasure:
- **Term drift:** a hook written in words the question never presents. The countermeasure is the shared vocabulary and the escape (§ 22.4).
- **State narration:** a payload or observation that describes the run instead of the world. The countermeasure is the laws (§ 22.2).
- **Claim drift:** a README or report sentence wider than the reading behind it. The countermeasure is the claim language (§ 22.6).

### 22.2 The three laws

Every directive ships as a Do plus its named overshoot (Don't).
- **L1 Run-invariance.** No payload, hook, observation or lens names a run, an arm, an episode index, a party ("the agent", "I", "we") or a moment ("now", "recently", "this round"). A banned-tells table lists each tell with its legal replacement, and the lint's `TELLS` list is the authority.
- **L2 State-invariance.** Every sentence in a record is a premise (it holds until named evidence falsifies it), a dated fact (it carries `at_idx` or an ISO date), or a directive. Records hold no prose about the past; the ledgers hold the past.
- **L3 Bounded directives.** Every Do carries the overshoot it guards against, named as a recognizable case.

### 22.3 Lexicon

The closed vocabulary of § 2 (term | means | not to be confused with), extended by Part II: `port`, `representation`, `capability`, `amendment`, `moot`, `converged`, `lease`, `mirror`. A term outside the lexicon enters through the escape `other(<what>)` with a definition, then becomes usable.

### 22.4 Term vocabulary (the world register)

The vocabulary hooks key on. It lives in the `terms` collection: `{term, aliases[], source: schema|question|authority|nominator, admitted_at_idx, decision_id?}`. It compiles into the `term_synonyms` mapping that `terms_search` reads (§ 20.3).
- A term is a lower-case noun phrase naming how a question **presents** ("active customers", "fiscal quarter", "revenue"), never a definition ("`st` in {2, 7}") and never a quirk id.
- **Seeding:** from the adapter's schema summary (field and collection names) and noun phrases mined from the first `VOCAB_WARMUP` stream questions. It is never seeded from the pack. A test asserts that no pack id, definition string or transform parameter appears in `terms`.
- **Growth:** the nominator proposes a missing term as `other(<term>): <presentation gloss>` inside a draft. The term is admitted with the draft and refused with it. An authority phrasing that names a concept adds an alias, never a term with a definition.
- **No edits:** a term is never renamed. A better word becomes an alias of the old one.

### 22.5 Voice by surface

| Surface | Voice | Never |
|---|---|---|
| `title` | the constraint, ≤ 12 words, present tense | the deliberation, a figure |
| `payload` | definition or procedure, present tense, names fields and values | a question's answer value, a run fact, hedges |
| hook `fires_when` | lexicon and vocabulary terms in the words a question arrives in | the payload's conclusion |
| `not_this.contrast` | one instantiated case the hook matches and must not bind | bare negation |
| `falsifier`, trigger `when` | an observable event in the stores | a date, a feeling |
| `residue` | what the enforcement does not check, named | "fully enforced" |
| observation `noticed` | 1–3 sentences, present tense, the surface and the gap | a fix, a definition guess |
| lens angle | an open question, reader-addressed, refuting where it adjudicates | first person, an expected answer |
| lens counterfactual | the specific opposite error | "…or was it fine?" |
| authority phrasing (pack-owned) | names the concept, never its definition | the definition |
| README, report | a claim no wider than the reading, with n, interval and population | "always", "proves", an unscoped "learns" |

### 22.6 The authoring register

One register with two faces, kept apart:
- **Latch language** (the key-space face): key on the presentation, bias broad, build from the vocabulary (§ 6.2's Do/Don't, owned here).
- **Consultation language** (the proposer's prompt): presume the store ("apply each consulted decision whose hook matched"), and report count and provenance through `consulted[]`, never a bare assurance.
- **Lens language** (the adjudicator's prompt): counterfactual pairing, refutation phrasing, stipulated certainty for generative lenses.

A form on the wrong side is the failure. A presumed-existence phrasing on a lens manufactures agreement; a refutation phrasing in the proposer's prompt makes it doubt an admitted decision instead of applying it.

### 22.7 Claim language

For the README, the report and the demo voice-over:
- A claim is no wider than its reading.
- Every quantity carries a unit, a population and an n.
- A forecast (§ 11) is printed beside its reading, and a disagreement stands as one.
- Status words (admitted, superseded, moot) are the lifecycle values, never synonyms.

### 22.8 Mechanical checks

`munchhausen/lint_language.py` runs at L0 on every draft and on every observation write:
- the banned tells
- hook terms in vocabulary or escape
- no source figure in the payload
- a non-empty `contrast` on each `not_this` row
- vacuous counterfactual patterns refused in `lenses.yaml` at load

Residue, disclosed: the lint does not check that a payload is true, that a hook is a good net, or that a counterfactual names a real overshoot.

## 23. Writing observations and lenses

This section is the observer's and the lens author's contract. The observer prompt and `lenses.yaml` are compiled from it, and a human writing through the injection control or the owner port follows the same rules.

### 23.1 Observations

The record (amends § 7.1 and § 10.1):

```
{ episode_id,                       # the anchor; required. Chat and memory are no anchor.
  via: observer|owner|injection|anomaly,   # provenance, never a class
  class: reducible|irreducible,     # the noise filter (§ 7.1); the only write-time class
  noticed: str,                     # 1–3 sentences
  surfaces: {terms[], collection, fields[], phrasing},
  answer, figure, ratio, delta, signature_guess?,
  re_check_when?: {terms[], templates[]},  # an observable presentation the shape should recur on; omit if none
  disposition: open|shaped|spent|noise|dropped|moot, disposed_by?,
  rep: {embedder_id}, emb.<embedder_id>[] }
```

Rules:
- **Noticing only.** `noticed` states the surface (the population, the field, the period) and the gap (answer against figure, as a ratio or delta). It never states a fix or a guessed definition. A fix is the nominator's act, after a shape clears the bar.
- **Present tense, reader-addressed, run-invariant** (L1).
- **Write blind.** The observer never reads other observations. Independent observations are what make a cluster evidence. An observation written after reading its neighbours reproduces them.
- **Quote, don't conclude.** The authority's phrasing goes verbatim into `surfaces.phrasing`. `noticed` doesn't restate it as a finding.
- **Classes come from recurrence.** The only class an observation carries at write time is the noise filter's. Shapes are assigned at the episodic pass, never by the observer.
- **One noticing per record.** A miss touching two surfaces writes two observations, never one record that absorbs both.

Examples over the `analytics-v1` world:

| | `noticed` | Why |
|---|---|---|
| Bad | "The agent should exclude customers with `src: k7`." | a fix, and the definition leaks |
| Bad | "Wrong answer on active customers." | no surface, no gap |
| Bad | "We miscounted again this round." | L1 tells, no surface |
| Good | "The count of customers for 2016 exceeds the figure by 3.1%. The pipeline counts every customer document. The phrasing names how active customers are counted." | surface, gap, quoted concept, no fix |
| Good | "The quarterly sum for Q1 2015 differs from the figure by the sum of one calendar month of trades. The pipeline windows Q1 as January to March." | the gap's signature (one period's contribution), no fix |

### 23.2 Lenses

The lens entry format (`lenses.yaml`, mirrored to the `lenses` collection with a version on every change):

```
- id: generalizes
  angle: str                  # the open question, present tense, impersonal
  counterfactual: str         # the specific opposite error the angle steers into
  product: noul|choice|score  # Jev output kind; levels: [...] for choice and score
  pointer: [draft.payload, draft.latches.hook, sources.noticed, neighbours.payload]   # the state fields it reads
  role: routing|corroborating # never dispositive
  consumer: L3                # never the nominator or the proposer
  counterfactual_anchor: draft_id|observation_id|seed   # where the overshoot was observed; `seed` is disclosed as unwarranted
  phrasings: [str, str, str]  # for the hedging read (§ 24.2)
  status: active|folded|reversed|dead|retired
  warrant: [{lensfit_version, delta_logloss, auc_contribution}]   # effect evidence, appended by lensfit
```

Rules:
- **Pair every angle with its counterfactual**, and make the counterfactual name the opposite error, recognizable in an answer. "…or was it fine?" is refused at load.
- **Refute where you adjudicate.** Ask what reading would make the draft false and whether that reading was taken, never whether the draft is right.
- **Never hand the lens its answer.** No expected verdict in the angle; no other lens's score, and no draft `lens_score`, in the state it reads.
- **One proposition per lens.** A lens asking two things folds two signals into one probability, and `lensfit` can't separate them.
- **Externality.** A lens's consumer is the adjudicator, never the party that wrote the draft.
- **Warranted by supply.** A new lens is admitted only with a `counterfactual_anchor` naming an observed overshoot: a draft that L3 scored above threshold and the backtest refused, or the reverse. A lens authored from imagination stays `seed`, and the report says so.
- **Few, clean lenses.** Keep the panel at about five. Do not prune it below five while the judge is weak (§ 24.2 L7).

The seed panel replaces § 7.3's lens table, with corrected counterfactuals. Each counterfactual names an overshoot, never a yes/no question:

| Lens | Angle | Counterfactual |
|---|---|---|
| `generalizes` | Which future questions, beyond the cited sources, does this decision change the answer to? | Name the source question it fits only by coincidence; a decision fitted to its sources answers none beyond them. |
| `case_leak` (negative) | What reading would show the payload encodes one question's answer value rather than a definition? | Name the second question the payload answers correctly; a definition with no second question is an answer sheet. |
| `org_fact` | What reading would show this is one persona's preference rather than an organizational definition? | Name the persona whose question this decision would answer wrongly at org scope. |
| `contradicts_neighbor` | What reading would show this draft and a neighbour can't both hold? | Name the question both hooks match; without one, the contradiction is moot and routing it as supersede is the error. |
| `mechanizable` (Choice: floor / taxonomic / procedural / preference / none) | Is the payload checkable as a `$match` predicate on one collection? | Name the question shape the predicate would wrongly filter. |

**Lens minting** (post-event, the second-order loop's generative half): when `lensfit` reads a stable L3 false positive (above threshold, refused by backtest) on ≥ `LENS_MINT_MIN` drafts sharing a kind, the nominator drafts one lens whose `counterfactual_anchor` is those drafts. The new lens enters `status: active` at weight 0 and earns weight only through `lensfit`.

## 24. Avenues: representations and lenses

Each avenue is a port selection or a knob (§ 21) with the reading that settles it. All of them come from the author's prior project. Rows marked **day** fit inside § 13's milestones; the rest are post-event.

### 24.1 Representation avenues

| ID | Avenue | Arm or knob | Reading | When |
|---|---|---|---|---|
| E1 | Embeddings locate signal but recover identity. On templated text, clusters can track collection and template rather than concept. | `EMBED_MASK=none|surfaces`: embed `noticed` raw vs with collection, field and template tokens masked | ARI between the two partitions; shapes that survive masking | day |
| E2 | On templated questions, TF-IDF blocks recover the templates, and residual signatures carry the concept with no text at all | `Grouper` = `agglomerative`(voyage-4) vs `tfidf-blocks` vs `signature-buckets` | share of shapes clearing `BAR_MIN_TEMPLATES`; quirk recall from `planted_map` | day (signature-buckets is cheap) |
| E3 | Read a partition for stability before trusting it | sweep `CLUSTER_DISTANCE` ∈ {0.25, 0.35, 0.45}, and across `Representation`s | share of shapes persisting across settings (co-association) | post-event |
| E4 | A shape formed from misses is selected on the outcome | pre-nominate direction read over all matched episodes, hits included; **promoted into the bar** (§ 7.2) | miss rate inside vs outside the shape's presentation; refuse a shape with no gap | day (part of the bar) |
| E5 | Miss triage has three kinds: noise, parameter, structure | add `class: parameter` (a constant ratio across all templates: a unit or scale miss) kept off the nominator | share of parameter-class misses; nominator spend saved | post-event |
| E6 | Wording similarity does not predict answer similarity | `Similarity` for L2 = `atlas-vector`+`rerank-3` vs `behavioural` | duplicate and supersede routing agreement with backtest outcomes | post-event |
| E7 | A learned surrogate is cheap where a zero-shot one is not | `LensPanel=ridge-surrogate`: ridge on the draft's embedding predicting the backtest verdict, as a pre-L3 screen | prequential AUC vs `jev` at equal n | post-event |
| E8 | World shift shows as text novelty before it shows as cluster mass | an observation-novelty statistic (mean distance to the prior rounds' cluster centroids), read beside revisit fires | lead in episodes over the first dispositive fire after D1 and D2 | day if `observations_vec` fits |
| E9 | Retrieval's lead lower-bounds what hooks miss | per-question lead of `naive` over `governed` on quirk-bearing questions | the share of misses where `naive` retrieved the right decision and no hook matched | day (a metrics query) |
| E10 | A changed embedder reads as drift | pin `embedder_id` per run; a version change is a new `emb.<id>`, never an overwrite | — (an invariant) | day |

### 24.2 Lens avenues

| ID | Avenue | Arm or knob | Reading | When |
|---|---|---|---|---|
| L1 | A sign-blind dead-lens test can't tell dead from reversed | amend § 9: a lens whose fitted weight's sign is opposite its seed sign over 2 fits is `reversed` (dropped from the panel), distinct from `dead` | count of reversed vs dead lenses | day (in lensfit) |
| L2 | Per-lens weights at n ≈ 20 are coin flips; set-grain readings resolve | report the panel's prequential AUC with its interval as the claim; per-lens weights advisory until the interval clears | a power read for `LENSFIT_MIN_LABELS` | day |
| L3 | Collinear lenses each ablate as worthless | fold on ρ > `LENS_FOLD_RHO` **and** an entailment check by the nominator model; report the effective rank of the lens correlation matrix | effective rank; AUC lost to a fold | post-event |
| L4 | One call answering all lenses shares a wording prior (answer echo) | `LENS_CALL_MODE=isolated|joint`, default `isolated` | inter-lens ρ under each mode, residualized on wording cosine | day |
| L5 | `case_leak` is measured by a held-out stratum, not read from wording | the backtest reports `fixed_heldout`: fixes on templates absent from the sources. Admission needs `fixed_heldout ≥ BACKTEST_MIN_FIXED_HELDOUT` (seed 1) | case-leak drafts refused by held-out vs by the lens | day: a field on `backtests` |
| L6 | Paraphrase agreement does not detect a bad lens; hedging does | log per-lens hedging, mean 4p(1−p), across the 3 phrasings | hedging per lens vs its `lensfit` contribution | day (logging) |
| L7 | Five lenses hold the gain only on clean answers | keep ≥ 5 active lenses; fold only by L3's rule | — | invariant |
| L8 | A seeded start saturates; an empty start widens room | `SEED_DECISIONS=empty|sme`: an SME-written seed set vs empty | drift-to-supersede latency and quirk recall per arm | post-event |
| L9 | Lens-weight trajectories carry no runtime signal at small n | `lens_weights` versions are a log; no reading is claimed from their path | — | invariant |
| L10 | `not_this` is authored only from observed `considered-not-applicable` dispositions | an amendment (§ 10.2) proposes a `not_this` row when a hook collects ≥ `NOT_THIS_MIN` considered-not-applicable dispositions on one key set | hook precision before vs after | post-event |
| L11 | Optimism at admission is misread as later drift | read stale-applied rate (§ 11) only on episodes after `LABEL_HORIZON` from admission | — | invariant |

New knobs, added to § 16: `EXACT_BELOW` 2000, `LEASE_TTL_S` 120, `VOCAB_WARMUP` 40, `EMBED_MASK` none, `LENS_CALL_MODE` isolated, `BACKTEST_MIN_FIXED_HELDOUT` 1, `SEED_DECISIONS` empty, `NOT_THIS_MIN` 3, `LENS_MINT_MIN` 4, `FUSION` rank.

## 25. Raindrop (optional)

Raindrop is a `Trace` and a `SignalSource` (§ 21), off unless `RAINDROP_WRITE_KEY` is set. The engine, the stores and every reading are identical with it off. With it on, the RSI story gets an external observer that grades the harness on signals the harness does not author.

### 25.1 Write path (`Trace=raindrop`, SDK `raindrop-ai`)

| Munchhausen event | Raindrop call | Fields |
|---|---|---|
| episode start | `begin(user_id=persona, event="episode", convo_id=f"{run_id}:{arm}")` | properties: `arm`, `template`, `idx`, `consulted` ids, `view_map` |
| proposer output | `interaction.finish(output=answer)` with the pipeline as a code attachment | `confidence` as a property |
| first-attempt score | `track_signal(name="correct", signal_type="feedback", sentiment=POSITIVE|NEGATIVE)` | — |
| authority reply | `track_signal(name="authority_correction", signal_type="feedback", sentiment=NEGATIVE, comment=phrasing)` | the stakeholder's correction is the analogue of a user's frustration signal |
| floor view applied | `track_signal(name="floor_filtered")` | decision id |
| fire, admission, supersession, moot, retirement | `track_ai(event=<name>, input=draft or fire, output=verdict)` | lens answers and the backtest record as attachments |
| model calls | `tracing_enabled=True` auto-instruments the Anthropic client | spans per party |

Arms become Raindrop experiment variants through the `arm` property, so Raindrop's own experiment view compares `frozen`, `self_ref`, `naive`, `ungated` and `governed` on the same signals.

### 25.2 Read path (`SignalSource=raindrop`, post-event or M5 stretch)

- **Signals:** the Raindrop Query API (read key `RAINDROP_QUERY_KEY`) returns Raindrop's issue clusters over NEGATIVE-signal interactions since an index.
- **Shapes:** each issue becomes a candidate `Shape` handed to the `external` grouper, carrying its member episode ids.
- **Admission:** an external shape passes the same coherence guard, bar, nominator and L0–L4 as an internal one. It is corroborating input only. Raindrop never admits, refuses or fires.
- **Reading:** agreement (ARI) between Raindrop's issues and the internal shapes over the same episodes. This is an outside check on the grouping, which the harness can't author.

**Do:** treat Raindrop as an observer whose groupings the harness must earn admission for, like any other.
**Don't:** let a Raindrop signal settle anything. A dispositive outside signal would make Raindrop the authority, and the backtest is the only authority over admission.

Premise: the RSI prize does not require the read path. False if: the Discord answer at kickoff says the prize needs Raindrop to drive the improvement loop. In that case, § 25.2 moves to M5 and Raindrop leaves the cut order (§ 13).
