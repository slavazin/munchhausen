# Governed Corpus Evolution: A Doctrine for Running a Document Corpus as the Learning System of Frozen-Model Agents

**Slava Zinevich**
*Independent — August 2026*

---

## Abstract

A project assisted by a large language model has a peculiar epistemic
shape: its most capable component — the model — is frozen and rented,
learns nothing between sessions, and holds no memory of the project.
Everything the project *knows* must therefore live in text. This paper
states **Governed Corpus Evolution (GCE)**: a doctrine for running a
typed, versioned document corpus as the persistent learning system of
agents whose generalizer cannot be trained. Four theses organize the
doctrine. First, the three functions that weight training bundles —
storage, generalization, behavior binding — separate under the
frozen-model constraint and are reassigned. Second, the store space
partitions on two axes — decay profile and truth-maker, the live
question whose answer would falsify a record; the truth-maker cuts the
live-hypothesis stores into a **belief store** ("is this still true of
the world?"), a **case store** ("is this still correct?"), and a **duty
store** ("did you actually do it, at every site?"), above a settled
fact-and-trace floor that is the belief store's zero-price limit. Third,
because nothing global remains to carry the learning loop, every
persistent entry carries it locally in a five-slot **entry contract** —
activation, payload, warrant, enforcement split, lifecycle — with fine
structure: the activation slot is a fan of typed latches under a
kind-level port calculus, and a latch grown to the commitment grain is a
checkpoint; a payload's claim granularity is materialized lazily along
three grains — ratification, falsification, retrieval; and the one
designable stage of every read has two surfaces, selection and
composition, composition's unit being the lens — a typed question walked
against an item, filling the corpus's question tier. Where the corpus
faces an exogenous world, its beliefs are run as a governed population: a kind
calculus types what would falsify each claim, calibration runs on two
timescales — structure frozen as pre-registration, judgments scored
out-of-sample — and conditioning variables are admitted only ahead of
the contradictions they would explain. Fourth, the write path is
**governed**: contradiction from structurally independent sources,
unstaked adjudication, refinement damped by recurrence evidence graded
by blast radius, and a human gate on every permanent write — a response
to measurement, since surveyed alternative write policies exhibit
documented collapse, contamination, and self-bias. The doctrine is
distilled from production deployments spanning two payload classes —
process knowledge, truth-made by the project's own execution, and
world-facing domain beliefs settled by an exogenous world, two of them
world-facing corpora run at population scale — and argued as
position and design theory, not as a benchmarked artifact; parts of the
fine structure are design-stage, and the failure-surface section says
which. Among its neighboring families, GCE occupies the position none
claims: the write path constitutionally removed from the model, with the
human as the optimizer.

---

## Contents

- [1. Introduction](#1-introduction)
- [2. The root constraint and the doctrine it forces](#2-the-root-constraint-and-the-doctrine-it-forces)
- [3. Statics: the store space](#3-statics-the-store-space)
  - [3.1 The three functions of training, unbundled](#31-the-three-functions-of-training-unbundled)
  - [3.2 Two partition axes: decay profile and truth-maker](#32-two-partition-axes-decay-profile-and-truth-maker)
  - [3.3 The store roster under both axes](#33-the-store-roster-under-both-axes)
- [4. Reads: two-stage attention](#4-reads-two-stage-attention)
  - [4.1 Selection](#41-selection)
  - [4.2 Composition](#42-composition)
- [5. Writes: event-sourcing and identity](#5-writes-event-sourcing-and-identity)
- [6. The entry contract](#6-the-entry-contract)
- [7. Evolution: the refinement machinery](#7-evolution-the-refinement-machinery)
  - [7.1 Signals, the steer, and the detection matrix](#71-signals-the-steer-and-the-detection-matrix)
  - [7.2 Hypothesis ledgers](#72-hypothesis-ledgers)
  - [7.3 The contradiction-source species](#73-the-contradiction-source-species)
  - [7.4 The slow loop: consolidation as a slot-factored backward pass](#74-the-slow-loop-consolidation-as-a-slot-factored-backward-pass)
  - [7.5 Escape hatches, vocabulary birth, and revision routing](#75-escape-hatches-vocabulary-birth-and-revision-routing)
  - [7.6 The carrier: the fast loop](#76-the-carrier-the-fast-loop)
  - [7.7 The pipeline, worked end-to-end](#77-the-pipeline-worked-end-to-end)
- [8. Grains: the units of ratification, falsification, and retrieval](#8-grains-the-units-of-ratification-falsification-and-retrieval)
- [9. Activation: the latch, the fan, the port calculus](#9-activation-the-latch-the-fan-the-port-calculus)
- [10. The belief store: the corpus's model of the world](#10-the-belief-store-the-corpuss-model-of-the-world)
  - [10.1 The priced claim](#101-the-priced-claim)
  - [10.2 Scoring](#102-scoring)
  - [10.3 Postdiction and transcription — the zero-price limit](#103-postdiction-and-transcription--the-zero-price-limit)
  - [10.4 Falsification pressure — the evidence state](#104-falsification-pressure--the-evidence-state)
  - [10.5 Watch modes and the falsifier's floor](#105-watch-modes-and-the-falsifiers-floor)
  - [10.6 Pre-registered conditioning: the admissibility of a regime](#106-pre-registered-conditioning-the-admissibility-of-a-regime)
- [11. The belief population: kinds, calibration, quantification, audit](#11-the-belief-population-kinds-calibration-quantification-audit)
  - [11.1 The kind calculus: three axes, one selector](#111-the-kind-calculus-three-axes-one-selector)
  - [11.2 The two-timescale calibration regime](#112-the-two-timescale-calibration-regime)
  - [11.3 Quantification is a projection that nominates](#113-quantification-is-a-projection-that-nominates)
  - [11.4 The falsification-surface audit](#114-the-falsification-surface-audit)
- [12. The duty store: propagation machinery](#12-the-duty-store-propagation-machinery)
  - [12.1 Duty conflation](#121-duty-conflation)
  - [12.2 The derivability discriminator](#122-the-derivability-discriminator)
  - [12.3 The adoption register](#123-the-adoption-register)
  - [12.4 Population kinds: spatial, temporal, relational](#124-population-kinds-spatial-temporal-relational)
  - [12.5 Collapse and register, orthogonal](#125-collapse-and-register-orthogonal)
  - [12.6 The question tier](#126-the-question-tier)
- [13. Projections and seams](#13-projections-and-seams)
- [14. One contract, many families](#14-one-contract-many-families)
  - [14.1 The coordinate table](#141-the-coordinate-table)
  - [14.2 Agent families: roles as independence machinery](#142-agent-families-roles-as-independence-machinery)
  - [14.3 Fan-out censuses](#143-fan-out-censuses)
  - [14.4 The episode family](#144-the-episode-family)
  - [14.5 The instantiation law and genesis](#145-the-instantiation-law-and-genesis)
  - [14.6 Importing the doctrine](#146-importing-the-doctrine)
- [15. Lineage](#15-lineage)
- [16. Failure surface and boundary conditions](#16-failure-surface-and-boundary-conditions)
- [17. Discussion](#17-discussion)
- [18. Conclusion](#18-conclusion)
- [References](#references)

---

## 1. Introduction

The practical unit of work with a large language model is the *session*:
a context window is assembled, work happens, the window is destroyed.
The model retains nothing, and, decisively, its weights are not
available for the project to train. The model is *frozen and rented*:
the project owns only the endpoints — what enters context, what leaves
as action, what gets written down.

This is usually treated as a deficiency to patch with a memory feature.
We treat it instead as a design constraint whose correct response is
architectural: the project's document corpus — instructions, decisions,
rules, beliefs, notes, logs — *is* the learning system, and can be run
as one with the rigor learning systems require. We name the discipline
**Governed Corpus Evolution (GCE)**: since evolution proceeds only
through writes, governing every write governs the trajectory.¹

**Thesis.** When the generalizer is frozen, a project's knowledge can be
run as a genuine learning system in text space if and only if the
functions training bundles are unbundled and reassigned (T1) and the
write path is governed (T4); the stores and entries then take the
determinate structure of T2 and T3:

- **T1 (Unbundling).** The three functions weight training bundles —
  storage, generalization, behavior binding — are separated and
  reassigned: storage to a typed corpus, generalization to the model's
  in-context learning at read time *and* human judgment at write time,
  behavior binding to mechanical enforcement plus disclosed residue
  (§ 3).
- **T2 (The store space).** Two axes partition the corpus's stores:
  decay profile, and the truth-maker — the live question whose answer
  would falsify a record — cutting the live-hypothesis stores into a
  **belief store** ("is this still true of the world?"), a **case
  store** ("is this still correct?"), and a **duty store** ("did you
  actually do it, at every site?"), above a settled fact-and-trace floor
  that is the belief store's zero-price limit (§ 3).
- **T3 (The entry contract).** Because nothing global remains to carry
  the learning loop, every persistent unit of knowledge must carry it
  *locally*: when it activates, what it caches, what warrants it, what
  enforces it, how it retires — five slots, one contract (§ 6); the
  apparent diversity of knowledge artifacts is this one contract
  evaluated at different coordinates (§ 14), with fine structure: the
  activation slot is a fan of typed latches (§ 9), and claim granularity
  is materialized lazily along three grains (§ 8).
- **T4 (Governance).** The write path is governed: beliefs are ledgered
  hypotheses exposed to structurally independent contradiction; the
  adjudicator is distinct from proposer and contradictor; refinement is
  damped by recurrence evidence graded by blast radius; a human gates
  every permanent write (§ 7). Not conservatism but a response to
  measurement: every surveyed alternative write policy exhibits
  documented corruption modes (§ 15).

**Contributions.** (i) The corpus's statics: two-axis stores with
price-fillability as the belief store's mechanical membership test,
two-stage reads with two design surfaces — selection and composition —
and event-sourced writes with the identity law (§§ 3–5). (ii) The entry
contract as a unifying derivation, with its invariant set and a named
failure mode per missing slot (§ 6). (iii) The evolution machinery,
traced through one lesson's full lifecycle, with the checkpoint tier and
revision routing — horizontal against vertical, decided by computable
features (§ 7). (iv) The contract's fine structure: the three-grain law
with record leafing and the refinement engine's characterization (§ 8);
the activation slot unbundled into a fan of typed latches under a
kind-level port calculus, with the corrected three-tier activation
vocabulary — hook, latch, checkpoint (§ 9). (v) The belief store's
machinery (§ 10); the belief population's — a kind calculus,
two-timescale calibration, pre-registered conditioning, and the
falsification-surface audit (§ 11); and the duty store's, with the
question tier and the lens (§ 12), under the shared projection and seam
discipline (§ 13). (vi) Instantiation: one contract across artifact
families and agent roles, genesis, and the import law (§ 14). (vii)
Positioning against ten neighboring literatures and an honest failure
surface (§§ 15–16).

**Method and evidentiary status.** A doctrine paper in the position and
systems-design tradition, not an empirical study. Its claims are
distilled from production deployments spanning two payload classes:
**process knowledge** — truth-made by the project's own execution — and
**world-facing domain beliefs** — settled by events the project does not
control, and contributed at population scale by two world-facing corpora
whose claims are run and settled as populations, not single records.
Quantitative results cited are the literature's; the few deployment
measurements retained are observations of single deployments, never
rates. Parts of the fine structure are design-stage — stated as design,
no deployed instrument yet computing them — and § 16 discloses which,
along with the validity limit no deployment escapes: all share
one calibrating human judge (§ 17 states the corresponding open
experiment).

GCE sits at the intersection of ten neighboring literatures; the
divergences concentrate on one question — who writes, under what
governance. § 15 gives the lineage and the negative results no located
prior art states.

¹ The name admits two bindings — governed *corpus* evolution (what
persists between sessions) and governed *context* evolution (what is
assembled per session). We write "corpus": the persistent store is the
thing that evolves; each session's context is a projection of it (§ 4).
The constructs are identical.

## 2. The root constraint and the doctrine it forces

**The model's weights are not ours to change.** The map is rented; only
the endpoints are owned (§ 1). Five doctrine positions follow, each
turned from limitation to advantage:

1. **Own the endpoints; treat the model as a fixed oracle.** No learned
   routing, auto-judged applicability, or tuned embedder in the
   retrieval path: legible symbolic keys transfer under novelty and
   survive a model swap; a latent index does neither.
2. **Cache judgment in legible text, never in weights.** Text can be
   diffed, attributed, audited, rolled back; reversibility and
   attribution are non-negotiable on a rented substrate.
3. **Amortize the human's judgment, not the model's inference.** Each
   hard question surfaces once, at a scheduled checkpoint; its answer
   crystallizes into a store with a lifecycle.
4. **Place every judgment on the deepest available key** — the duty as
   narrow as is true, the consultation hook as broad as is predictive
   (§ 9 gives the vocabulary); placement sets steering leverage and
   drift exposure on the same axis.
5. **Behavioral feedback is forced, not chosen.** Activations and
   embeddings are invisible; behavior is the only channel — *acted-upon*
   beats *technically-correct*, and catch-rate is never a target. Within
   the channel one signal is sovereign: the human's correction — the
   **steer** — is the sole durable *reward*; its capture machinery is
   therefore a first-class, independently tunable component (§ 7).

The species differentiator against the self-evolving-context field
(§ 15) is **governance**, and one asymmetry shapes everything
downstream: **promotion is owner-performed — always.** The agent is
excluded because self-performed promotion is self-referential — the
context that emitted a hypothesis would be ratifying it (§ 15); the
world because it can only contradict — outcomes ground claims but do not
decide the lesson. In borrowed training vocabulary — words, never
mechanism (§ 17) — sessions are the forward pass, the world the loss
signal, agents compute *proposed* updates with evidence attached, and
**the human is the optimizer step**: one deliberate, low-frequency
backward pass that alone applies updates. The throughput bottleneck is
accepted — it is the point — and is why proposals arrive self-contained,
all five slots filled (§ 6), so each judgment surfaces once, cheaply,
while it can still change the outcome.

These positions are the doctrine's trunk, developed at three altitudes:
the statics of a governed corpus (§§ 3–6), the machinery and fine
structure of its evolution (§§ 7–13), and its instantiation across the
artifacts and agents of a working project (§ 14).

## 3. Statics: the store space

### 3.1 The three functions of training, unbundled

Weight training bundles three separable functions; GCE unbundles them, and
the unbundling is where every borrowed training word both fits and breaks:

1. **Storage** lives in the corpus — reversible, attributable,
   live-next-session with zero retraining, and stronger than fine-tuning
   for factual and procedural content (Ovadia et al., 2024).
2. **Generalization** splits in two: *outsourced to the frozen model's
   in-context learning at read time* — the corpus curates, the model
   generalizes — and *performed by human judgment at write time*, in
   promotion's abstraction step: restating an instance object-decoupled,
   at transferable altitude, before it moves up a tier. Load-bearing,
   not stylistic: stored raw instances produce negative transfer that
   flips positive when stored as abstracted insights (*When Continual
   Learning Moves to Memory*, 2026). Promotion that copies instead of
   abstracting builds a recall cache, not a learning system.
3. **Behavior binding** is every context system's weakest link — a rule
   acts only if retrieved AND applied. GCE binds mechanically where
   bindable and directs attention to the rest by disclosure: every rule
   states what its enforcement does *not* check — the **enforcement
   split**, floor plus disclosed residue. The field mostly hopes.

### 3.2 Two partition axes: decay profile and truth-maker

The corpus is not one pile; it is partitioned twice.

The first axis is **decay profile**. Different knowledge rots at
different rates, is recalled at different moments, and fails differently
— so it belongs in stores with different recall modes, capacity
policies, and forgetting mechanisms. This is the separation law
(invariant I1, § 6): **one store per decay profile; never one
governance.** Its support is measured: heterogeneous memories sharing
one retrieval space contaminate each other, and explicit typing at write
time restores reliability (Ha et al., 2026).

The second axis is the **truth-maker**: the live question whose answer
would falsify a record. It cuts the live-hypothesis stores into three:

| Store | Live question | Contradicted by | Dominant machinery |
|---|---|---|---|
| **Belief store** | Is this still true of the world? | the world: exogenous events, settled outcomes | Falsification machinery: frozen claims, watches, evidence state, skill scoring (§ 10) |
| **Case store** | Is this still correct? | currency: a premise reversing, a constraint dissolving | The warrant and the revisit list: falsification-list warrants, revisit triggers, supersedure |
| **Duty store** | Did you actually do it, at every site? | the estate: the corpus and codebase observing its own uptake — non-propagation made visible | The adoption register: per-site triage, carry reasons, gap cells (§ 12) |

The middle column is chosen carefully. Only the belief store's
contradictor is the world; the duty store is contradicted by *the
estate* — the site population under the corpus's own governance. That
structural asymmetry makes the trichotomy a **nested dichotomy**: first
cut, world-facing versus internal; second cut, within the internal half,
correctness versus propagation. So stated, two later failure classes are
*different modality errors*: duty conflation (§ 12) is intra-internal,
while mixing lifecycle status into world-pressure state (§ 10) is a
world/internal conflation — a flat three-way table leaves those
undistinguished.

The nesting also yields a mechanical membership test. The belief store's
pricing machinery (§ 10) requires a declared, independent reference
frozen at entry; internal records have none — they have internal
economies (ratification cost; the standing tax the route-before-mint
ladder prices at admission, § 7), governed by bars and caps, not
references. So:

> **A record belongs to the belief store iff its entry-price slot is
> fillable — iff its truth-maker admits an independent reference that
> can be frozen at entry.** A record whose price cannot be filled from
> outside the corpus is internal.

Two load-bearing disambiguations. First, this is *not* the
episodic/semantic/procedural cut: that trichotomy partitions by content
type and cognitive origin; this one by what would falsify the record —
the axes cross. Second, the truth-maker axis does not replace the decay
axis: decay profile still separates stores within a leg (§ 5). The
second axis assigns each store its *dominant machinery*: the table's
fourth column derives from its second. (§ 6 sharpens the point: the axis
selects which of an entry's slots grows largest.)

**The floor beneath the legs.** The trichotomy partitions the
*live-hypothesis* stores; two organs carry no live question at all — the
typed fact layer (settled measurements, as-of-stamped) and the trace
store (session logs). Nothing falsifies a fact record except
transcription error. Under the pricing frame these are a derivation, not
an exception: **a fact is a belief whose price is identically zero** —
it never bore epistemic risk in the corpus's custody, which is exactly
why facts are transcribed and never adjudicated (§ 10 derives the same
boundary from the write side). The fact layer is the belief store's
price-zero floor, and the trace is born there. One seam, stated once,
holding up all three legs.

The axis has an external warrant: applying AGM belief revision to
*norms* required rebuilding the revision operator on a different logic
altogether (Alchourrón & Makinson, 1981) — belief-revision and
norm-revision machinery cannot share one operator. The deeper root is
the deontic/alethic modality distinction — belief records truth-apt and
world-falsifiable; duty records obligation-apt, *violated* by an agent
rather than falsified by the world (McNamara & Van De Putte, SEP).

### 3.3 The store roster under both axes

A roster is an output, not an input: an adopting project grows its own
(§ 14). One deployed corpus stabilized on six store classes — the roster
below is offered as observed, the two-axis reconciliation as derived,
the separation law as the claim:

| Store class | Truth-maker position | Holds | Recall mode | Forgetting |
|---|---|---|---|---|
| Constitutional | Duty leg — its hard-capped, always-loaded apex | The always-loaded rule tier | Loaded every session | **Hard cap with forced eviction** — the system's only fixed-width layer |
| Rule | Duty leg — the duty store proper | Recurring conditional duties (condition → duty) | Routed associatively by declared work-shape | Demotion review; probation; tombstones |
| Case | Case leg | Settled point decisions that constrain the future | Full scan of one-line summaries + native matching | Status flip (superseded / moot); never deleted |
| Belief | Belief leg (a pre-admission draft tier below eternal claims) | Priced claims, watches, evidence states over an exogenous world | Revisit-trigger-fired + a dedicated status projection | Settlement: verdicts retire claims to the fact floor; deadlines and kill criteria |
| Episodic | Pre-admission stratum of all three legs | Not-yet-evidence: observations, felt friction, typed defect records | Trigger-fired + periodic passes | The only delete-with-pointer piles — promotion or obsolescence empties them |
| Procedural | Enforcement surface of duty floors — not a hypothesis store | Gates, skills, generators | Mechanical execution; progressive disclosure | Retirement on supersession |
| Trace | The settled floor, with the typed fact layer | Session logs — the event record | Header at boot; projections on demand | None — everything else regenerates from it |

Three placements, a sentence each. The constitutional tier is not a
fourth leg but the duty leg's apex — duties too load-bearing to trust to
routing, paid for under a hard cap. Procedural artifacts are enforcement
surfaces, not hypothesis stores: the duty record, not the gate, carries
the live question. The episodic pile is not a leg but a stratum: a
noticing may mature into a belief claim, a case, or a duty, and until
admission belongs to no leg (§ 5 states the identity consequence).

One absence in the roster is disclosed rather than patched: it names no
store class for schema and registry artifacts — the axis registries and
port declarations through which later sections gate their vocabularies
(§§ 9, 11) — which are neither hypothesis stores nor procedures; the
account of that surface is owed (§ 17). The activation calculus those
registries serve is, by contrast, store-general — one calculus, every
leg (§ 9).

The constitutional tier's hard cap is the most frequently resisted rule
in practice: the always-loaded tier is hard-capped on both item count
and total mass, and adding a rule means evicting one. Soft budgets fail
— a deployment scar and the practice literature's convergent warning
(context rot; Hong, Troynikov & Huber, 2025). Exactly one fixed-width
layer exists, and the cap forces the ranking conversation a growing pile
silently avoids.

## 4. Reads: two-stage attention

Every read surface in the system is one pattern: **a mechanical,
legible, hard pre-attention stage assembles what enters context, and the
model's native attention does the conditioning.** All design content
lives in stage one, the only stage that is ours — and stage one has two
design surfaces: which stored items enter context, and what authored
text accompanies them. The two surfaces share stage one's defining
property — no gradient will ever repair either — and differ in their
failure modes; they are taken in turn.

### 4.1 Selection

**Selection** is the routing surface: routing vocabularies, trigger
predicates, per-document section maps, progressive disclosure. Which
stage owns which selection tracks three variables: corpus size ×
per-item token weight × miss cost. Heavy, numerous, high-miss-cost
entries (the rule store) get routed activation with declared firing
shapes; cheap one-line summaries (the case store) get bare full-scan;
heavy documents get section maps and partial reads; procedures get
name-and-description tiers with bodies on demand. The placement
heuristic: **move selection into stage one only when items are too heavy
to scan; keep stage-one keys legible, because there is no gradient with
which to repair an illegible key space** — a latent or opaque key fails
silently and forever, so keys stay symbolic: words a human can read,
audit, and rewrite.

Two external facts triangulate the design: the tool industry, under
competition, independently converged on the same taxonomy (§ 15); and
retrieval method dominates write-time sophistication in measured
accuracy spread (Yuan, Su & Yao, 2026) — locating the leverage exactly
where this section spends it.

Read whole, the two-stage surface is the corpus's **associative
memory**. A frozen model retains no association between this project's
situations and its knowledge; the corpus rebuilds that faculty outside
the weights, as cued recognition over legible keys. Progressive
disclosure makes the faculty affordable: every store leads with the
cheapest cue that can carry recognition and defers its mass until the
cue fires (the read-side activation machinery is worked through in §§ 7
and 9).

### 4.2 Composition

Selection decides what the model conditions on; it does not exhaust what
stage one contributes to the conditioning. Alongside every selected item
travels authored text — a question, a schema, a principle, a directive's
wording — and that text is a design surface in its own right, with its
own leverage and its own discipline. The evidence for the leverage is
controlled, not anecdotal. Hold the model, the retrieval, and the
selected context fixed, and vary only the authored question that
accompanies them: a refinement loop whose critique prompt is
*actionable* rather than generic moves a task from 31.2 to 43.2, and
with no critique the same loop scores zero (Madaan et al., 2023 — the
feedback ablation); one added abstraction question — "what principles
govern this problem?" — moves knowledge-heavy benchmarks by double
digits (Zheng et al., 2023); a three-step harm-enumeration schema cuts
measured harmfulness by up to a third (Kim et al., 2025). The same
experiment run on humans forty years earlier found the same result: an
instruction to *consider the opposite* corrected judgment bias where the
demand-laden "be as fair and unbiased as possible" did not (Lord, Lepper
& Preston, 1984). None of these interventions changes what enters
context or reaches into the forward pass; every one adds authored
conditioning text beside the selected material.

> **The composition law.** Stage one has two design surfaces:
> **selection** — which stored items enter context — and
> **composition** — the authored conditioning text that accompanies
> them. The lens is composition's unit: a versioned artifact with an
> effect claim, governed like a routing key, priced per model, and
> repaired only by rewriting — there is no gradient here either.

**Composition** shares selection's constitution — legible, auditable,
rewritable, because no gradient will ever repair it — and adds one
property selection lacks, which the doctrine carries as a warning:
composition is *unstably* powerful. Meaning-preserving reformatting
alone is measured to move task accuracy by tens of points (Sclar et al.,
2024), and the sensitivity cuts both ways — what makes a well-worded
piece of conditioning effective makes an idly reworded one a silent
regression. A piece of composition is therefore never prose: it carries
an identity and an effect claim, and its repair is a governed rewrite.
The lens — a typed question walked against an item — is the surface's
unit, developed with the question tier (§ 12.6); composition's
store-derived, index-level instance appears with the projection
discipline (§ 13).

Composition's wording is governed by an **authoring register** — one
register with two faces, one per stage-one surface. The key-space face
governs the recognition conditions selection fires on (§ 9 gives their
calculus): key on the *presentation* — what the consumer holds before
the payload has helped — never on the conclusion; bias broad, because
the costs are asymmetric — a false fire costs one disposition and
doubles as narrowing telemetry, while a miss is a structural zero,
invisible until paid for; and build conditions from the shared lexicon
only, because a term minted ad hoc inside one condition is an assumption
smuggled across the session gap. The composition face governs the
conditioning text itself and partitions its wording forms by the duty
class the text serves (§ 7.4 derives the classes): count-and-provenance
and presumed-existence forms belong to consultation — text exercising
the corpus's cached judgment; refutation phrasing, stipulated certainty,
and the counterfactual belong to the lens side, where judgment is
elicited rather than replayed (§ 12.6). Deployed corpora reached the
register from the writing side — wording rules preferring certainty over
possibility, instruction over exhortation, cue–action binding, the count
as the response (a pointer no answer can fabricate without reading the
item) — before the surface carrying them had a name.

The statics so far cover how knowledge is partitioned and read. What
remains is the write side — where the corpus acquires its graph.

## 5. Writes: event-sourcing and identity

Writes are event-sourced. Single canonical source; every index a
regenerated projection; IDs reserve-once, immutable, gap-tolerant;
retirements tombstone with successor pointers; refinement is a new record
or a status flip, never a rewrite of evidence. A hand-maintained parallel
surface is drift by construction. The precedents are exact: RFC
immutability with `Updates:`/`Obsoletes:` pointers (Bradner, 1996) and
ADR practice's never-reuse-numbers discipline (Nygard, 2011).

The identity law is also where the corpus acquires its graph. Immutable
IDs make records stable vertices; every typed pointer between records is
an edge that cannot dangle by renaming — stable enough to build law on.
The successor pointer is the first edge type: successor edges compose
into the **lineage DAG** — a DAG and not a chain, because refinement
merges as well as branches (one successor with two predecessors, one
retiree with several heirs; § 7.4 names the operators) — and "the
history of being wrong" (§ 7.2) is read off it as a path query. Later
sections lean on this one typed graph repeatedly: the fold is an edge
contraction (§ 7.4), retrieval structure a bipartite incidence (§ 8),
the wiring fan its maintenance layer (§ 9), the relational duty kind its
completeness law (§ 12.4).

Two write-surface shapes recur throughout, their vocabulary fixed here
as law: a **register** is a hand-authored statement of current state,
corrected in place; a **ledger** is an append-only history, never
edited. The distinction is load-bearing — a current state maintained as
history rots into archaeology; a history amended in place stops being
evidence.

The projection rule carries an admission converse — a hand-authored
register is warranted exactly where its load-bearing relation is
un-derivable — a clause of invariant I3 (§ 6), developed in § 12.

The identity law — reserve-once, immutable, gap-tolerant — has a lower
boundary, found from below in deployment when an intake pipeline minted
permanent identifiers *before* admission — admission and identity
conflated. The remedy is the **pre-admission tier**: a record class
below the eternal store in which **eternal identity attaches at
admission, not at intake**. Membership is a two-part test: (a)
referenced by no eternal record; (b) named in no append-only ledger —
jointly, in graph terms: no in-edge from the eternal graph. That reading
makes the tier's exit rule a derivation rather than a dispensation:
removing a vertex with no in-edges breaks no path, so no tombstone is
needed — a draft nothing references has nobody to resurrect it *from*.
The tier derives the identity law's purpose rather than carving an
exception: ID immutability exists to prevent dangling references and
protect the history of being wrong; a never-admitted draft generates
neither. Records-management law has run the same boundary for decades
(the U.S. federal working-files rule; NARA, 36 CFR § 1222.12).

Inside the tier, the recommended mechanical form is the **name/UID
split**: pair every tier record with a non-recycled internal UID and let
the human-facing draft number recycle as a momentary name (the
Kubernetes name/UID move; Kubernetes documentation, *Object Names and
IDs*) — converting the guarantee from procedural to mechanical. Cost
asymmetry remains the fallback defense where the companion UID is not
built.

Two lessons generalize beyond the tier. **Never encode tier, status, or
any revisable slot in an identifier** — promotion breaks the ID (the
cool-URIs lesson, § 8). And the admission *event* gets the same
governance as any write: accept mints the eternal ID and stamps
provenance from the draft's frozen date (§ 10); decline drops the draft;
either way the adjudication appends to the owning ledger.

## 6. The entry contract

This section derives what every entry in any store must carry — the
doctrine's central claim.

In a weight-trained system, five functions are *global* properties of
the training loop: attention learns when knowledge activates; the loss
warrants it; the weights bind it; continued training refines and retires
it. The root constraint removes the optimizer — nothing global will ever
activate, warrant, bind, or retire a piece of cached judgment. Therefore
**every persistent entry must locally self-carry the whole learning
loop, in legible text** — one five-slot contract, the **entry
contract**, informally the *pentad*:

1. **Activation** — when does this enter context, or fire?
2. **Payload** — the cached judgment, at transferable altitude.
3. **Warrant** — what grounds it as correct: anchors, truth-maker,
   adjudication — causally independent of the entry itself.
4. **Enforcement split** — the mechanical floor plus the disclosed
   residue.
5. **Lifecycle** — the named consumer plus the retirement leg.

The contract also has a derivation from above — from the corpus-wide
commitments of §§ 2–5, stated here as an explicit invariant set (the
last four anticipate § 7's machinery):

- **I1** — One store per decay profile; never one governance.
- **I2** — Writes are human-gated: the machine enumerates, proposes, and
  audits — it never authors.
- **I3** — Single canonical source; every index a regenerated projection;
  immutable IDs with tombstones. A verifier's independence from its
  subject is causal, not spatial. A hand-authored register is warranted
  iff its load-bearing relation is un-derivable — derivable structures
  are projections, regenerated or materialized-and-gated (§ 12) — and
  eternal identity attaches at admission, not intake (§ 5). Derivation
  presupposes resolvability: an entry is derived only where its consumer
  can resolve the pointer; where the read boundary is hard — a
  dispatched context that sees nothing outside itself — verbatim
  carriage under a single owning dispatcher, with a coherence gate on
  the copy, is the correct shape, because there the pointer, not the
  copy, is the drift.
- **I4** — Progressive disclosure everywhere; stage-one keys stay legible.
- **I5** — No record without a standing consumer.
- **I6** — Promotion must raise abstraction, never tier-copy an instance.
- **I7** — Every entry threshold pairs with a retirement leg: counts
  nominate, competence decides, killer-items are exempt regardless of
  count.
- **I8** — The always-loaded tier carries a hard cap with forced eviction;
  exactly one fixed-width layer exists.
- **I9** — Feedback is behavioral only; catch-rate is never a target.
- **I10** — Every rule, gate, and checkpoint discloses what its
  enforcement does not check.
- **I11** — Noise-filter the error stream before updating process:
  reducible failures update authoring; irreducible ones update detection.
- **I12** — External signals outrank self-graded ones; self-graded labels
  never drive permanent structure alone.
- **I13** — Every held belief is a marked, anchored hypothesis; suspected
  and verified never mix registers.
- **I14** — Every belief class that matters has a structurally independent
  contradiction source, adjudicated by a party distinct from both proposer
  and contradictor.
- **I15** — Contradictions land append-only in the domain that held the
  failed belief: one owning ledger per domain.
- **I16** — The instruments are instrumented: attacker precision tracked,
  misses recorded, vocabularies blind-coded, floors honest about
  observed ≠ occurrence.

The pentad is the **per-entry projection of this set**: activation is
I4/I8's per-entry face; payload I6's; warrant I3/I12–I14's; the
enforcement split I10's; lifecycle I5/I7's. Necessity follows from the
removed-optimizer derivation. Sufficiency — are five slots *enough*? —
is held as an empirical claim: across observed organ births in
deployment none has needed a sixth slot; the claim stays open in the
posture § 17 prescribes, and it survives only together with one
disclosed debt — the store roster of § 3.3 names no store class for the
schema registries that carry § 9's port declarations, an account owed
and carried open (§ 17).

Three properties make the contract more than a checklist. First, it is a
*derivation*, not a convention: in deployment, organs kept being born
five-slot-shaped with nobody mandating it. Second, **slot fillings are
coordinates, not choices**: artifact families differ because each
evaluates the contract at its own position on axes the doctrine owns —
recall economics, truth-maker, bindability, decay profile, moment in the
loop — worked family by family in § 14. Third, **each missing slot names
a known failure mode**: no activation → the **structural zero** — in
the corpus graph (§ 5), a record no activation edge reaches:
unreachable, therefore unretrievable, stored but never recalled — the
new forgetting; no independent warrant → the **floating entry** —
nothing external grounds it, so it reads as whatever the surrounding
context suggests — with the self-warranting verifier (§ 7.2), whose
warrant loops back to its own author, as the circular worst case; no
floor disclosure → complacency about what enforcement does not check;
no lifecycle consumer → the graveyard, or entry-without-retirement;
payload un-abstracted → the recall cache.
An organ proposal missing a slot names its own failure row — turning
"design a new knowledge artifact" into "fill five slots and defend
each."

The contract carries one cross-slot regularity the invariants build
severally without naming. The **not-this clause** on the activation slot
declares the router's exclusions (§ 14.1); the **falsification list** on
the warrant states the constraining facts as what would refute them; the
disclosed residue is I10 on the enforcement slot; the retirement leg is
I7 on lifecycle; the escape is every closed vocabulary's off-map channel
(§ 7.5). One law generates all of them, and completes the set with a
member the payload slot was owed:

> **The complement law.** Every declared positive carries its declared
> negative — the specific opposite failure, the refuting fact, the
> unchecked remainder, the exit condition, the off-map channel —
> because a frozen generalizer interpolates beyond any unbounded
> pointer, and the negative is what makes a declaration a region
> instead of a ray.

| Slot | Complement member |
|---|---|
| Activation | the not-this clause — the router's declared exclusions (§ 14.1) |
| Payload | the **counterfactual** — the directive's named overshoot (below) |
| Warrant | the falsification list — constraining facts as what would refute them |
| Enforcement | the disclosed residue (I10) |
| Lifecycle | the retirement leg (I7) |
| Every closed vocabulary | the escape (§ 7.5) |

The payload's member repays its mechanism, because the plausible
misreading — tell the model what not to do — is measurably the *wrong*
lesson: frozen models handle bare negation badly, insensitively at small
scale and unstably at large (Ettinger, 2020; Truong et al., 2023), and
humans under thought suppression rebound into the suppressed content,
the remedy in that literature being a single named replacement thought,
not better suppression (Wang, Hagger & Chatzisarantis, 2020). The
effective negative is a **contrast** — a concrete, plausible,
instantiated alternative failure — and four independent fields converge
on instantiation as the active ingredient: consider-the-opposite beats
be-fair-and-unbiased (Lord, Lepper & Preston, 1984), with the moderator
the plausibility of the instantiated alternative, not its oppositeness
(Hirt & Markman, 1995); contrastive reasoning demonstrations built by
minimal plausible perturbation of a valid chain — one believable error,
not incoherence — lift frozen-model reasoning across every tested
benchmark (Chia et al., 2023); actionable critique beats generic
critique beats none, 43.2 over 31.2 over 0 (Madaan et al., 2023);
thought substitution beats suppression. Stipulated certainty sharpens
the form further: the prospective-hindsight factorial isolates
*certainty*, not temporal framing, as the active ingredient — outcomes
stipulated as certain drew longer, more specific explanations, with the
temporal frame near-inert (Mitchell, Russo & Pennington, 1989; the
study measured the quantity and character of reasons, never their
correctness — the popularized thirty-percent-accuracy reading of the
premortem overstates its base). A directive alone names a direction and
lets the generalizer run along it; drift under a bare directive is
over-compliance toward the nearest attractor, and the named overshoot
is that attractor, given coordinates.

> **The contrast law.** The effective counterfactual is a concrete,
> plausible, instantiated alternative failure, asserted with stipulated
> certainty — contrast, never bare negation. A directive alone is a
> vector; the pair is a segment.

One honest gap travels with the law: no located controlled experiment
isolates prohibitive against contrastive instruction phrasing in frozen
models; the mechanism is quadruply convergent, the specific comparison
unrun. The counterfactual's known degeneration — "don't overdo it,"
which bounds nothing — is closed by evidence, not style:

> **A counterfactual is warranted by supply: it is non-vacuous exactly
> when it traces to an observed instance — a ledgered defect, a caught
> over-claim, a steer.** Authoring a counterfactual from imagination is
> priming (§ 7.5); authoring it from the miss stream is consolidation.
> The pair is an evidence obligation wearing a style rule's clothes.

The wording forms that carry the pair live in the authoring register's
lens-side face (§ 4.2). And one boundary keeps the family honest: the
in-artifact pair is micro-adversarial — adversarial *direction* folded
into authoring — and cannot substitute for an independent contradiction
source, because the same context reads both halves, so there is no
structural independence (I14); in deployment, the corpus whose pairs
are sharpest had its question machinery's own defects caught not by its
counterfactuals but by an independent reviewer. Two instruments, two
moments: the pair bounds the reader's interpretation; the examiner of
§ 7.3's attack species attacks the author's claims. A corpus that lets
cheap pairing erode its examiner budget has traded its contradiction
source for a style.

Two slots repay closer examination: the activation slot is a fan of
typed latches (§ 9 unbundles it), and the payload slot leaves open where
an entry's internal claim boundaries lie (§ 8 answers it). Both
examinations presuppose a system that already knows when an entry is
wrong — and nothing in the statics supplies that knowledge.

## 7. Evolution: the refinement machinery

The statics store and recall knowledge; this section is how the system
*finds out it is wrong* — the evolution in the name.

### 7.1 Signals, the steer, and the detection matrix

Four signal classes, deliberately not conflated: **the steer** — the
human's correction, an n=1 supervised specification edit that also
performs credit assignment, deciding *which artifact* absorbs the
lesson; **the world** — failing tests, live behavior, incidents, gate
fires: it grounds claims and rewards nothing; **recurrence counters** —
the accumulator: nothing structural updates on one instance (§ 7.4); and
**self-noticed signal** — lowest trust, since self-refinement amplifies
self-bias (Xu et al., 2024), so self-graded labels never drive permanent
structure alone.

The taxonomy is not flat: **the steer is the sole durable reward
channel; everything else is evidence or bookkeeping.** The world can
falsify a belief but cannot say what the lesson is worth; counters
nominate but never decide. Since every unit of value enters through a
steer, **steer capture is an independent, first-class design concern**:
typed steer records written at the moment of correction, before the
context that understood it is destroyed; a classification vocabulary
over steer kinds grown by § 7.5's staged discipline; the close's
scheduled steer moment (§ 7.6). Capture is itself instrumented and
tunable (I16). One polarity guards the concept: maximize *yield per
steer*, never steer *count* — soliciting corrections manufactures reward
(I9), and in a healthy system steers become rarer.

Where do steers come from? Every catch-or-miss event falls in a
two-by-two — the system's own apparatus against the human:

| | Human catches | Human does not catch |
|---|---|---|
| **System catches** | **Redundant catch.** The mechanical catch made the steer unnecessary — confirmation that a minted duty now fires on its own, and *demotion-side* evidence: mass here nominates coverage migration | **The amortization working.** Zero marginal human cost; the majority cell by design, and the cell to which a healthy system migrates its mass |
| **System misses** | **The steer.** Reward and credit assignment in one — and simultaneously a miss report against the system itself: every steer carries a second, free payload ("why didn't the apparatus fire?") that feeds the slot analysis of § 7.4 | **The true miss** — the hardest class. Invisible until the world votes; reaches the system only through the reality species (§ 7.3) as a defect, and is repaired *backwards in time*: a judgment-performed backtrace from the manifested harm to the belief that failed, with direction-paired archaeology closing the causal ambiguity. Counts here are floors, permanently (I16) |

The matrix is the health trajectory made legible: maturation is mass
migrating from the steer cell into the system-catches cells — and the
steer's scarcity argument in one picture: the bottom-left cell is the
only durable reward source and each of its events is unrepeatable.

### 7.2 Hypothesis ledgers

Every consequential belief committed to text is a hypothesis with an
anchor, never a bare assertion (I13). A **hypothesis ledger** is a typed
disagreement store — the five-slot tuple:

> **⟨ claim · contradiction source · adjudicator · verdict vocabulary ·
> consolidation consumer ⟩**

The claim is frozen verbatim with its anchors: contradiction against a
drifted paraphrase is contradiction against a strawman. The
contradiction source is structurally independent — independence causal,
not spatial: the source must be load-bearing for something other than
this measurement. The adjudicator is distinct from both proposer and
contradictor. The verdict vocabulary is closed with an honest escape
(§ 7.5). The consumer is the named periodic pass reading recurrence and
routing it — a ledger with no consumer is a graveyard (I5). Records are
append-only under immutable IDs; the system's history of being wrong is
its most valuable training corpus. The ancestor is the TMS belief node
(Doyle, 1979); the difference, the inserted judgment seam between
contradiction and retraction (§ 15).

The tuple encodes a constitutional principle: **proposer, contradictor,
adjudicator, and committer are distinct parties**, each collapse of two
roles a named failure. Proposer = contradictor → no contradiction is
ever generated: hypotheses survive their author's scrutiny by default.
Contradictor = adjudicator → the attacker grades its own attack; every
contradiction is "confirmed". Proposer = adjudicator → the
*self-warranting verifier*: the disagreeing party decides the
disagreement (a test author whose test unexpectedly fails must
quarantine and report, not rule on it). Adjudicator = committer,
unattended → the ungoverned auto-write loop, with the field's measured
collapse and self-bias (§ 15). The human gate on permanent writes is the
last, non-collapsible seam — and, after the poisoning results (§ 15), a
security control as much as an epistemic one.

The ledger audits itself (I16): attacker precision is a tracked ratio,
persistently-zero findings interrogating the *dispatch bar* before
targets are declared clean; the attacker's misses get records — a
retroactive should-have-been-caught-by stream; the ledger's own class
labels are staged hypotheses, blind-coded at consolidation (§ 7.5); a
new ledger is born with record grammar, verdict vocabulary, and named
consumer stated (§ 14.5). One known instrument limit — the
absorbed-feedback ceiling artifact, where attacker precision cannot
measure itself — is disclosed in § 16.

### 7.3 The contradiction-source species

A boundary first: **the doctrine necessitates the family, not the
roster.** Ledgers differ by where their contradiction comes from; one
deployed corpus stabilized at six **species** — an observed taxonomy and
a menu, each independently adoptable, none individually required:

| Species | Contradiction source | Distinctive law |
|---|---|---|
| **Attack** | Manufactured — an adversarial examiner with no authoring stake, dispatched against a proposed artifact *before commitment*, phrased to refute | Targets the artifact's own claim list; survived-with-attack-named is confirmation value; the attacker's misses are recorded retroactively; the highest-value attack class is the premise kill |
| **Collision** | Emergent — two honest parties independently derive one contract (canonically: a test author deriving expectations blind from committed artifacts) and disagree | Nobody attacked anybody — the disagreement is the datum; the verdict assigns fault among **three** parties: derivation wrong, implementation wrong, or *the contract is open* — an undecided fork surfaced, routing to specification work |
| **Forecast** | The future — predictions and kill-criteria frozen at episode entry, scored at boundaries, never edited | Pre-registration transposed into planning (Nosek et al., 2018); the only species that refines the *predictor* rather than the corpus — accumulated scorecards become calibration priors about the planning faculty |
| **Reality** | The world, unscheduled — defects that manifest | Counts are floors, never rates (observed-zero ≠ zero); attribution runs backward through judgment at a periodic pass; paired archaeology streams (fixes that landed before codification; codifications that forced fixes) close the causality ambiguity either alone carries |
| **Currency** | Time and drift — the standing hypothesis "this is still true" | Declared at write time: a falsification list plus revisit triggers make staleness *scheduled* rather than discovered; retirement keys on mootness or coverage migration, never on low salience — the rarely-binding entry can be the killer-item; watch referents, never aliases |
| **Coding** | A blind second coder — labels versus labels over shared anchors | The countermeasure to self-emitted-taxonomy bias: an independent party classifies raw anchored instances *without seeing* the candidate labels; agreement ratifies a class, disagreement keeps the boundary open |

The table carries a gradient. Two species are **passive** — their
sources exist unbidden: the world votes and time passes whether or not
anyone keeps the ledger. The other four are **active**: their
contradiction is *manufactured* — an examiner dispatched, a blind
derivation staffed, a prediction frozen, a second coder run — each an
investment in independence machinery. Admission is by test, not
template: a new species is warranted only when a belief domain no
existing store's lifecycle owns meets a structurally independent
contradiction source, an unstaked adjudicator, and a named consolidation
consumer — refusal a first-class outcome. The doctrine runs as soon as
one species runs with all five slots filled; the deployment ordering —
passive first, active as affordable — is § 14.5's genesis rule, not a
law. The set is closed-with-escape (§ 17): a claimed seventh species
does not embarrass the table; it re-derives it.

### 7.4 The slow loop: consolidation as a slot-factored backward pass

The fast loop — the session, § 7.6 — generates signal; the **slow loop**
is the set of scheduled passes that consume it and move knowledge
between tiers: the **episodic pass**, walking the observation piles
grouped by shape (judgment-bounded, never cadence-bound); the
**classification passes**, blind-coding accumulated ledger records
against their raw anchors (§ 7.3, coding species); the **demotion
reviews**, reading use-time telemetry; the falsification-surface
audits, walking a conditioned claim's falsification surface leg by leg
(§ 11.4); and the boundary ceremonies of § 14.4. Consolidation runs at
these passes and nowhere else — that is, where the human is present.

Recurrence — never a single record — drives structural change; three
disciplines, together the refinement law, govern every pass.

**Noise-filter before updating process.** Every failure is classified
irreducible-at-the-time (no authoring duty could have prevented it)
versus reducible (a duty was missed — route it): the aleatoric/epistemic
split performed by judgment, preventing process overfitting to one-off
failures. Irreducible recurrences tune the *detection* side — never the
authoring side.

**Route before minting.** A ratified recurrence lands at the *cheapest
sufficient home*, walked in order: edit to an existing template → row in
an existing duty table → rule enrollment → hook edit on an existing
checkpoint → new checkpoint (only on a genuinely new authority join) →
mechanical gate (only where fully mechanical). The ladder's upper rungs
are one operator, named: the **latch→checkpoint promotion** — the
moment a latch's owed act stops being "apply this record's payload" and
becomes a bounded judgment over an authority join, the latch has
outgrown its bearer and mints as a checkpoint — with the
de-latch-to-gate move (below) as its reverse. Refusal is a first-class
outcome: every
standing mechanism taxes every future session, and the ladder prices
that at admission.

**Bars grade with blast radius.** A cheap episodic note takes one
noticing; a promotion candidate, two anchored recurrences; a rule, an
observed recurrence *plus* human approval; a mechanical gate, two
instances of silent failure; the always-loaded constitutional tier,
repeated evidence at scale plus a forced eviction under its hard cap
(I8). Deeper, wider layers update slower — the damper an unreliable
attribution channel requires (§ 15). The bar values are house
convention, honestly labeled; the field's equivalents derive their
currencies no better (Zhao et al., 2024; Park et al., 2023). The
principled part is the shape: counts nominate, the human decides,
promotion raises abstraction (I6, § 3).

**The slot-factored backward pass.** Given accumulated evidence against
an entry, *what kind* of refinement is needed? Text space has no
gradient, and the holistic alternative ("this rule seems wrong; rewrite
it") inherits the field's measured attribution weakness (§ 15). The
entry contract restores tractability: **the pentad is the coordinate
system in which text-space credit assignment becomes local.** Each
signal class carries a characteristic *slot signature*:

| Accumulated evidence | Indicted slot | Slot-local operator |
|---|---|---|
| Fired-but-not-applicable dominates (applied ÷ fired low) | Activation — precision | Tighten the guard; grow its not-this clause |
| Fired-off-map — applied outside the declared domain | Activation — boundary | Widen or re-shape the hook; the declaration was wrong, not the firing |
| Should-have-fired, surfaced by a defect backtrace or a recall probe | Activation — recall | Re-key; add a routing family; audit for the structural zero |
| Recalled, applied — and the steer still corrected the outcome | Payload | Re-abstract (altitude fault) or re-derive (content fault) |
| Clean application on one recurring sub-shape, never on another | Payload — fused | Split: leaf the entry (below) |
| A falsification-list fact reversed; a revisit trigger fired; anchors rotted | Warrant | Re-adjudicate; upgrade or drop; status flip |
| A defect shipped green through the gate | Enforcement | Grow the floor if the failed part is newly mechanical; otherwise re-disclose the residue honestly |
| The gate fires on correct behavior | Enforcement — over-reach | Shrink the floor to the invariant it serves |
| Never fired across review periods; domain no longer entered; duty fully absorbed by a floor | Lifecycle | Demote, retire on mootness, or de-enroll by coverage migration — after the killer-item check (I7) |

The first two rows separate only under the edge/guard factoring of § 9's
latch tuple, and the factoring supplies a finer indictment vocabulary
than any single fires-when field can: considered-but-guard-failed is
routing working as designed and indicts nothing; fired-but-not-
applicable indicts the guard; fired-off-map indicts the declared
domain. Where the pair is not declared as fields — the factoring is
design-stage (§ 9) — the coarse ratio applied ÷ considered stands in as
the nominator, a floor over the finer reading.

Three properties keep the procedure honest. **Locality:** the pass asks
"which slot does this evidence indict, and which way?", never "is this
entry good?" — which makes the owner-as-optimizer asymmetry (§ 2)
feasible at human frequency. **Typed sparsity:** the noise filter runs
first, so no slot updates on an irreducible failure; the evidence *type*
supplies the direction, the recurrence *count* the nomination, the human
the magnitude and verdict. **Floors, not rates:** several rows read
detection-limited streams (observed ≠ occurrence), and one —
should-have-fired — has no complete instrument at all (§ 16); the pass
treats those terms as lower bounds.

**Split and fold.** Two operators act on entry *granularity* rather
than a single slot, and both are moves on the corpus graph of § 5 — a
vertex split and an edge contraction, the operations that give the
lineage DAG its branch points. Dispositions bimodal across
recognizable sub-cases mark a fused entry: **split** it into leaves,
each re-satisfying the whole pentad, the parent retiring by coverage
migration or surviving as the leaves' shared warrant (§ 8) — one
tombstone, several heirs. The reverse signal is **covariance**: two
entries whose answers converge put their differentiation under stress.
Covariance alone, though, only *watches*; the **fold** is an edge
contraction, and contraction is defined only on an edge — entailment
between the entries' answers is that edge, and confirming it is what
licenses the merge. The fold contracts exactly the edge the covariance
revealed: two records, one successor, their lineages meeting. Default:
fold-before-split, since a premature split mints two lifecycles where
one suffices; every split or fold is ratified against the raw anchors,
never the labels — § 7.5's staged minting applied to entry boundaries.
When the nominating signal arrives through a vocabulary's escape stream
rather than an entry's dispositions, the choice between these operators
and their axis-level namesakes is computed, not felt — § 7.5's revision
routing.

**The checkpoint tier under the same analysis.** A **checkpoint** is
the read-side complement of the ledger machinery: a record minted where
an activation join acquires a bounded judgment duty — payload the
judgment procedure; warrant its authority slot's filling and that
filling's truth-maker (the slot is typed, and may honestly read
none-with-adjudicator — § 12.4 gives the range); a typed record with a
named consumer, a paired gate, its own identity and retirement
machinery. It is itself pentad-shaped, so its telemetry factors
identically; its activation is one row of § 9's fan, grown to the
commitment grain. Fired/not-applicable distributions and off-map fire
records indict its hook: re-scope it. Answer entailment between two
checkpoints' duties is the fold signal: merge — **exactly one
checkpoint owns any judgment**, the duties-disjoint law (§ 9 transposes
it per slot). One reading rule guards the tier: distributions are
**signature-relative** — a checkpoint firing hard in a period whose
work is its class is the system working, not an anomaly to prune.

The tier's boundary tests complete a classification. A checkpoint whose
judgment residue has emptied **de-latches to a pure gate**,
probationary; one whose consulted authority has dissolved retires with
it; and one whose consulted authority never existed is not defective —
it is a lens, a judgment duty walked against the generalizer itself
(§ 12.6 gives the machinery). Gate-work, consultation, lens — total
mechanism, judgment against a consultable authority, judgment against
the generalizer: **the duty-class triple**, three classes exhausting
the checkpoint space. The tests run in order: no judgment residue →
gate; a consultable authority → consultation; neither → lens.

The triple is not a caste system; its classes exchange members under
the same ladder that prices minting — the question-tier face of
route-before-mint:

> **The crystallization law.** Lens and consultation are life-stages,
> not castes, and the lens exits by two distinct doors.
> **Variance-collapse**: a lens whose answer stream stops varying has
> produced a cacheable artifact — the answer lands at the cheapest
> sufficient home (a rule sentence, an exclusion edge, a gate) and the
> question retires; a question is never minted as a standing artifact
> on a recurring answer. **Authority-crystallization**: a lens whose
> subject accrues a consultable authority — a store of settled answers,
> a registry, an oracle — converts to a consultation duty: the question
> survives and its authority slot fills. The reverse door exists too: a
> consultation whose cached answer stops fitting reopens as a lens. The
> discriminator at the first door is **answer variance**, never firing
> frequency; at the second, the authority's existence. A lens is
> correct exactly where neither door is open — the answer uncacheable,
> no authority consultable — which is why novel territory is lens-dense
> and settled territory gate-dense, and a corpus's lens-to-gate ratio
> over a domain is a maturity reading, not a defect count.

In deployment the discriminator has run at cluster scale in both
directions — offered as observed: a recurring-answer cluster folded
down-ladder into existing homes with its question never minted, while a
varying-answer cluster minted as a standing question — the law naming
what the minting passes already did.

The law supplies the inverse I7's retirement leg lacked for
question-shaped duties; § 14.5 applies its maturity reading at genesis.

The tier's instrumentation splits with the triple. Consultation-side
duties are measured in the fan's vocabulary — applied ÷ considered,
fired-off-map, and the finer considered-but-guard-failed versus
fired-but-not-applicable split — authority-shaped questions about
firing and coverage. A lens answers none of them: it is instrumented on
answer variance (the crystallization signal), decoy rejection, and its
miss stream — § 12.6 states the contract. Two telemetry vocabularies
for two duty classes, never one list; the one shared instrument is the
should-have-fired archaeology.

Checkpoints and ledgers are complements by design: checkpoints without
ledgers are a confident recall cache, rotting invisibly; ledgers
without checkpoints are a well-audited graveyard. Joined: consolidation
passes over the ledgers are the only legitimate minters of new
checkpoints, rules, and gates; the checkpoint walk is where minted
knowledge earns its keep; per-checkpoint dispositions feed back into
the ledgers. The loop closes.

Every threshold, at every tier, pairs with this scheduled reverse (I7):
applied ÷ considered as nominator, never verdict; mootness and coverage
migration as retirement keys, never low salience. Running the
up-pipeline without the down-pipeline accumulates confidently-wrong
rules — CBR's utility problem and Wikipedia's ossification (§ 15), one
lesson from two directions.

### 7.5 Escape hatches, vocabulary birth, and revision routing

Every closed vocabulary in the system — verdict sets, class registries,
routing families — is **closed-with-escape**: it ships an honest escape
(`other(<what>)`, `unresolved(<carry>)`) — not tolerated slack but the
vocabulary's own measurement channel. A forced pick manufactures noise
in both directions at once — inflating a wrong class's count while
keeping the missing
class invisible — corrupting the exact quantity the loop consolidates
on. The anti-pattern wearing rigor's costume: a closed set whose only
"escape" is loud rejection at ingress — rejection is a gate, an escape
is an instrument, a healthy closed set has both. Escapes are per-level
in any routing hierarchy.

The escape law sits inside a fuller birth procedure. Where a closed
decision procedure encloses the space, the class set is **derived** —
the decision tree's leaves, total by construction — and a recurring
escape there indicts the procedure, not just a missing label. Where no
procedure encloses the space, minting is **staged**: free prose until
instances exist (classes invented ahead of instances are priming, not
observation); then organic labels with mandatory anchors — the label a
hypothesis, the anchored instance the datum; then blind-coded
ratification at two to three recurrences (§ 7.3's coding species); then
a closed registry with loud-unknown ingress, its misfits visible *as*
misfits. Either way, one universal rule: the adjudicator alone fills the
verdict field — a proposing party submits records with the verdict
*pending*, structurally unable to grade itself.

Growth from the residue stream carries an independence qualifier: two
same-shaped escapes mint the missing class only when they arise from
**independent contexts** — two escapes from one context are one datum;
this binds hardest at fan-out scale (§ 14.3).

**Revision routing.** The escape stream nominates growth, but the pile
alone under-determines the *response*. Growth is **horizontal** — the
axis keeps its question: add a member, partition a member, merge
members, retire a member — or **vertical** — the axis set itself
changes: split a conflated axis, fold two covarying axes, re-home the
distinction onto an existing other axis. The two families differ in
cost and in failure mode, and choosing between them by feel is exactly
the holistic refinement the slot-factored backward pass (§ 7.4) exists
to replace. The routing has a formal object: an axis *partitions* the
instance set into its members' blocks; a candidate distinction — read
off a cluster of same-shaped escape payloads — *also* partitions it;
**the relation between the two partitions routes the move.** A
candidate that refines a single block belongs inside that member
(partition it — horizontal). One that cross-cuts several members while
remaining nearly independent of the member label is a free dimension
the axis conflated (split the axis — vertical). One that coincides with
or coarsens the axis is the axis renamed (fold). One mutually exclusive
with every member is the missing peer (add — horizontal). Partition
refinement, independence, and coarsening are all mechanically
computable over an itemized escape record — the second, deeper reason
the escape carries its payload (`other(<what>)`, never bare):
itemization is what makes the routing computable at all.
Itemized-never-net (§ 13), applied to classification.

Three cheap features approximate the partition relation over the
escape records: **truth-maker identity** — does adjudicating the
candidate route to this axis's declared evidence, or elsewhere?
Different ⇒ vertical, full stop: the candidate answers a different
question and cannot be a member here regardless of how it distributes.
**Cross-cut breadth** — how many existing members' instances carry the
distinction: zero, a missing peer; one, local to that member; two or
more, cross-cutting. **Dependence** — how strongly carrying the
distinction covaries with the member label: low dependence at high
breadth marks an orthogonal dimension; dependence near one marks a fold
(§ 7.4's covariance watch, made quantitative). One principle stands
behind every row of the resulting table — *is the new distinction
orthogonal to the axis's question, or a value within it?*

| Reading | Route |
|---|---|
| Truth-maker different | Vertical: new axis, or re-home to an existing one |
| Same truth-maker; breadth ≥ 2; dependence low | Vertical: split — the axis conflated two questions |
| Same truth-maker; breadth = 1 | Horizontal: partition that member |
| Same truth-maker; breadth = 0; a mutually exclusive peer | Horizontal: add the member |
| Two members; dependence ≈ 1 | Horizontal: fold the members |
| Two axes; dependence ≈ 1 | Vertical: fold the axes |

Before the table runs, the axis's space-kind — whether a closed
decision procedure encloses it, above — settles half the question. On a
decision-procedure axis, closed by construction, any recurring escape
is inherently vertical: there is no room for a missing value in a total
procedure, so the escape indicts the procedure itself, and the fix is a
loud re-derivation, never "just add a member." On an open-phenomenon
axis, escapes are the normal growth channel; the table is live and
horizontal is the common case.

The vertical test earns its keep on a severity asymmetry. A horizontal
miss corrupts a *count*: a missing member's instances sat in the escape
pile; the fix is additive, and nothing already classified is wrong. A
vertical miss corrupts the *structure*: every instance was forced to
average two independent questions into one token, so the labels do not
mean what they say. **Vertical error is to classification what
net-collapse is to aggregation** — the failure § 13's
itemized-never-net law exists to block: the axis can be directionally
wrong while every escape payload is individually right, and the
corruption is invisible from inside the labels — which is why a wrong
axis at genesis outranks any number of missing members. The routing's
split and fold are namesakes of § 7.4's operators, not the same moves:
those act on entry granularity — a vertex split, an edge contraction on
the corpus graph — while these act on axis structure, and a revision
must know which object it is revising.

The routing is a nominator, never a verdict, and its enforcement split
is exact. Floor: detect the pile crossing the recurrence bar under the
independence qualifier; compute the member-by-distinction contingency
table and the three features; emit the route as a nomination with the
table attached — a warning, never an error. Residue: whether the
distinction is real or small-N noise (I11); whether a genuinely
orthogonal axis is *worth* minting (I5 — every axis taxes every future
classification); and the naming of the new axis's question and
truth-maker (I2 — the machine proposes, never authors). Three honest
limits ship with the instrument: clustering escapes by payload is
itself model-assisted and can launder the classifier's own bias, so
blind-coded ratification (§ 7.3's coding species) is mandatory before
any route fires; the dependence feature is unreliable at small N, so
the nominator weakens early and never fires a schema change on a
handful of escapes; and a thick escape that straddles
value-and-dimension is flagged ambiguous and escalated, never forced
into a route.

### 7.6 The carrier: the fast loop

What carries the slow loop is the **fast loop**: the session, the only
place knowledge is actually exercised and every signal the slow loop
consumes is generated. Adopting the stores without it builds a library,
not a learning system.

A session opens by **assembling its context**: the constitutional tier
loads unconditionally; the trace store's carry-forward header restores
continuity; a brief orientation classifies the work's shape; the
checkpoint walk runs the fixed join schedule (§§ 4, 9). The assembled
window is the query's result set, under § 4's cost discipline.

Work proceeds with micro-decisions delegated to the strongest available
adjudicators — compiler, tests, the live tree (§ 14.2) — and
verification behavioral (§ 2). Candidate signal is jotted at the
episodic floor as work runs: one noticing, one anchor, seconds of cost —
capture must stay near-free, or the capture problem (Lee, 1997) wins.

The session **closes by producing the slow loop's inputs** — the step
most pile-based practice omits. A reflect pass leads with the session's
typed event streams before free recall; the query's returns get
per-entry **use-time dispositions** — applied,
considered-but-not-applicable, fired-off-map — the telemetry the
demotion review reads (§ 7.4); observations and caught contradictions
file to their owning ledgers; a session log appends to the trace store.
The reflect step terminates at the human (§ 7.1): the session proposes,
and nothing it proposes is yet true.

Boot consumes what the slow loop produced; close produces what it will
consume. That closure — not any individual store — is the system.

### 7.7 The pipeline, worked end-to-end

The refinement law in motion: one generic lesson traced through every
tier — agents notice, draft, and nominate; the world contradicts; every
movement between tiers is the human's (§ 2).

**Noticing (bar: one instance).** A session, mid-task, notices a retry
wrapper discards the underlying error's cause when it rethrows. Not
worth stopping for; not nothing. One line lands in the episodic pile —
*observed: wrapped errors in the ingest path lose their cause; re-check
when touching error wrapping* — with a file anchor. No classification,
decision, or process change: the entry bar sits deliberately at the
floor.

**Promotion (episodic → case).** Weeks later a second session hits the
same shape in the export path and appends its line. The episodic pass
groups the pile by shape: two anchored instances of one undecided
fork — this move's bar. The pass fixes nothing; it surfaces a
**promotion candidate** — recurring and undecided, so someone must
decide it once. A decision entry drafted in the case store's shape
(options considered; constraining facts as a falsification list) faces
the write-time examiner (attack species, § 7.3); the human performs the
promotion, which **raises abstraction** (I6): *errors that wrap must
carry their cause* — object-decoupled — not *fix ingest and export*. The
observations are deleted-with-pointer; the pile empties *by* promotion.

**Proceduralization (case → rule).** The decision binds only if
recalled, and its domain is entered constantly — every catch block that
rethrows. The tell that a case needs a rule form: a session observed
**not propagating it** — settled, discoverable, still missed. Observed
non-propagation nominates; the human's approval promotes. The rule is
the decision's duty form — its hook: authoring a catch that wraps or
rethrows — the duty sentence carrying the obligation, the decision
cited as warrant. The case keeps the *why*; the rule the
*when-and-what*; nothing duplicated that could drift. This middle
operator — case → production rule — is the pipeline's load-bearing one:
it converts a thing the project *knows* into a thing that *fires*.

**Mechanization (rule → floor).** Later, part of the duty proves fully
mechanical — *the wrapping constructor receives a cause argument* is
lintable. When that part has failed silently twice (the silent-failure
bar), a gate takes it. The rule's floor grows; its residue shrinks and
is re-disclosed: the gate checks that *a* cause is passed; judgment
still owns whether it is the *right* one (I10).

**And back down, on the calendar.** At the periodic review each rule's
dispositions (§ 7.6) are read — applied ÷ considered as nominator, never
verdict. A rule routed constantly and rarely applicable gets its hook
re-scoped; one whose gate fully owns its duty de-enrolls by coverage
migration — living on at its enforcement surface, the decision staying
as warrant; the case itself retires only on mootness. Every move is the
human's; the counters only nominate.

The trace shows structurally what § 14 argues in general: at each
handoff, pentad slots change hands exactly as the coordinates predict —
the noticing had only activation and anchor; the decision added a
warrant; the rule added routable activation and an enforcement
obligation; the gate is all floor. The families are stations on one
line.

## 8. Grains: the units of ratification, falsification, and retrieval

In a governed corpus, three units of aggregation come apart. The
**retrieval grain** is the hook's incidence set: what one reading
session opens together, grouped by hook. The **commitment grain** is the
record: what one human adjudication event ratifies — I2 (§ 6) makes the
human gate's throughput the deliberate bottleneck, and the commitment
grain is that gate's unit of work. The **falsification grain** is the
claim, or leaf: what a contradiction lands on — the world falsifies not
a record but a specific assertion inside one.

The three coincide only in a corpus of one-claim records consulted and
ratified alone — which nobody runs. So the grains diverge, and every
physical organization privileges one at the others' expense:
retrieval-grain storage duplicates claims under every hook — the
tier-copy that drifts (I3, § 6); falsification-grain storage fragments
the warrant and multiplies ratification acts until the gate clogs or
rubber-stamps; commitment-grain storage bundles claims whose
falsification surfaces later diverge — the strain leafing resolves
below.

The resolution is a law, stated as design:

> **Canonical storage sits at the commitment grain. The falsification
> grain is materialized lazily, by contradiction-driven leafing. The
> retrieval grain is derived, as a hook-major projection.**

The storage clause's argument is economic and constitutional at once:
the human gate is the bottleneck by design, the record its unit of work,
so bundling the claims one hook opens together into one record
*amortizes the ratification act*.

Three corollaries. **(a) The latch is a non-unique secondary index —
never the primary key**: latches are among the corpus's most-revised
slots, and a revisable slot must never be the identity — the cool-URIs
lesson (Berners-Lee, 1998) behind § 5's identifier law. The same law
holds the checkpoint apart from the latch (§ 7.4): a checkpoint has
crossed the commitment grain and is ratified as a record; a latch never
is. **(b) Hook-major storage re-derives the law by exhaustion**: either
claims duplicate under every hook — tier-copies, which drift (I3) — or
claims get stable identifiers and the hook files hold references,
re-inventing exactly the law's own architecture. **(c) The read surface
should nonetheless be hook-major.** Latches and records stand in a
bipartite incidence graph — corollary (a) restated: the latch is an
index into that graph, never an identity within it — and storage and
projection are its two orientations: storage record-major, the
stage-one index a session consults (§ 4.1) hook-major. The hook-major
orientation is also why the projection doubles as a *leafing
instrument*: answer covariance (the fold nomination) and heterogeneous
claims under one hook (the split nomination) both surface as adjacency
structure — records clustering under the same hooks.

The pressure demanding the law has been measured: in one deployed
corpus, roughly a third of revisit conditions shared no content word
with their own record's consultation hook. Read at the three levels § 9
separates, the finding is one fact three times over: at the hook level,
the revisit condition and the consultation hook are different
predicates; at the latch level, a revisit trigger is its own latch over
the *world*, not the record's subject; at the key-space level, the two
draw on disjoint vocabularies — so no single stage-one key can serve
both consultation and falsification.

**Record leafing** is the case store's granularity law — § 7.4's
split-and-fold generalized to record payloads. Its premise:
**born-bundled is legitimate**. Claim boundaries are not reliably
authorable at write time, because which assertions prove independently
falsifiable depends on how the world chooses to contradict. What the
author *can* declare is the set of world-property **dimensions** the
falsification surface watches (§ 10.5) — the axes along which the world
*could* draw boundaries, without asserting where any boundary lies. The
doctrine's granularity error is not bundling — it is refusing to cut
when the world draws one.

**The contradiction draws the cut.** Claim individuation is a
posteriori, by falsification surface: a contradiction lands on a
*region* of the record's world-property space, and a record turns out to
contain two claims exactly when a contradiction leaves part of the
payload's space untouched. Under § 3's truth-maker discipline this is
near-definitional — a claim's identity *is* its truth-maker. This
inverts the instinct to atomize up front: a priori atomization spends
ratification throughput now to mis-draw boundaries the world would have
drawn differently.

Because contradictions localize to regions, not positions in a
sequence, the leaf structure is a **lattice, not a tree** — stated as
design: a split-*sequence* model fails the multi-axis case (a B-cut
crossing an earlier A-boundary is localizable to neither A-leaf), while
in the lattice it is routine. Leaves are **cells of the accumulated
common refinement** of all cuts so far; cells never overlap.
**Materialization stays lazy**: cells materialize only when a
contradiction lands, so an uncontradicted record remains one leaf.
**A joint-predicate cut mints a compound dimension**, entering the
record's basis closed-with-escape (§ 7.5). And **leaf identity is
region-coordinates, never split-sequence ordinals**: coordinates
(dimension × interval) survive any refinement — corollary (a) at the
leaf tier, and what makes per-cell supersedure stable.

Leafing is **one operation with two nominators**: the scheduled
consolidation pass (§ 7.4), and the settlement event — **a contradiction
landing on a proper region both reveals and forces the cell boundary,
because a partial verdict cannot honestly attach to an unsplit whole**.
The one-dimensional special case is the revisit trigger's partial-fire
split (§ 9): a single axis, cut once.

**Per-cell supersedure** gives partial wrongness clean mechanics: cut at
the region boundary the contradiction drew; tombstone the falsified cell
with a successor pointer; leave surviving cells untouched (a
hollowed-out record tombstones wholesale). Nothing is amended in place —
§ 5's write law, and its lineage DAG, continued at the finer grain —
and this dissolves the immutability/amendability shear behind duty
conflation (§ 12.1): a record can be partially wrong without freezing
the error or rewriting history.

The operation is closed-with-escape, and **the cut license is
store-dependent** — two regimes, stated apart and never averaged. Where
contradictions arrive against claims the project's own execution
settles — the case store — the syntactic license suffices: a
contradiction naming an unanticipated world-property region is not an
escape case; it cuts a declared dimension or mints a compound one. In
the belief store the license tightens: **region-bearing means
predicted, not merely named** — the cut must fall on a variable a
pre-registered mechanism declared before the contradiction it would
explain (§ 10.6 states the admissibility rule such a mechanism
satisfies), because an unanticipated-dimension cut read off the flip it
explains is the garden of forking paths. What counts as basis-free
correspondingly widens there, and without a pre-registered mechanism
the narrow-versus-re-adjudicate fork is unfalsifiable — the operational
content behind the boundary condition (§ 16) that leafing degenerates
if most real contradictions are basis-free. The escape is reserved for
**basis-free** contradictions, naming *no* world-property region under
the store's own license: they land on the record as a whole, and a
*recurring* basis-free contradiction indicts the record's **warrant**,
not any cell — the disposition is wholesale re-adjudication, not
another cut (kin to the collision species' third verdict, § 7.3).
Retrospective detectors may *trigger* the re-adjudication; they never
adjudicate.

The concept's boundary: leafing resolves partial falsification of cases
and claims; it does not resolve duty tracking — "did you do it at every
site?" has no home inside any cell. Leafing is the case store's
granularity law; the register is the duty store's lifecycle law (§ 12).

Read as a standing structure rather than an operation, the accumulated
lattice is more than a granularity law: it is the corpus's
**refinement engine**, and its honest characterization is exact about
what the engine is for.

> **Conditional refinement is a supersession-disciplined,
> human-adjudicated partition of a judgment's outcome space that
> doubles as the corpus's conditioning-and-activation engine: it
> decides which judgments bear on a target, which are overridden there,
> and which judgments a world-item activates at all. It is inert for
> exactly one thing — quantification: it carries no uncertainty
> calculus and no regime predictor.**

The decomposition behind the sentence: projecting a body of belief onto
a target decomposes into **four acts** — *select* which claims bear and
resolve which are overridden here; *predict* which regime the target
falls in; *quantify* each survivor; *combine*. The lattice owns the
first act natively — its applies-when/except-when edges, read as
defeasible inheritance with a specificity order (Touretzky, 1986;
Poole, 1985), *are* the selection engine, and its typed roots are
stage-one attention in graph form — and it owns none of the rest
(§ 11.3 gives the disciplines a computed quantification projection
obeys). Since identifying the conditioning is the severest failure a
forecasting reading of the lattice finds, the structure is doing the
hardest part of that work; it simply is not doing the arithmetic. The
structure has kin sharing one order-theoretic skeleton — the
foundationalist belief base (Hansson, 1999), the argumentation calculus
(Dung, 1995), the concept lattice (Ganter & Wille, 1999), and
assumption-based bookkeeping (de Kleer, 1986) — cited as kinship over a
shared skeleton, never as names for one identical object.

Two laws travel with the characterization. **The two-DAGs law**: the
*activation* graph — a judgment to the typed root or authority it
instantiates — answers *when does this enter context*; the *refinement*
graph — successor and supersedure edges — answers *is this a more
specific case of that*. Different truth-makers; the duties-disjoint law
(§ 7.4) and § 9's key-space separation forbid fusing them. Leaf-to-root
is the stored edge; root-to-leaf is a computed inverse (I3) — which is
what keeps the index robust while leaves supersede constantly and roots
stay put. And **the projection returns an antichain, not a leaf**: two
judgments can co-apply to a target with no specificity order between
them — the Nixon diamond of the inheritance literature (Horty,
Thomason & Touretzky, 1990) — and the honest behavior is skeptical:
display both as a conflict the human disposes; never silently tiebreak.
The antichain is an *inter-record* structure — two records co-applying
at one target — and does not touch the intra-record law above that one
record's cells never overlap. In aggregate, a standing contradiction
becomes a boundary: a contrarian pair resolves by region, each ruling
where its condition holds — a fight becomes a partition — but only in
aggregate; at any specific target the antichain case governs.

One identity ties forward: **the leaf lattice's axes and the watch
layer's dimensions are the same axes** — one structure read from two
sides (§ 10.4 states the unified object).

## 9. Activation: the latch, the fan, the port calculus

The entry contract's first slot reads as one question: *when does this
enter context, or fire?* — two verbs, and each now carries a precise
referent: entry is stage-one selection (§ 4.1), and a fire is a reified
event this section defines. The § 8 measurement shows the slot bundling
keys from different spaces, and unbundling it demands a vocabulary
discipline first, because the objects at stake sit at three grains:

> **The hook** is a latch's fires-when key — the recognition predicate,
> written in a key-space's governed vocabulary. **The latch** is the
> typed activation unit: the full tuple attached to a pentad slot, of
> which the hook is one component. The checkpoint (§ 7.4) is a latch
> grown to the commitment grain — a record minted where an activation
> join acquires a bounded judgment duty. One word per tier: each term
> is the next one's part or seed.

The precision is not pedantry; it is a general lesson about vocabulary
in corpus design. Activation words are where corpus lexicons fork: in a
family of deployed corpora read at lexicon grain, one activation word
came to denote three referents across four examined corpora — the
recognition predicate in some, the activated judgment record in
another, a shelf of full checkpoints in a third — one lexicon carrying
an explicit collision flag. The fork is not sloppiness; it is what
happens when a corpus's own machinery is named at one grain and used at
three, and each adopter inherits the seam faithfully. A corpus lexicon
is itself a governed key-space — § 7.5's closed-set law at term grain:
one word per tier, collisions flagged, platform homonyms disclaimed —
and the doctrine holds its own activation vocabulary to it.

**What a latch is precedes which latches exist.** The naive placement
makes a latch a property of its record, and the resemblance is real: a
latch inheres in a bearer — declared on the record, traveling with it,
its admissibility governed by the bearer's kind — and the record's
subject supplies the property-like half of its content, the binding
that says *which* region of the key-space this instance watches. The
limit is exact: a property is truth-made by its bearer alone, while a
latch asserts that a join between the record and an external stream —
passing work-shapes, the moving world, a neighbor's change, a diff, a
competence signal — will be recognized when it occurs. Formal ontology
has owned the distinction for decades: a quality is fully actual in its
bearer; a disposition is a latent tendency realized only when an
external process triggers it, existing undiminished while unrealized
(Arp, Smith & Spear, 2015). Stated as law:

> **The disposition law.** A latch is a disposition, never a quality: a
> first-class dependent entity with its own identity and lifecycle,
> truth-made by an encounter between its record and an external
> stream — existent while unfired, independently amendable. A property
> is what a record is; a latch is what a record is waiting for.

The category even types the fan: the revisit trigger is a disposition
proper — the world triggers it; the consultation hook is nearer a role,
conferred by the arriving work-shape rather than grounded in the
record's own make-up; the floor gate is nearer a function — what the
enforcement surface is for. The borrowed categories are graded as § 17
grades all borrowed vocabulary: category, never mechanism. And the
lifecycle clause is the least optional part: every mature field that
externalizes activation gives the activation unit its own identity and
lifecycle, separately amendable from the knowledge it serves, because
scope drifts faster than substance (von Wright, 1963, states the
decomposition as the norm kernel: character, content, and *condition of
application* as separable components).

The law places the latch between two refused poles. The property pole
fails as stated: a property has no lifecycle of its own, and a latch
must. The opposite pole is the pure overlay — activation owned entirely
by a third party, the record oblivious, the shape of production rules,
content-based publish/subscribe, and aspect-oriented pointcuts. The
overlay fields are the *reactive* fields, their subject matter event
streams, and they pay two measured costs the knowledge fields refused:
the fragile pointcut problem — hooks keyed on incidental structure of
an oblivious base silently over- and under-fire under safe-looking
edits (Koppen & Störzer, 2004) — and cascade opacity: rules triggering
rules, with termination and confluence undecidable without
reconstructing a triggering graph nobody declared (Aiken, Widom &
Hellerstein, 1992). A governed corpus is a knowledge system, not an
event bus; its records are the A-side, and its activation lands between
the poles: declared on the record, typed by the kind, keyed into an
external space, with its own lifecycle — a declared port, not a foreign
hook. The overlay shape is retained deliberately for exactly one organ:
the examiner species (§ 7.3) is overlay-shaped by design, because
independence from the record is its point — contradiction machinery
must not be declared by its target.

**The fan.** A consultation hook is keyed on **work-shape** — what kind
of session should open this record — and is considered at plan
assembly. A revisit trigger is keyed on **world-state** — what event
would make the warrant stale — and fires when the world moves. No
overlap in vocabulary, consumers, or owed acts. The unbundled slot,
as a design schema:

> **The fan schema.** An artifact is a resident {payload, warrant} plus
> a fan of typed latches, each latch a tuple ⟨key-space · edge · guard ·
> consumer · owed act (+ role) · lifecycle⟩ attached to a specific
> pentad slot. The fan's row set is indexed by store × kind: a record's
> kind declares which rows it may carry — no artifact carries every
> row (§ 11 gives the kind calculus).

The **edge** is the event, or the polling schedule that stands in for
one, that makes the latch *considered*; the **guard** is the predicate
that makes a considered latch *fire*. Together they are the latch's
hook — the fires-when, unbundled one field further. The activation
*disciplines* differ exactly as digital electronics splits them — the
consultation hook is **level-sensitive**, polled at the scheduled walk
and answering to whatever shape the session holds at the poll, while the
revisit trigger is **edge-triggered**, armed continuously and firing on
a transition of the world — but the discipline is a *value of the edge
field*, not a boundary between latch types. The edge/guard pair is
stated as design: no deployment yet declares the two as separate
fields. The owed act carries a **role** mark: **dispositive** — a fire
can settle the record, once disposed — or **corroborating** — a fire
bears, never settles; the record's effective falsification grammar
joins over its dispositive latches only (the port calculus below), and
§ 10.5's watch modes state the same distinction one level down.

| Latch type | Key-space | Edge | Consumer | Owed act |
|---|---|---|---|---|
| Consultation hook (*fires-when / read-when*) | work-shape | plan assembly (level-sensitive) | the working session | apply the payload |
| Revisit trigger (*watch / revisit-if*) | world-state | the world moving (edge-triggered) | the adjudication loop | re-adjudicate the warrant |
| Wiring edge (*derives-from, adopts, supersedes*) | neighbor identity | a neighbor changing | propagation | re-derive / re-check |
| Floor gate | the diff | commit / review | the gate runner | check the mechanical floor |
| Retirement trigger | competence signals | the consolidation pass | the lifecycle review | retire / demote |

The parenthetical italics are reader-facing aliases of each row's hook,
never schema fields. Each row is a latch; the rows attach to
*different pentad slots* (§ 6): the consultation hook to the payload,
the revisit trigger to the warrant, the wiring edge to the warrant's
dependencies, the floor gate to the enforcement split, the retirement
trigger to lifecycle. The pentad is unchanged as a completeness
contract; its first slot was five keys wearing one name. The
world/internal cut (§ 3.2) falls cleanly across the table: the revisit
trigger is the fan's only world-facing row. The wiring-edge row is
where the fan meets the corpus graph (§ 5) and the duty store's
relational population (§ 12.4): a wiring edge is the graph's
maintenance latch — it keeps an *existing* edge true when a neighbor
moves — while the duty that every required edge *exist* belongs to the
relational register's complement audit. In deployed corpora the fan is
latent in mature practice — the reformulation names what the organs
already do severally. And it makes the constraints statable per slot:
**hooks may overlap freely across the fan** — forced partition
manufactures misses — while **each owed act has exactly one owning
latch**. The second constraint is a transposition, performed
deliberately: § 7.4 states that exactly one checkpoint owns any
judgment, at the checkpoint tier; here the same discipline is restated
per slot, for owed acts and their latches. The law crosses a tier by
restatement, not by inheritance, because the two tiers' objects are not
the same object.

One corollary makes the § 8 measurement more than a key-space fact: a
case record's world-keyed revisit triggers — and the world-facing
premises in its falsification-list warrant — are **embryonic
belief-store records**, world-claims unpriced and unwatched inside the
case store's slots. The clean factoring is a design direction, carried
open in § 17: world-facing premises belong in the belief store as
watched claims, the case record holding wiring edges to them.

**The port calculus.** The fan schema's store × kind clause is a
calculus, not a gesture — its unit the **port**, a kind-level
admissibility slot for a latch type:

> **The port law.** A record's kind declares its **port set**: which
> latch types are admissible on records of this kind, each with an
> **obligation mark** — required, optional, or forbidden — and, where a
> corpus's evidence warrants it, a grammar-level constraint on what may
> fill a port. The declaration is **defeasible by warrant**: an
> off-declaration latch is admitted when it carries an explicit
> warrant, and a recurring off-declaration channel is the declaration's
> own miss stream, nominating widening exactly as the
> admissible-evidence map's bypass stream does (§ 11.1). Where
> occupancy evidence is thin, the declaration begins as a materialized
> projection of observed occupancy guarded by a **first-occupancy
> gate** — a latch type's first appearance on a kind routes through the
> human as a proposal — and hand-set obligation marks are earned, not
> presumed. Each latch instance carries its **own settlement grammar** —
> the evaluator that scores its fire. The record's effective
> falsification grammar is the **derived join over its dispositive
> latches** — derived, never stored (I3).

Four clauses unpack it. **Kind declares; the instance fills.** The port
declaration is schema-level, gated, closed-with-escape; the latch
instance is data-level, per-record, shape-checked only. What the record
kind governs is *which activation kinds can exist here* — a small
closed vocabulary — never the content of any one. **Declaration is
three-level**: the store's truth-maker fixes the default port profile;
the record's kind refines it; the record's subject binds the keys. Read
in port terms, § 3.2's trichotomy was already declaring fan shapes —
the belief store's dominant machinery is the watch and revisit ports,
the case store's the summary-scan and revisit ports, the duty store's
the consultation hook and the floor gate — and one deployment carries
the strongest concrete form: belief-store records with *no consultation
hook at all*, retrieval running entirely through a computed subject
index, the port declared as a non-field with the I5 argument attached
(no reader exists; the port reopens when one does). The coordinate
table's activation row (§ 14.1), which varies by family, is the same
law read columnwise. **Admissibility is state-indexed, not kind-indexed
alone.** A proposed record admits a different port set than an active
one; a settled record's watch ports close while its wiring edges
persist; a tombstone admits only the successor pointer. Lifecycle is
not a sixth axis of kind — it is a co-index into the same declaration.
**The genesis posture is the projection.** A projection can gate
*novelty* but cannot express *obligation*: a forbidden port never yet
occupied and a required port whose absence is a defect are both
invisible to an occupancy matrix, and only a declared mark catches
silent conforming drift under an already-occupied port, or the record
class born missing the watch its kind owes. The evidence that settles
how much declaration a corpus needs is therefore named: if its port
defects arrive as first occupancies, projection-plus-gate suffices; if
they arrive as conforming drift or owed-but-absent ports, marks earn
their admission — per mark, through the write gate, like everything
else (§ 14.5 carries the genesis clause).

One boundary case sharpens the calculus from inside deployment: the
same textual shape — "re-check when…" — is a governed latch on judgment
records and an explicitly latch-stripped advisory on observation
records, an advisory note-to-self and never a gated falsifier. Same
words, different store, opposite status — decided by the record's
class, not the field's shape. The property/latch boundary is not
lexical or syntactic; the kind declares it. One further property is
observed rather than designed: the calculus is reflexive. At the tier
where a latch is a record — the checkpoint — the record has a kind, and
deployed checkpoint governance already types each checkpoint by its
grounding class and derives its retirement trigger from it: a
corpus-join grounding retires with its store, a world-reference
grounding when the world absorbs the pattern, an oracle grounding with
its toolchain — the sharpest deployed instance of the fan's generic
retirement row, and a candidate for generalization across every
artifact family. Nor is the calculus store-local: its three-level
declaration holds on every leg of § 3.2's trichotomy — what
distinguishes prediction corpora is only where settlement authority
lives (the world settles), never the activation architecture. One
calculus, every leg.

**The reified fire.** Eligible to fire, firing now, and fired are three
states, and a corpus that conflates them loses control of its own
activation. Stated as law:

> **The reified-fire law.** A fired latch emits a typed **fire record**
> its named consumer disposes; the fire is an event in a ledger, not a
> state change in the record. Fired and discharged are distinct states,
> and the gap between them is owned — a fire that cannot name its
> disposer is a standing false alarm by construction.

One deployment runs the seam as constitutional law — a watch fire opens
an owner-disposed record and never flips status; the sole
status-mutation path runs through a disposed fire — and the evidence
state (§ 10.4) is the same discipline in the belief store: a
contradiction lands as display, and the record stays active until a
human disposes. The law's absence has a measured cost. In one
process-facing deployment, one record family's revisit conditions —
several hundred entries — carried not a single settled mark while the
same corpus ran settlement at other grains: the concept existed and was
never transposed, because no per-port law demanded it, and every
fired-and-addressed condition there is a standing false alarm the
scheduled walk re-reads. A hazard the same deployment met repeatedly —
a surfaced finding evaporating in the seam between checkpoints — is the
unreified fire's signature failure: findings fall through where fires
have no record. The fire ledger is the mechanical floor under "every
flagged finding reaches a terminal disposition." Like the edge/guard
fields, the ledger is stated as design: one deployment runs the fire as
law; none yet declares the ledger as schema.

A revisit trigger, being a latch, needs the full tuple — including a
lifecycle, where practice drifts furthest. The discipline is the
**structured trigger**:

> A revisit trigger is `{when, then, settled}`: **when** — the
> recognition condition, word-capped (a house convention, labeled as
> such) and self-contained; **then** — the instruction, stage-two only
> (§ 13); **settled** — absent while live, set **in the same commit as
> the settling change**. A partially-fired trigger **splits at
> settlement** into a settled entry plus a live remainder. Settled
> triggers leave the always-scanned surface by mootness.

Two operators do standing work. **Same-commit settlement** makes the
status flip and its cause atomic, keeping an always-scanned index
honest (a fired-but-unsettled trigger is a standing false alarm; a
settled-elsewhere trigger a silent one) — and under the reified-fire
law it is the degenerate case, where fire and disposition are atomic:
legitimate exactly where the disposer is the settling commit itself.
The motivating negative result is the sunset-clause literature's
(WFD/Agora, 2022, via secondary summaries): review triggers without a
forcing function have frequently failed to initiate the scrutiny they
mandate; same-commit settlement is the forcing function scaled to a
corpus. **The partial-fire split** has two clauses, one at each end of
a trigger's life. At authoring, a conjunctive condition is split per
conjunct up front, because a conjunct that can only fire inside a
compound trigger is unwatched in the strict sense. At settlement, a
partially-fired trigger splits into a settled entry plus a live
remainder — § 8's event-driven nominator at the trigger tier, forced by
partial satisfaction, and the residual repair for the conjunctions
authoring did not catch. The remaining clauses inherit standing
discipline: eviction keys on **mootness, never low salience** (§ 7.3);
the word cap inherits the caveat that thresholds are under-derived
(§ 16); and the `when` field is embryonically an edge + guard pair — a
deadline is an edge, its predicate a guard. The `then` field is bound
by a rule of its own: **the owed act is a typed reference to a named
act class — apply, re-adjudicate, re-derive, check, retire — never an
escape into arbitrary instruction.** A corpus whose activation surface
is procedural stops being able to reason about its own activation
exactly at the scale where it must; the settlement test (§ 13) polices
the same boundary at projection cells. Prior art: dynamic adaptive
policy pathways' signposts (Haasnoot, Kwakkel, Walker & ter Maat, 2013)
and assumption-based planning's signposts (Dewar, 1993/2002) supply the
{when, then} factoring but no settlement concept and no partial-fire
operator.

**Cascades.** Latches compose into a graph whether or not it is
modeled: wherever a latch's owed act can change state other latches key
on, the corpus has a **triggering graph**, and rules triggering rules
make termination and confluence undecidable unless someone declares the
graph (Aiken, Widom & Hellerstein, 1992). The doctrine's write
governance is its cycle breaker: owed acts that mint or modify latches
route through consolidation passes and the human gate (§ 7.4's minting
monopoly; I2), so cascade frequency is human frequency — the ungoverned
auto-write loop the doctrine already refuses is, among its other
failures, the unbounded-cascade case. The residue is the mechanical
floor: gates whose checked population includes gate configuration;
projections consumed by projections. Small — but a corpus that grows
its mechanical layer should run the acyclicity check over declared
consumer-edges as a lint before the first cycle ships rather than
after. The lint is stated as design, like the fields and the ledger: no
deployment yet declares its consumer-edges.

The tuple's shape, refined this far, is still not where the design
succeeds or fails:

> **The key-space law.** A latch is worth exactly as much as the
> governance of its key-space. Each key-space a fan draws on —
> work-shape, world-state, neighbor identity, the diff, competence
> signals — is a governed vocabulary with its own change control, or
> the latches keyed on it are decoration: firing on incident, rotting
> on rename, unshareable across corpora. The tuple's shape is not where
> the design succeeds or fails; the key vocabularies are.

The law is the governance half of § 4.1's legibility rule: there is no
gradient with which to repair an illegible key-space, and none with
which to repair an ungoverned one. Its sharpest external warrant is a
portability failure — the oldest deployed five-slot activation contract
separated its evocation, logic, and action slots cleanly, standardized
the shape, and failed at its stated goal of shareable knowledge
principally because its key-space was not governed: institution-local
terms sat inside the data bindings, so a structurally perfect hook
fired nowhere but home (HL7, 1992–; Hripcsak, 1994; § 15 places the
lineage). Aspect orientation
reached the same conclusion from the other side: pointcuts keyed on
incidental structure silently rot, and the field's remedy is to key on
a declared conceptual model instead (Koppen & Störzer, 2004).

Deployed corpora grade unevenly against the law, and the gradient is
informative. The world-state key-space is strongest where a typed fact
layer exists — there the watch predicate is machine-evaluable against
governed series, and the admissible-evidence map is computable *from*
the predicate set rather than declared beside it: where evidence
arrives as typed facts rather than narrated events, a separately
hand-declared map is a derivable structure stored by hand — I3's own
violation — and the declared map earns its keep exactly where the event
stream is narrative. Neighbor identity is governed wherever the
identity law (§ 5) is — stable identifiers are precisely a governed
key-space. The weakest space everywhere is **work-shape**: the
consultation hook's vocabulary, mostly free prose matched
associatively. The strongest deployed exhibit grades both ways at once:
one corpus keys its rule store's hooks into a gated, closed vocabulary
of routing terms — and already runs that vocabulary's miss stream,
recording an off-map line for any paid-off consideration no checkpoint
keyed — while sibling record families on the same shelves carry
free-prose read-when hooks. Split governance inside one corpus is the
per-type key-space audit's exact target: the governed space works and
instruments itself; the ungoverned spaces beside it rot silently. The
law has an authoring face, owned by the authoring register (§ 4.2) —
key on the presentation, never the conclusion; bias broad under
asymmetric costs; build from the shared lexicon only.

The fan buys four things unavailable while activation is one slot:
**per-type lifecycle law** (conflating them is how triggers come to
carry instructions and instructions come to leak authority);
**per-type key-space audits** (auditing "the activation slot" as one
thing cannot see one key-space colonizing another); **derivable
projection composition** — what a stage-one index prints per store
becomes a function of which latch types a reader must see and which
payload surfaces it must not be able to act on (§ 13); and a **finer
indictment vocabulary** — the edge/guard split separates
considered-but-guard-failed, which is routing working as designed, from
fired-but-not-applicable, which indicts the guard: two verdicts a
composite fires-when cannot tell apart (§ 7.4 carries the telemetry).
The fan's one world-facing row is the door to the store the next
sections walk: the corpus's model of the world.

## 10. The belief store: the corpus's model of the world

Of the three live-hypothesis stores (§ 3.2), the belief store is the one
whose truth-maker is the world — and run as such, it is the corpus's
world model. The term is borrowed under one boundary, drawn before any
machinery:

> **A world model, in this doctrine's sense, is a governed set of
> falsifiable commitments about an exogenous domain, held in legible
> text and calibrated through settlement** — not a simulator, not a
> learned transition function, not a probabilistic database.

The borrowed term is graded as § 17 grades every borrowed vocabulary —
function, never mechanism: the corpus claims the world model's *role*,
the maintained, calibrated representation of an exogenous domain that an
agent consults before acting, and none of the owning family's rollout
machinery (§ 15 positions the families). One refusal is constitutive.
The generalizer's own world model — provably present in any agent that
generalizes, and resident in the frozen model: rented, unversioned,
unreadable — is queried as inference and refused any truth-maker role
(I12). The corpus's world model is the *project's* faculty: owned,
auditable, and the only one that persists.

Read as a model of an exogenous world, the store's records carry the
three kinds of structure a model needs: spatial (the declared
world-property dimensions, the same axes the leaf lattice cuts, § 8),
temporal (deadlines, revisit triggers, settlement), and relational (its
edges in the corpus graph, §§ 5, 9). This section develops the record
machinery — the priced claim, the watch, and the evidence state
(§§ 10.1–10.5) — and the admission discipline a *conditioned* claim
must pass (§ 10.6). One claim, one price, one watch fan, one evidence
state: everything here is per-record. What the store acquires when the
records are many is population structure, and § 11 states it.

### 10.1 The priced claim

The belief store's write-side record: a domain belief frozen at entry —
the claim verbatim, a typed assertion, kill criteria, a deadline — and a
declared, dated reading of the reference the claim departs from, frozen
in the same commit: the claim's **price at entry**. The price is **a
frozen, provenance-carrying measurement of world-state at entry** — not
"the market's number" — carrying `source` and `as_of` beside the value.
A reference that cannot be measured honestly is declared categorically
or not at all — never manufactured to fill a numeric slot.

The slot carries a **reference class**, a closed vocabulary with the
standard escape (§ 7.5): **consensus** (a crowd, market, or expert
aggregate), **base-rate** (the historical frequency of the asserted
outcome), **persistence** (the current measured state carried forward),
and **incumbent** (the standing best result, frozen). Boldness —
departure from reference — reads naturally in all four classes, but its
units differ per class and must be declared with it.

Most of the construct is the forecast species (§ 7.3) evaluated at a
coordinate the case store never uses: the truth-maker is the world, not
the project's own execution. The reference-at-entry slot is the
genuinely new field: no other construct records an exogenous baseline at
freeze time.

### 10.2 Scoring

Skill is graded **reference-relative and resolution-graded**, never bare
hit-rate — "resolution" in Murphy's (1973) sense, distinguished on every
use from prediction-market *resolution* (settlement). The one-line
argument: **a naive hit-rate rewards sandbagging** — the
consensus-hugging forecaster scores perfectly and learns nothing
(Gneiting & Raftery, 2007). The incentive-clean shape is **per-claim
baseline adjustment of a proper rule** (Winkler, 1994): a reference
frozen per claim at entry is a forecast-independent term whose
subtraction leaves the optimal report unchanged. One caveat transfers
with its proper scope: forecasters optimizing *relative standing* report
more extreme probabilities than their beliefs (Witkowski et al., 2022) —
a caution for leaderboard use, not for fixed-reference skill itself.

What the priced claim adds to that literature is the record: claim,
falsifier, reference, and verdict are all authored inside one system,
the first three frozen in one commit before the world moves —
pre-registration supplies the freeze, proper scoring the grade, and
neither supplies the typed store, the write gate, or the lifecycle
connecting them. One channel stays open: the freeze closes claim-drift
but **not question selection** — the author also chooses which beliefs
enter the corpus; the honest posture names it open (§ 17).

### 10.3 Postdiction and transcription — the zero-price limit

A claim whose deadline predates its record — bright-line,
machine-checkable: `deadline < record_created_at` — is **born settled**:
the world already spoke. Its verdict is **transcribed** by an oracle
adjudicator: a machine-kind source reads the settled fact through the
graded falsifier and writes the verdict through the governed seam, every
ambiguity surfacing to the human instead.

The framing matters more than the mechanism: phrased as an *exception*
to I2, this becomes a loophole later work will widen. Two framings block
the widening. **The type distinction**: fact-transcription is not
adjudication — a postdicted claim was never a live prediction in this
corpus. **The derivation**: **transcription is legal exactly where the
claim's price was zero at entry** — reference reading and settled
outcome coincided at freeze, so the claim never bore epistemic risk in
custody. The deadline test is the mechanical *detector* of that
property, not the property itself: a live claim whose kill criterion
fires reaches price zero *during* custody, but keying legality on price
**at entry** — a frozen historical property no later event can change —
keeps it human-owed, however obvious the verdict has become.

One qualification ships with the derivation: a prose-only falsifier
carries zero *epistemic risk* but nonzero *evaluation cost*, and an
ambiguous reading partly *constitutes* the verdict — **zero price
licenses transcription only where evaluation is mechanical**.
(Prediction markets automate the *live* case by default; this design is
strictly more conservative.)

The derivation also closes the store theory from below. Postdicted
records are excluded from the skill score — reference and outcome
coincide, so departure is undefined. And a **fact is the price-zero
limit of a belief** — which is why the fact layer is transcribed, never
adjudicated, and why § 3 places it as the floor beneath the trichotomy's
legs. The fact/judgment boundary and the belief-store/fact-layer
boundary are one seam.

### 10.4 Falsification pressure — the evidence state

The **evidence state** is a live-computed reality-pressure axis on
every belief record. Three properties are constitutive: it is **computed
live and stored nowhere**; it is **orthogonal to lifecycle** (lifecycle
is what the corpus holds; evidence state is what the world is saying
— § 3's world/internal cut for a single record class); and **a
contradicted record stays active, displayed loudly, until a human
disposes** — the state variable the judgment seam between contradiction
and retraction presupposes. Doyle's truth maintenance gave every node a
computed label separate from the node's existence (Doyle, 1979) but
propagated to retraction automatically; this axis stops at display. In
deployment the axis has arisen independently more than once, converging
on the same shape.

The vocabulary, stated as design, is six tokens:

> `corroborated` · `rebutted` · `undercut` · `holding` · `unevaluated`
> · `unwatched`

The positive pole is **`corroborated`** — Popper's term, on purpose
(Popper, 1934/1959): a passing test fails-to-falsify and never confirms;
the axis has no `confirmed`. Contradiction splits into **`rebutted`**
and **`undercut`** — Pollock's (1991/2001) distinction between a
defeater arguing against the conclusion and one dissolving the
inference — a split earning its schema cost because the two route to
different human dispositions: revise the claim versus revise the
reasoning. `unevaluated` is preferred over "pending", which misreads as
pending-human-judgment — the other axis.

Pressed further, **rebutting and undercutting are two orders of
pressure, not two values of one scale**: rebutting is first-order — the
*level* on an outcome dimension moving against the claim; undercutting
is second-order — the *validity* of the level signal degrading while the
readings stand. Each watched dimension therefore carries a **{level,
validity}** pair. And validity degradation has no instrument
anywhere — `undercut` is the axis's unimplementable-without-new-machinery
value, said so plainly (§ 17 files the missing instrument).

A second constraint comes from § 13's itemized-never-net law:
**evidence state is per-watch — itemized — and the record-level token is
a derived, non-compensatory projection** (worst component plus a
conflict count) **or an explicit `conflicted` value with a mandatory
human surface** — never a lone net token, which is Simpson-vulnerable
across dimensions and compliable without opening the record.

Assembled, the axis's unified form, stated once and marked as design:
**one pricing axis per belief record, one named dimension per declared
world property — the watch layer's dimensions and the leaf lattice's
axes (§ 8) being the same axes. The entry price is the t0 vector of
reference readings (§ 10.1). The evidence state is the current itemized
pressure vector, each component a {level, validity} pair — rebutted is
level-against; undercut is validity-degraded. The verdict is the
per-dimension terminal settlement — a fully settled record retiring to
the fact floor (§ 3), a partial settlement forcing a leaf cut (§ 8).
Postdiction is the degenerate case where the t0 vector already equals
the terminal vector (§ 10.3).** The six-token display value is a
projection of this object, not the object.

### 10.5 Watch modes and the falsifier's floor

The machinery producing the evidence state: **machine-evaluable watch
predicates over a typed fact layer**, each carrying a declared **mode**
— the verdict authority of a true predicate, fixed at authoring time.
The modes are `falsify | corroborates | revisits`: a fire counting
against the claim; a fire that fails-to-falsify it (Popper's asymmetry —
never "confirm"); a fire that neither kills nor strengthens but
re-opens — re-opening authority inside the typed layer, which a
free-prose revisit line cannot declare. The deflation, stated plainly:
the floor/residue split here is the enforcement split (I10, § 6) at the
belief store's currency coordinate; only the mode field is new.

Two disciplines and one tension complete the construct. **The honest
escape is preferred over a precise predicate testing the wrong
quantity**: `unwatched`/`manual` is a better falsifier than a crisp
threshold on a surrogate — an easily measured proxy can be exactly wrong
(Prentice, 1989). **Twin predicates close under strict negation**: a
falsify leg and its corroborate twin are complements (¬ ≥ is <) — never
a same-value inclusive pair, never a hand-tuned epsilon. The tension is
carried, not smoothed: prediction-market practice pushes resolution
criteria *toward* machine-checkability, because ambiguous criteria make
traders forecast the resolver rather than the world (Aphyer, 2022).
Reconciliation: mechanize wherever the mechanizable predicate tests the
true quantity; where it cannot, recording `unwatched` is how the corpus
hears what the claim says about its own testability.

### 10.6 Pre-registered conditioning: the admissibility of a regime

The most valuable world-facing hypotheses are rarely flat. Their truth
is conditional on a regime; they conflict with a contrarian sibling; and
the regime moves — sometimes under the pressure of the hypothesis's own
adoption. One deployed corpus reports the forcing shape: two directly
contrarian strategy hypotheses were scored against a short seasonal
panel over a public field, and the focal strategy's measured edge
*flipped sign* as adoption of it roughly doubled — inviting a clean
crowding narrative and a conditioning meta-hypothesis. The panel then
broke the narrative: one transition showed adoption and edge
rising together — the reverse of crowding — and two periods at nearly
identical adoption showed opposite-sign edges, so no single-valued
function of adoption fits; the system carries hysteresis, a second state
variable, or a calendar effect a short panel cannot identify. A
conditioning variable read off the flip it would explain is not a
finding; it is the garden of forking paths wearing a regime clause
(Gelman & Loken, 2014). The discipline that survives the case is the
**condition-admissibility rule**:

> **A conditioning variable is admitted because a mechanism names it — a
> framework authority whose stated dynamics carry the variable — with an
> independent proxy in the governed fact layer, frozen and dated before
> the contradiction it would explain. A condition read off the flip it
> explains is refused: where no mechanism names a region, the honest
> move is wholesale re-adjudication of the warrant, not a conditioned
> child** (the store-dependent cut license, § 8).

The rule is pre-registration (Nosek et al., 2018) carried from claims to
*conditions* — a knowing inheritance — and it is one of the doctrine's
scoped novelty claims: a directed review failed to locate an
admissibility condition on conditioning variables in governed belief
corpora, agent memory, or world models for language-model systems
(§ 15). Its strongest external validation is disclosed as convergence,
never lineage — the deployments derived the rule from their own audit
failures before the review found its twins. The twins are exact at
clause level: the clinical subgroup-credibility instruments hold an
effect modifier credible only when specified *a priori* with its
direction, measured at baseline before the treatment and outcome it
would explain, and supported by a plausible mechanism rather than read
off the data (Sun, Briel, Walter & Guyatt, 2010; Schandelmaier et al.,
2020); economics pre-analysis plans pre-specify heterogeneous-effect
dimensions for the same reasons (Casey, Glennerster & Miguel, 2012;
Olken, 2015). Two fields where the experiment can rarely be rerun,
arriving independently at the same clause structure from opposite
directions, is the strongest validation available to a rule of this
kind — the convergent-evolution argument of § 15, one store deeper.
Five corollaries complete the rule, each blocking an observed failure.

**The effect is not a proxy.** The condition's proxy must be causally
independent of the claim's own predicted effect: a strategy's revenue
cannot proxy the regime that favors the strategy, and measuring crowding
by the degraded outcome it explains is circular. The surrogate-endpoint
literature carries the general warning — an easily measured proxy can be
exactly wrong — and the quantitative-finance literature
instantiates the discipline precisely: crowding must be measured with a
variable independent of the strategy's own performance, or "adoption ate
the edge" is unfalsifiable (Lou & Polk, 2022). One deployed audit caught
the violation live: an adverse print filed as *supporting* a claim was,
under the declared condition, evidence the condition itself was
*ending* — a contradiction-shaped edge hiding as vindication, surfaced
for re-disposition precisely because the condition and its proxy were
declared.

**The condition is not the claim.** The conditioning slot carries the
regime's *state*, never the payload's conclusion. A declared condition
of the form "while X holds, so Y is overstated" smuggles the assertion
into its own regime clause — un-falsifiable by the condition's
end-events because it was never a condition. The repair is mechanical:
the condition keeps the state; the conclusion returns to the payload.

**Basis is frozen per series.** A proxy is a measurement with a declared
basis — spot versus contract, announced versus closed, one methodology
versus another — and the basis is fixed at admission; a reading on a
different basis is a *different series*, never a splice. The corollary
has teeth because bases genuinely diverge: in one deployment the two
declared bases of a single reference series moved in opposite directions
across the same stretch — and which basis the condition lives on is
itself information. A single point on a series licenses no delta; two
same-basis points are the floor for any change claim.

**No single print falsifies a regime.** A regime claim is falsified by
events that end its condition — structural events: a policy act, a
failed refinancing, a demonstrated capability plateau — never by one
adverse reading, and the falsifier wording carries the breadth guard
explicitly: across the cohort, not one member's print; persistence, not
one period's draw. Conversely, the triggers key on *presentation* — how
the condition's end would first show up — never on the payload's
conclusion, so a session can recognize the fire without first believing
the claim (the authoring register's key-space face, § 4.2).

**A conjunctive condition falsifies per conjunct.** A condition of the
form *A and B hold* ends when either conjunct ends, so its falsification
surface is authored split — one trigger per conjunct's end — because a
single trigger demanding both ends at once quietly converts *or* into
*and*, and a conjunct whose end can only fire inside a compound trigger
is unwatched in the strict sense. The per-conjunct split is the
partial-fire discipline (§ 9) as an authoring obligation; the
settlement-time split remains the residual repair for the fires
authoring did not anticipate.

Where no honest proxy exists, the watch discipline of § 10.5 governs
unchanged: an explicit `unwatched` with the unblock named — what series,
on what basis, would make the condition readable — outranks a precise
predicate on a surrogate that is exactly wrong (Prentice, 1989). In
deployment the refusals proved as load-bearing as the admissions: no
watch was minted where the only candidate was a level predicate on a
single series, where a second watch would double-charge a series another
hypothesis already watches — each owed act has exactly one owning latch
(§ 9) — or where no governed series existed at all; each refusal
recorded, each a first-class outcome of the route-before-mint ladder
(§ 7.4).

A claim admitted this way is still one record. The store's remaining
structure is what the records make together.

## 11. The belief population: kinds, calibration, quantification, audit

§ 10 treats the belief store record by record. Run at scale against a
live domain, the store acquires population-level structure the
per-record machinery does not determine: hypotheses of *different kinds*
demand different falsification machinery; hypotheses *interact* — one
conditions, overrides, or contradicts another; and the store's schema
itself — which kinds exist, which evidence bears on which — is a
hypothesis about the domain, exposed to its own falsification pressure.
This section states that structure: the kind calculus, the two-timescale
calibration regime it forces, the quantification boundary, and the audit
that closes the loop. The evidence is the world-facing deployments run
at population scale — experience reports throughout, per § 1's method
statement; where the corpora's independently-conducted designs
converged, the convergence is reported as such, and a construct observed
in only one is marked.

### 11.1 The kind calculus: three axes, one selector

Applied to the question *what kind of judgment is this?*, the
truth-maker discipline (§ 3.2) — one axis, one question, one
truth-maker — splits the intuitive notion of a hypothesis's **record
kind** into three orthogonal coordinates. A judgment carries one value
on each; this is why a flat multi-tag "kind" field feels natural and is
a category error — the intuition detects a *product*, not a set:

| Axis | Question (its truth-maker) | Cardinality | Governs |
|---|---|---|---|
| **Falsification grammar** | what shape of world-fact contradicts this? | single-valued | the assertion payload's shape (constitutive); the declared admissibility relation over latch types and settlement grammars (the port law, § 9) |
| **Subject ontology** | what world-item is this about? | multi-valued | the activation *target* |
| **Order** | does it press on world-items, or on other judgments? | single-valued, **derived** | the activation *direction* |

The grammar axis's scope is stated exactly, because its two halves land
at different strengths. The payload half is single-valued and
constitutive: a cohort-comparison claim, a regime claim, and a base-rate
claim assert different shapes, and the shape is the union discriminator.
The activation half *declares* rather than enumerates: which latch types
and settlement grammars are admissible on records of a kind is a port
declaration (§ 9) — per-corpus and defeasible by warrant — and the
record's effective falsification grammar is the derived join over its
dispositive latches, admissibility co-indexed by lifecycle state. A
single-valued grammar — one record kind, one homogeneous watch
vocabulary — survives as the homogeneous-fan special case. The deployed
corpora split on exactly this freedom, and the split is reported, never
smoothed: one kind-separates watch occupancy — the declaration living in
schema prose, enforced by no gate — while the other's watch-kind ×
record-kind table cross-cuts heavily under two declared truth-makers, so
that record kind and watch kind are orthogonal axes there. Both satisfy
the floor — the kind governs which latch types its records may carry;
whether grammar-level constraints bind into ports is each corpus's own
declaration, adjudicated through its exception stream.

The load-bearing consequence: **activation direction is a function of
grammar and subject.** The kind selects which way a judgment presses —
down onto a cohort's facts, at a named condition's end-events, or
sideways onto other judgments. A cohort-comparison hypothesis carries
latches keyed to member-level outcome records; a regime hypothesis
carries latches keyed to the events that would end its declared
condition; a meta-hypothesis — one whose falsifier is the behavior of
*other hypotheses* — carries latches keyed to the hypothesis population
itself. Nothing about that routing is decoration: it is the belief
store's instance of § 4's two-stage attention, expressed as schema.

The order axis is deliberately **derived, never stored**: what a
judgment presses on is readable off what its edges point at, and a
stored copy of a derivable relation is drift by construction (I3). In
both deployed corpora the meta-hypothesis order is held open as an
escape channel rather than pre-populated — an arrival route honest about
its emptiness, because classes minted ahead of instances are priming
(§ 7.5).

Not every classification deserves an axis. The discriminator, stated as
a lint: **a classification is a type — declared, gated, closed — iff it
does falsification-grammar work**: it changes the assertion payload's
shape or the declared admissibility relation over latch types,
settlement grammars, or evidence classes. Otherwise it is a tag —
navigational, escape-carrying, ungated. The one-line test: if grouping
by a tag ever moves a disposition, it was a type all along — a tag doing
verdict work is duty conflation (§ 12.1) in classification clothing. One
deployed corpus ran the test in both directions: an outcome-payload
discriminator passed — its truth-maker is literally *which typed
assertion payload can express and score this* — and was promoted to
schema; a positional grouping field failed (it drove no gate, no
disposition, no wiring) and stayed a tag.

The grammar axis is a **discriminated union over the entry contract, not
an inheritance hierarchy**. Each grammar member *defines* its own
falsification method — a scored comparison, events ending a declared
condition, a frequency — and the truth-maker discipline forbids a shared
falsification vocabulary across record kinds: one delineation copied
across axes is the canonical drift shape (§ 3). The only shared base is
the pentad itself — the entry contract (§ 6), a contract, not a
superclass — and the only genuine IS-A order in the system lives
*within one judgment's outcome space*: the refinement order of its
conditioned narrowings (§ 8), never across the kind set. The
distinction matters because § 8's lattice invites the misreading: the
leaf lattice is intra-record — one judgment's outcome space,
partitioned; the kind axes are inter-record — coordinates over the
population. The superclass instinct is right for leaves and wrong for
kinds.

The deepest placement question — is a hypothesis's record kind a
property of the record or part of its definition? — resolves by
observing what the kind *does*: **a falsification grammar is the
selector into the admissible-evidence map.** Each grammar member owns a
declared relation from event kinds to itself — which classes of world
events are admissible evidence for claims of this kind — and that
relation is what the ground-facing matcher consults when a new event
arrives: the event's kind keys into the map; the map proposes which live
hypotheses the event bears on; the human disposes the bearing. The kind
therefore lands at schema level (constitutive, gated,
closed-with-escape) while the subject axis lands at data level: a
multi-valued property feeding the activation index, its inverse
computed, never stored.

Two properties of the **admissible-evidence map** are design. First, it
is **a proposal filter, never a hard gate**: the human may attach
evidence the map did not propose — the map routes attention; it does not
adjudicate admissibility (I2 at the wiring layer). Second, precisely
because attachment is free, the map acquires its own falsification
stream: **owner attachments that bypass the map are the map's miss
records.** In one deployed corpus a family of regime hypotheses
accumulated the majority of its lived evidence through event kinds the
map excluded — a handful of recurrences on each of the two strongest
channels — the map's own revision trigger firing in spirit: the blocked
act is the *proposal*, and recurrence of out-of-map attachment nominates
widening the map, exactly as escape recurrence nominates a vocabulary
member (§ 7.5). One attachment is an anecdote; a recurring channel is a
schema defect.

Declaration order follows the one proactive exception of § 14.5 —
schema precedes records: **the axes and the selector precede the
members.** A wrong or missing axis is the silent, expensive mis-location
a recurrence counter never catches — every instance forced to average
two questions into one token — while a missing member merely accumulates
visible escapes. So the axis structure and the admissibility relation
are declared at genesis, honest about emptiness; the members stay
route-before-mint.

### 11.2 The two-timescale calibration regime

A world-facing corpus is a **structure/parameter split across two
timescales**. The *structure* — the kind axes, the vocabularies, the
admissibility maps, the graph topology — is discrete and combinatorial:
a huge hypothesis space with no smooth gradient, genuinely data-hungry,
as structure learning is throughout the graphical-model literature. It
is calibrated slowly, at the consolidation passes where the human is
present (§ 7.4), against the corpus's **large-N world substrate** — the
typed fact layer and event ledger, which in a world-facing deployment
dwarf the hypothesis set by orders of magnitude. The *parameters* — the
individual judgments, their tokens, thresholds, and dates — are the
few-shot layer: authored per claim within the frozen structure,
tractable at small N exactly because the structure they instantiate was
fit elsewhere.

This dissolves an apparent tension the world-model case makes acute: the
project authors *few* claims yet claims credibility against a domain
that demands *large* N. The resolution is that the large-N calibration
is on the world, not the claims. The fact substrate — thousands of
settled outcomes, full-population panels, filing series — is the
training corpus for the *structure*; the claims are the
deliberately-few, human-authored queries scored against it. The division
of labor is meta-learning's (learn the inductive bias across many
instances; adapt per task on a handful), imported as vocabulary rather
than mechanism (§ 17). The probing literature supplies a sharp external
statement of the failure the split answers: a foundation model can
predict orbits to high accuracy while implying a nonsensical force law
when probed for the governing structure — predictive skill on the task
does not certify the frame (Vafa et al., 2025). Settling the structure
separately from the judgments, against a substrate orders of magnitude
larger, is the corpus's answer to exactly that failure.

**The freeze is pre-registration.** The structure is frozen per episode,
as late as the settlement calendar allows — to capture the most recent
world-state, not from any intrinsic optimality of the freeze point
(§ 14.4's plan-on-policy discipline applied to schema). The freeze
converts each subsequent world-print into an honest out-of-sample test:
re-fitting the frame per judgment is the garden-of-forking-paths failure
(Gelman & Loken, 2014), and the freeze is what blocks it. This is a
second freeze on a different object than § 10.2's: the claim-freeze
closes claim drift, the structure-freeze closes frame drift, and neither
closes question selection — the channel § 10.2 names open stays open
here.

**Each settlement is two verdicts on two objects.** For the *judgment*
it is a test: a ledgered, immutable adjudication, scored once, never
re-scored. For the *structure* it is validation: *systematic* miss —
never a single one (I11) — is the signal that the frame is wrong,
re-opening the slow loop. The two roles cannot contaminate each other
because of the write law (§ 5): a structure revision supersedes forward;
it never rewrites a ledgered verdict. Append-only supersedure is the
firewall that lets one settlement be test-for-the-judgment and
validation-for-the-structure without the machine-learning hazard of
tuning against one's own validation set. And because the hold-out is
temporal and non-stationary — the next season, the next quarter, never a
random split — it is a *stronger* structure-drift detector than a random
partition: structure error usually manifests as the world moving, which
a same-period split cannot see. Both halves of that argument have
independent external convergence: the settlement stream is the
concept-drift detector on the schema, in the drift literature's exact
sense (Gama et al., 2014), and the forecasting-evaluation field has
converged, for its own contamination reasons, on exactly the
future-only, temporally-held-out design — post-training-cutoff question
sets and continuously refreshed future-question benchmarks (Halawi et
al., 2024; Karger et al., 2025).

**The miss triage.** Every miss is triaged **parameter-miss versus
structure-miss**, and the triage is the same orthogonality question as
revision routing (§ 7.5): a parameter miss is a residual *within* the
frame — right grammar, wrong token or date; supersede the judgment,
cheap, few-shot — while a structure miss is an error the frame *cannot
represent*: the escape pile grows, misses correlate orthogonally to the
axes, or — the sharpest detector either deployed corpus found — **a
verdict moves while every stated falsifier stays quiet**. That last
signature deserves its own sentence, because it is the world-model
instance of the floating-entry failure (§ 6) caught live: if a claim's
evidence state changed and no declared watch, trigger, or falsifier
fired, then either the falsification surface was mis-specified (drift —
a falsifier defect) or the taxonomy itself moved under the claim (a
structure revision — legitimate, and loud). A per-supersedure audit
that asks *what moved, and did anything declared fire?* routes every
such event to its timescale; a deployed instance of the audit
attributed a verdict change to a vocabulary re-grade — the instrument
moved, not the world — a category no naive falsifier accounting
contains.

### 11.3 Quantification is a projection that nominates

Projecting a body of belief onto a target decomposes into four acts —
select, predict, quantify, combine — of which the refinement lattice
owns selection natively and none of the rest (§ 8). Where a number is
wanted — a per-cell estimate, a combined read across surviving
hypotheses, a next-period regime probability — it enters as a **computed
projection**, never as stored record authority, obeying five disciplines
the deployed corpora converged on. Pre-register the conditioning
dimension from a mechanism (§ 10.6). Pool rather than partition for the
estimate: partial-pooling shrinkage is the risk-dominant posture in the
regimes these estimates inhabit (James & Stein, 1961; Efron & Morris,
1975) — the formal dominance theorem binds at dimension three and above
under squared error; what is imported is the direction, not a theorem
about every small-N setting — and report honestly wide intervals.
Combine hypotheses, if at all, by a predictively-scored, partially
pooled gate in the M-open posture — stacking of predictive densities
rather than Bayesian model averaging, because when no single hypothesis
is globally true (each ruling a region), model averaging asymptotically
concentrates all weight on one model, which is exactly wrong for regime
mixture (Yao et al., 2018; Yao, Pirš, Vehtari & Gelman, 2022). Price
unresolved cells as intervals or credal sets that honestly span both
signs (Walley, 1991) rather than manufacture a point. And disclose
every component — itemized-never-net (§ 13) at the estimate — the
combined read nominating a disposition and never driving one.

The tension is named rather than smoothed: the best combiner *produces a
net*, and the doctrine forbids a net from settling anything. The
resolution is the constitutional one (§ 2) — **the net may be shown; it
may never settle; the human disposes** — and the tension is permanent,
the price of keeping the human as the optimizer. A system that stored
the fitted regime model as record authority and let its posterior settle
dispositions would be a better statistician and would no longer be
running this doctrine; at small N against a contested regime, the
deployed corpora report the human-disposed, itemized,
computed-not-stored posture not as a handicap but as the honest reading
of how little the panel identifies. The forecasting literature's state
of play is consistent with the posture even on raw accuracy: on
continuously settled future questions, professional human forecasters
have outperformed every language-model team entered against them across
the public benchmark's settled comparisons (Karger et al., 2025;
Metaculus, 2024–2025), and language-model forecasters are measured to
violate the elementary probabilistic consistency a settling net would
presuppose (Paleka et al., 2024) — observations of a moving field, cited
for the settlement discipline they share, never as a static gap to lean
on.

### 11.4 The falsification-surface audit

The population forces its own instrument. A flat claim is audited by its
watch fan (§ 10.5); a *conditioned* claim has a falsification surface
with more ways to rot — the mechanism can fail to carry the condition,
the proxy can be circular or basis-drifted, the trigger fan can
under-cover the conjuncts, the evidence ledger can mis-carry bearings —
and a periodic, per-claim **falsification-surface audit** walks each
leg. Distilled from a deployed instance over a family of regime
hypotheses, the legs are:

1. **Mechanism** — does the cited authority actually carry the
   conditioning variable, or does the real mechanism live elsewhere (an
   uncodified heuristic, the record body's own arithmetic)? A condition
   whose mechanism has no home is a floating entry in the making; the
   repair routes the mechanism to a home, not the condition to the bin.
2. **Proxy** — does an independent, basis-frozen, governed observable
   exist per conjunct? Is anything offered as a proxy actually the
   effect?
3. **End-events** — does each declared falsifier key on the condition
   ending? Is the benign end (the claim retiring *right*) represented,
   or only the loud one?
4. **Trigger language** — does each trigger fire on presentation, with
   breadth and persistence guards, without requiring belief in the
   payload?
5. **Conjunct coverage** — is every conjunct's end independently
   watchable, or does a compound trigger fuse them?
6. **Ledger coherence** — do the accumulated evidence bearings respect
   the condition/effect distinction, or is condition-weakening evidence
   filed as support? Are events arriving through channels the
   admissible-evidence map excludes (§ 11.1 — the map's miss stream)?
7. **Honest residue** — where the condition is unwatched, is the
   unblock named?

The audit is retroactive-as-check, not forking-paths suspicion, when the
audited conditions predate both the discipline and any contradiction — a
distinction the audit header records, since an audit performed after an
adverse print is itself a selection event. And the audit's output obeys
the constitutional grammar end to end: every finding lands as a proposal
row the owner disposes; the audit applies nothing (I2); refusals are
recorded beside repairs.

Population-level, the audit legs aggregate into the schema's own health
signals: recurring mechanism-leg gaps indict the authority roster;
recurring out-of-map arrivals indict the admissible-evidence map —
widened on recurrence, never per instance; and the census of
region-bearing versus basis-free contradictions gates the refinement
lattice (§ 8's store-dependent cut license). The world model audits its
schema with the same machinery the schema uses to audit the world — one
loop, two directions.

Every instrument in this section and the last answers to the world. The
remaining live store answers a question the world never asks — whether
the corpus's own obligations actually reached every site they bind.

## 12. The duty store: propagation machinery

The duty store's live question — *did you actually do it, at every
site?* (§ 3) — is about propagation, not correctness. Its machinery
develops in five movements — the conflation that motivates the store,
the discriminator that decides how its structures are built, the
register that is its dominant instrument, the population kinds that fix
the register's shape — and closes on the duty class that completes
§ 7.4's triple: the question tier.

### 12.1 Duty conflation

**Duty conflation** is a record class whose payload slot is filled from
two stores at once — canonically, a case record carrying a standing-duty
payload: a retrieval-key summary grown into a present-tense obligation
binding future work. The root is structural: a shear between two
lifecycle disciplines. A case record is *frozen* — immutable,
superseded-never-edited (§ 5; Nygard, 2011); a duty is *amendable* —
re-audited as sites appear, its adoption state changed in place. One
record class cannot honor both lifecycles: it either freezes the duty
(adoption state silently rots) or amends the case (the evidence
discipline breaks) — § 3's deontic/alethic distinction reaching down to
filing: a modality error, not taste.

Misplacement is *progressive*: observed in deployment, retrieval key
becomes duty sentence, the sentence accretes per-rule mechanics, child
records escape the class — ending as an adoption register in case-record
clothing, with none of a register's instruments and all of a case
record's constraints. The consequence: a projected duty sentence in an
always-scanned index is an authority leak (§ 13) — observed in
deployment as rule cells complied with unopened. Conflation is the
generator; the leak is the symptom.

The decision-record literature has the symptom, not the mechanism
(Zimmermann, 2023); the explicit counter-position — standing constraints
as a *subtype of decision* (Kruchten, 2004) — is refused: they are a
different store. The remedy's precedent is institutional: when a case
pile grows rule-shaped payloads, mint a separate distilled-rule store
with back-pointers — the American Law Institute's Restatements — never
enrich the cases; though the Restatements never track adoption, leaving
"did you actually do it?" unasked.

### 12.2 The derivability discriminator

How a duty structure is built is decided by the derivability clause of
I3 (§ 6):

> **A ledger or register is hand-authored iff its load-bearing relation
> is un-derivable — human triage over sites with no textual edge to the
> rule. Where the relation is already textual or citational, the same
> structure must be a computed projection — never a hand-maintained
> copy.**

I3 alone states one direction — derivable ⇒ projection; the clause adds
the converse as an admission criterion, without which I3 would refuse
every legitimate hand register. Two scope amendments: derivability
selects a structure's **mode, never its existence** (whether the
relation deserves tracking at all is I5's question); and the derivable
branch is two modes — regenerated on read, or **materialized-and-gated**
(committed, its regeneration verified mechanically so it cannot silently
drift).

The clause resolves to opposite artifacts in two worked design cases.
**Where the load-bearing relation is already textual** — a
machine-recoverable citation — a hand register over it is drift by
construction; the correct artifact is a computed inverse index wired to
a standing consumer, or nothing at all. **Where the load-bearing state
is the absence of a decision** — the `unchecked` cell — there is nothing
to derive it from: a machine can track adoptions that happened; it
cannot represent the un-propagated gap. There the register is
hand-authored and human-disposed.

The strongest external anchor is the Kubernetes spec/status split —
authored `spec` as un-derivable intent, computed `status` never
hand-written (Kubernetes documentation, *Controllers*) — lifted here
from field level to artifact existence. No located source states the
selection rule itself (§ 15).

### 12.3 The adoption register

The duty store's dominant structure: a hand-authored, per-site
applicability state store — one row per site, each carrying a token from
a closed vocabulary, `adopted` · `adopted (partial)` · `checked-N/A`
(examined; inapplicable, with the reason) · `unchecked` (judged a gap,
not yet closed) — an anchor on every adopted row and a **mandatory
carry-reason on every unchecked cell**, without which "judged a gap" is
indistinguishable from "not yet read." Triage is human-disposed; a gate
may check that every cell is triaged, never that the judgment was right.
The value concentrates in negative space: an all-adopted register has
found nothing.

The closest external analog, the ISO/IEC 27001 Statement of
Applicability (ISO/IEC 27001:2022, clause 6.1.3(d); compare the scope
statement of ISO 9001:2015, clause 4.3) — per-control, hand-authored,
justification mandatory, audited — proves by existence that
applicability cannot be computed, but supplies no criterion for when to
hand-author versus compute; § 12.2 is that criterion. Two extensions
belong in the vocabulary: an **inherited** disposition (satisfied by an
underlying layer — neither adopted nor exempt) and **conditional
applicability** computed from a declared predicate. The register's own
failure mode, disclosed: ceremony and blanket justification;
countermeasures are renewal legs and modular justification — a register
without a renewal leg is a snapshot wearing a register's clothes. Last,
the nearest authority reconciled: "a rule is distinct from any
enforcement defined for it" (Business Rules Group, 2003) — enforcement
*mechanism* stays separate (I10); adoption *evidence* co-locates,
because "did you actually do it?" is the rule's own live question.

### 12.4 Population kinds: spatial, temporal, relational

A duty binds over a population, and the population's **kind** is a
design variable: it fixes the register's shape and the dominant failure
it exists to catch — sites, occurrences, pairs (the duty store's face of
the property triad, §§ 8, 10).

| Kind | Population | Structure | Dominant failure |
|---|---|---|---|
| **Spatial** | sites — boundaries, stores, record classes | the per-site triage table (§ 12.3) | the `unchecked` cell |
| **Temporal** | occurrences — every session or moment whose shape matches the hook | an attestation stream: per-occurrence record lines plus presence gates | the silent non-consultation |
| **Relational** | typed artifact pairs under a declared relation schema | the complement audit: the edge set plus its enumerated complement | the absent edge — and worse, the absent pair |

**Spatial duties** bind at sites; their machinery is § 12.3 entire —
the adoption register is the spatial kind's native structure, with the
`unchecked` cell as its dominant failure. The paragraphs below develop
the two kinds that shape does not fit.

**Temporal duties** bind at moments: at every occurrence of this shape,
consult the authority, walk the checkpoint, leave the record line. The
structure is a *stream* — append-only attestation lines with presence
gates — ledger-shaped where the spatial kind's triage table is
register-shaped (§ 5's axis). The deployed instance is a hand-authored
roster of checkpoints walked at fixed points in the session loop — the
session's query plan promoted to a first-class artifact (§ 8). The
checkpoint schema behind such rosters carries a **typed authority
range**: its authority slot is filled from a closed set — `store` |
`oracle` | `record` | `source-route` | `vocabulary` |
`none-with-adjudicator` — so that every duty class of § 7.4's triple is
expressible in-schema rather than riding a stretched slot; § 12.6
develops the class the last values exist for. The kind's honest limit:
a presence gate checks that an attestation exists, never that the
consultation happened — the **silent non-consultation** reaches the
system only through the steer channel (§ 7.1). Floors, permanently
(I16). Checkpoint bodies obey the settlement test (§ 13); the
discriminator splits the roster internally; price-fillability (§ 3)
confirms the store assignment. Checkpoints are minted by **credit
assignment at the checkpoint tier**: the steer is the loss signal;
minting asks which checkpoint would have caught this, *if catchable at
all* — the slot-factored backward pass (§ 7.4) aimed at the checkpoint
tier, "not catchable" the noise-filter outcome (I11) — and the human
gates every mint.

**Relational duties** bind over the corpus graph itself (§ 5): typed
artifact pairs under a declared relation schema, the schema typing the
edges. The register is a **complement audit** — the edge set plus its
enumerated complement — and the complement is where the law lives: **a
register can only triage edges someone enumerated, and a wiring miss is
by definition an unenumerated pair.** The pair population is quadratic
and not listable, so the audit advances by **frontiers** — in the
graph-search sense: each names a boundary along which the unexplored
pair space is entered. The **diff frontier** (missing edges are
overwhelmingly born with new artifacts — a close-phase machine walk
over what a session touched catches the dominant production channel);
the **read frontier** (a human reader trips over a missing citation;
the miss arrives as a steer); and the disclosed residue, the **dormant
pair** — two old artifacts whose relation *became* true later, reached
by neither frontier; only a scheduled census, or a contradiction
failing to propagate, detects it. Absent-edge counts are floors,
permanently. The relation schema is itself a vocabulary under the
closed-set discipline (§ 7.5), one truth-maker per edge type: a
**mechanical** truth-maker gets a coherence gate with a *derived*
required-pair set; a **judgment** truth-maker gets the frontier latch
pair — the machine proposes candidate edges, the human disposes the
bearing, I2 intact at the wiring layer.

### 12.5 Collapse and register, orthogonal

Two operations over one multiplicity look alike and are opposites.
**Consolidation de-duplicates the settlement liability**: a re-check
condition copy-pasted across records is a double-settlement hazard and
collapses onto the one owning record. **The register makes the
surviving, legitimate multiplicity navigable**: adoptions are not
duplicates — each is the rule made real at a different surface — and the
register is their index. Collapse without the register loses
navigability; the register without collapse keeps a settlement hazard.
Different relations, different instruments, both needed.

### 12.6 The question tier

The roster of § 12.4 is consultation-dense: checkpoints whose duties
are judged against a store, an oracle, a vocabulary. One duty class of
§ 7.4's triple remains — the checkpoint with no consultable authority
at all — and it is not a marginal case the schema merely tolerates but
a class the doctrine's foundations predict. T1 (§ 3.1) splits the
generalization function between the human at write time and the frozen
model's in-context learning at read time. The consultation exercises
the corpus's cached judgment; the lens exercises the outsourced
generalization. A close-of-work question with no answer store behind it
— what did this change make false? what else is true here? — is not an
anomaly at the doctrine's edge; it is the read-time half of T1's
bargain, running everywhere a corpus puts an open question to its
model, and unclaimed by any construct so far.

The instability practitioners report in such questions — without an
authority, the default authority is the model — is real, but it is
T1's accepted instability, and the write side already contains it: the
answer to an open question is self-noticed signal, lowest-trust by
I12, and nothing it proposes becomes true without adjudication. The
same containment covers the questions themselves: fan composition is a
write and routes through the gate like any write (I12) — a model may
*propose* an angle, and the proposal's warrant is an instance. What no
store supplies is the read-side discipline — which questions, in what
form, forcing what contact, measured how. That discipline is this
subsection.

> **A lens** is a typed question walked against an item: ⟨**angle** —
> the question paired with its counterfactual (the contrast law, § 6) ·
> **externality** — the strongest contact outside the answerer its
> answer must make · **product** — the answer-shape, which must force
> contact with the item and never substitute for judgment ·
> **consumer** — the adjudicator of the answer, never the answerer ·
> **lifecycle** — the crystallization law's variance test (§ 7.4)⟩.

One placement rule governs everything downstream, because the
confusion the construct invites concentrates exactly here. **The
placement law**: a lens is a **duty class, never an artifact class**. A
lens is always hosted — by a checkpoint whose duty it becomes (a
**lens-checkpoint**, its authority slot honestly reading `record` or
`none-with-adjudicator`), by a dispatch template, by a directive's
counterfactual pair. Minting a lens never mints a new record kind; it
fills a host's duty slot with a question. The slots follow: a lens
occupies its host's payload slot, declares no ports of its own, and its
activation is the host checkpoint's latch — the fan (§ 9) belongs to
the host, the question to the duty. The duty-class triple (§ 7.4) — no
judgment residue, gate; consultable authority, consultation; neither,
lens — then closes the checkpoint space from this end: a checkpoint
whose consulted authority never existed is not defective. It is a lens.

The intuitive repair for the lens's instability is structure — more
form, tighter answer shape. The cross-field evidence refuses the
intuition with one of the sharpest negative results in the record: the
intelligence community's most-structured analytic instrument
(hypothesis-by-evidence matrices, closed marks, an integration rule;
U.S. Government, 2009) multiplied process compliance while *collapsing*
the base-rate use it was built to protect, leaving accuracy no better —
by some measures worse — than unaided judgment (Dhami, Belton & Mandel,
2019; Mandel, Karvetski & Dhami, 2018). Structured form let procedure
stand in for the judgment it was built to structure. The same inversion
is measured in frozen models: an output schema that forces the answer
field before the reasoning costs double-digit accuracy (Tam et al.,
2024). Shape is a lever with a sign. What grades lens reliability,
convergently across every surveyed field, is **externality of
contact** — how much the answer is forced to touch something outside
the answerer — and at the top of the axis the evidence forks on the
lens's purpose.

An **adjudicative** lens — is this right, compliant, real? — needs an
external authority, because the answerer cannot be it: intrinsic
self-correction without external signal degrades the reasoning it
revises, and oracle feedback reverses the loop's sign (Huang et al.,
2024); expert judgment becomes reliable through scoring against seed
questions with known answers, fewer than a third of individual experts
being statistically accurate without it (Colson & Cooke, 2018); and a
sampled written principle improves critique-and-revision most for the
*smallest* models (Bai et al., 2022) — the written vocabulary supplying
content the answerer lacks. A **generative** lens — what else is true
here, what could fail, what is missing? — is *harmed* by a supplied
answer, which substitutes for the generation it exists to provoke: a
generic elaborative question beat a provided explanation on recall by
nearly two to one — the same margin by which it beat nothing (Dunlosky
et al., 2013); across sixty-nine measured effects, self-explanation
prompts lose half their effect when an instructional explanation is
supplied beside them, the decisive moderator being the *angle* rather
than the content (Bisra et al., 2018); and the after-action-review
tradition, whose measured effect is largest exactly where intrinsic
feedback is absent, doctrinally *forbids* grading and defines its
questions as having no specific answer — an explicit refusal of an
answer-store, by doctrine, in a generative instrument (U.S. Army
TC 25-20, 1993). Both purposes are served by the tier between: forced
contact with an external record — the answer must cite, enumerate, or
read a value off the item or the world. The checklist literature's
counter-design demands a response that carries the value of the item,
never a bare "checked" (Degani & Wiener, 1990), and question form
alone — no store, no aggregation — produces some of the largest
calibration gains in expert elicitation (Haran, Moore & Morewedge,
2010). The fork dissolves the default-authority worry into a design
rule:

> **The externality law.** Every lens forces the strongest contact
> outside the answerer its subject affords — a record read, an artifact
> cited, a source class grounded against — and declares the residue
> where the answerer is the authority: the enforcement split (I10),
> transposed to elicitation. What the contact may *supply* splits by
> purpose: an **adjudicative** lens terminates in an authority — store,
> oracle, vocabulary — never in the answerer; a **generative** lens
> touches the item and the record but is never handed an answer. Which
> contact the subject affords is set by its truth-maker: a lens whose
> product the world settles grounds against its declared authority
> class and may not terminate in the model; a self-facing lens may
> terminate in the model, with an unstaked adjudicator downstream.

The truth-maker clause is distilled from deployment experience: in one
corpus, world-facing reconnaissance lenses are routed into external
sources while its retrospective lenses — whose subject is the work just
finished — are bare, and the split tracks § 3.2's store partition
exactly: the same axis that assigns a record its store assigns a lens
its tier. One clause covers the mixed duty the deployments actually
run — elicit, then adjudicate what was elicited (a deployed retention
checkpoint chains exactly this way: an invariant elicited, a verdict
rendered). The chain is legal iff the adjudicative leg ends outside the
answerer — in an authority where one exists, in a downstream unstaked
adjudicator where none does, whichever the facing affords; a chained
duty whose verdict terminates in its own elicitor has fused the two
purposes the fork exists to separate.

**The routed lens, worked.** The strongest deployed form of the middle
tier is a reconnaissance fan over an incident surface: a handful of
orthogonal angles, each shipped with a counterfactual naming that
angle's characteristic over-claim, and each terminating in a per-lens
routing table into an external authority class — release notes and
vulnerability feeds for one angle, a dependency's status surface for
another — with a source-weighing rule (primary status surfaces and
exact-version changelogs authoritative; forums corroboration only) and
a standing disconfirmation duty: one query aimed at refuting the
correlational read before it is handed back. A lens returned without
its grounding call is declared defective. What the routing supplies and
what it withholds is the design: the world hands the lens *evidence*,
never the diagnosis — contact without answer-supply, which is why a
routed lens stays generative rather than degenerating into a lookup.
The lens supplies the query seed; the world supplies the ground. Open
content, closed source-space — the shape the bare-versus-consultation
dichotomy cannot see, and the correct one for every lens whose subject
the world settles.

Read against the entry contract (§ 6), the lens satisfies the pentad
with every slot displaced one notch — which is why it kept reading as a
checkpoint with a missing slot. Its activation is inherited from its
host: a lens-checkpoint's walk schedule, a dispatch template's send, a
directive's read. Its payload is a question, not an answer — cached
judgment about *where judgment is needed*, the only caching T1 permits
where answers cannot be cached. Its warrant is not an authority but the
lens's *effect evidence*: the anchored instance its counterfactual
traces to (non-vacuity by supply, § 6) and the evidence that the angle
earns its walk — admissibly a literature anchor or a miss-stream
instance, while the variance stream that would let a lens cite its own
record remains design-stage. Its enforcement split is honest and thin:
the floor checks pairing, shape, and the grounding call where the
routed tier demands one; vacuity, angle quality, and answer truth are
residue, permanently. Its lifecycle is the crystallization law
(§ 7.4): a recurring answer caches down-ladder and retires the
question; an accrued authority converts the lens to a consultation —
lens and consultation are life-stages, not castes. The coordinate table
(§ 14.1) carries the column form of this walk; the fan and host laws
(§ 14.2) govern how lenses compose — one angle per context, a distinct
product per angle — and where each is hosted between dispatched and
in-walk contexts.

**The lens telemetry contract.** A lens's instrumentation is different
in kind from the consultation's — § 7.4 presents the two vocabularies
side by side: applied-over-considered and coverage joins against a
hook-space are questions an authority-backed duty answers and a lens
cannot.

> A lens is instrumented on three streams or it is ceremony: **answer
> variance** (the crystallization signal), **decoy rejection** (does
> the counterfactual actually filter — the lens's floor gate, run in an
> evaluation battery, never live: a **decoy** is a louder non-causal
> signal planted in the battery that the counterfactual must reject),
> and its **miss stream** (steers and defects its angle should have
> caught — the same should-have-fired archaeology consultations get).
> Firing frequency is not on the list, and catch-rate stays off it
> (I9): a lens optimized for catches manufactures them. The ceremony
> tell is Degani and Wiener's, transposed: an answer whose latency and
> content could have been produced without reading the item — the
> sub-second "checked" — with the authoring register's
> unfabricatable-pointer demand (§ 4.2) as the standing countermeasure.

The variance and decoy streams are design-stage: designed, not
exercised, and disclosed as the question tier's measurement zero among
the open problems (§ 17). The recorded lens failures reached their
corpora through the steer and defect streams instead — a
presumed-existence phrasing that manufactured nominations; a
constructive-only question battery that survived coherent wrong answers
until a refutation-phrased question was added — the lens-side forms of
the authoring register (§ 4.2), refutation phrasing and stipulated
certainty and the counterfactual among them, distilled from exactly
these misses. Counts on all three streams are floors, permanently. A
question, so governed, is a duty like any other: hosted, warranted,
walked, and retired by evidence.

## 13. Projections and seams

The read side's governing split is the **projection seam**: every entry
divides into a machine surface (flat metadata) and a judgment surface
(the body); indexes, queues, and status tables are read models
regenerated from machine surfaces, never hand-maintained (§ 5;
§ 12.2's hand-authored register is the licensed exception). The slot
mapping is exact: **projections carry activation and lifecycle — never
payload or warrant.** A cell may invite a read; it must never settle a
question. Consuming a conclusion from a summary cell is the named
failure — **authority leak**: a conclusion acquiring decision authority
through citation of a surface carrying no warrant.

**The settlement test** sharpens the slot rule to a cell-local,
decidable predicate:

> **A projection cell may carry anything a reader cannot comply with
> without opening the record. Anything a reader can obey directly from
> the cell is an authority cell — the leak installed at read time — and
> is evicted to the full record.**

Titles, recognition tokens, and a structured trigger's *condition*
pass — pure activation; a rule sentence and a trigger's *instruction*
fail — they can be obeyed unopened. The predicate is decidable by an
author and by a lint-shaped gate, and it moves enforcement from the
consumption side to the write side; the mechanization hint is parse,
don't validate (King, 2019). The pedigree is old — the U.S. Supreme
Court had to disclaim its reporter's headnotes after counsel complied
with a mischaracterizing syllabus (*United States v. Detroit Timber &
Lumber Co.*, 1906) — but that countermeasure is a standing disclaimer;
the settlement test refuses to admit the compliable sentence at all. In
one deployed corpus, an always-read index shrank by more than half when
compliable cells were evicted — a defect fix, not a compression win.
One hole, disclosed rather than patched: **compliance by omission** — a
stakes cell reading "low-risk" is compliable *by not opening the
record*; the hole is recorded, and no deployed implementation closes
it.

**Itemized-never-net** — the test's aggregate-valued case: a computed
aggregate ships its components; a lone net number is refused. The
primary warrant is Simpson's paradox (Simpson, 1951): pooling can
reverse the sign of every subgroup's finding — a net can be
*directionally wrong while every component is correct*. The
mechanizable half is additive attribution — components must sum to the
aggregate, a gate condition. Two caveats travel: itemization does not
defeat **compensability** (a reader handed the components still pools
them mentally), so where dimensions are not tradeable the remedy is
non-compensatory aggregation; and the rule is distinct from I9 — I9
forbids *targeting* a metric, this forbids *emitting* a bare one.
§ 10.4 applies the rule to the evidence state itself, and the
quantification projection (§ 11.3) meets it at population scale — a
combined score may be shown, never settle.

**Store-derived stage-one composition.** In a two-stage index, which
slot stage one *omits* is derivable per store — the composition surface
(§ 4.2) at its index-level instance, conditioning exercised through
omission and position rather than an authored question. The
**case-store index hides the rule**: hook, stakes, and live trigger
conditions — never a rule sentence, because compliable text is the
leak. The **duty-store index hides the duty and leads with the
residue** — *what the floor does not check* — because leading with the
duty invites automation complacency (Parasuraman & Riley, 1997). The
new content over I10 is **position**: I10 mandates residue disclosed
somewhere; nothing before this mandates where a projection leads with
it. Honest status: one implemented instance plus one designed inverse —
a proposal, weaker than a two-instance pattern; the deeper variable —
perhaps *whatever the reader must not be primed by*, given § 14's
blindness-preserving ledger projections — stays open (§ 17). The
mechanism is sequencing, not secrecy: stage two is one keystroke away.

**Enforcement seams.** Where a floor binds is a second classification
axis over the enforcement split, orthogonal to the gate-class
vocabulary:

- **The write-seam**: a sealed typed model refuses a malformed record
  before the first byte lands — the proof travels in the type.
- **The review-seam**: document-review and coherence gates over a
  committed diff.
- **The runtime-seam**: oracle honesty at evaluation time — absent data
  reads `unevaluable`, never zero — I16's runtime face; the seam where
  § 9's cascade lint, design-stage, would bind.
- **The consumption-seam**: warrant-tier verification at read — read
  the decision surface, never only its projection, and treat a
  conclusion found *only* in projections as an undecided fork to
  reopen, not a settled constraint.

The consumption seam is the one seam that cannot be mechanized in a
corpus humans read as text — no gate observes a reader's citation —
which is why the settlement test flips its law to the write side:
everything admission can evict is evicted at admission; whatever it
cannot, the consumption discipline must carry. The axis's most valuable
claim is **portability**, stated as deployment experience rather than
theorem: deployed corpora on different enforcement substrates have held
the same invariants through different seams. Prior art is quality
engineering's inspection taxonomy (Shingo, 1986); the imported lesson:
late-seam findings refine early-seam rules — a loop feeding the
consolidation pass (§ 7.4), not a static taxonomy.

With the seams, the machinery is complete. What remains is to show that
the artifact and agent diversity of a working project is this machinery
and nothing else.

## 14. One contract, many families

The user-facing diversity of a mature corpus's knowledge artifacts —
rules, decision records, standing questions, defect ledgers,
checklists, gates, role definitions, episodes — is one contract
evaluated at different coordinates (§ 6), worked here family by
family: a *theory of the artifact space*, not a collection of
practices.

### 14.1 The coordinate table

| Pentad slot | Rule entry | Decision entry (ADR) | Checkpoint | Lens | Ledger record | Gate | Observation |
|---|---|---|---|---|---|---|---|
| Activation | routed: declared firing shapes + a not-this clause | one-line summary, full-scanned; revisit triggers as re-activation | hook walked on schedule at plan time | inherited from its host — a lens-checkpoint's walk, a dispatch template's send, a directive's read | the contradiction's arrival (species-dependent) | unconditional over a derived population | trigger-fired ("re-check when…") — the same text a judgment record carries as a governed latch is here a latch-stripped advisory: class decides, not field shape (§ 9) |
| Payload | condition → duty, one sentence, object-decoupled | the Decision — a constraint on future forks | a bounded judgment procedure | a question, never an answer — cached judgment about *where judgment is needed*, the only caching T1 permits where answers cannot be cached | claim-as-held + verdict | all floor | a noticing |
| Warrant | enrollment evidence + human approval | constraining facts written as a falsification list | the authority slot's filling × its truth-maker | effect evidence — the anchored instance its counterfactual traces to, and the evidence the angle earns its walk | mandatory anchors + the unstaked adjudicator | derivation of its checked population | the anchor |
| Enforcement | explicit floor + disclosed residue | shape-gated only; content deliberately judgment | the checkpoint's paired record gate | floor checks pairing, shape, and the grounding call; vacuity, angle quality, and answer truth are residue, permanently | record grammar mechanical; verdict judgment | total (residue zero by definition) | none |
| Lifecycle | applied ÷ considered → demotion review; tombstones | status flip / supersedure; retirement on mootness | disposition lines + retirement typed by grounding class (corpus-join / world-reference / oracle) | the crystallization doors (§ 7.4): variance-collapse or authority-crystallization | classification pass + attacker-precision review | class floors; retirement on supersession | delete-with-pointer on promotion |

Read columnwise, the table recovers each family's felt character;
rowwise, the same slot flexing under different coordinates. The Lens
column is the question tier's slot walk (§ 12.6) in table form — every
slot displaced one notch from the checkpoint beside it. Two worked
contrasts.

**Why a rule is not a decision.** Rule recall is associative over
dozens of heavy duties, so activation must be a *routable key* — and
any router over-fires, so the slot grows a precision control (the
**not-this clause**: the router's declared exclusions); the payload
must *bind at work time*, so the enforcement slot is obligatory.
Decision recall is a bare full scan of cheap summaries, so activation
*is* the summary line; the payload constrains future design rather
than commanding present work, so enforcement nearly vanishes and the
*warrant* slot dominates — a falsification list, because "is this
still correct?" is the case store's live question (§ 3). Same
contract; recall economics and live question set the coordinates. What
this upgrades in the industry's folk forms is precisely the slots they
silently lack — ADRs nobody can tell are stale, rules nobody recalls
at the right moment; the completeness obligation is the contribution,
not the artifact.

**Why ledger records are deliberately key-poor.** The two-tier,
progressively disclosed shape serving rules and decisions is
*store-relative*, not universal — call this the **disclosure law**.
Ledger records get minimal frontmatter and no routing tier, for three
ascending reasons: no mid-work retrieval exists to serve (work-time
reads consume the consolidated successor, never the raw record); the
consolidation read is wholesale by design; and *blindness
preservation* — a retrieval-tuned key tier would surface the fast
loop's candidate labels to exactly the blind second coder who must not
see them (§ 7). The general law: ask of every store, *who reads this,
when, how many entries at once — and must any reader be blind?*
Individually, on demand → two-tier, disclosed, routed. Wholesale, at a
scheduled pass → flat, append-cheap, key-poor on purpose. A ledger's
consolidated *output* rejoins the disclosed world — the minted rule is
two-tier. (Which slots a *projection* may carry is § 13's seam.)

### 14.2 Agent families: roles as independence machinery

Sub-agent roles exist in GCE for an epistemic reason before any
throughput reason: **independence is structural, not attitudinal** — a
single context cannot be instructed into genuine self-skepticism, but
skepticism can be *constructed* by giving the contradiction its own
context with no authoring stake. The role taxonomy follows the ledger
taxonomy, not an org chart. **Examiners** are contradiction generators
(attack species): dispatched against proposed plans and store entries,
refute-phrased, reporting proposed records with verdicts left pending;
they never write or commit. **Independent derivers** are collision
parties: canonically, a test author with no authoring stake derives
expectations blind-first from committed artifacts and quarantines
rather than adjudicates its own disagreements. **Reconnaissance**
grounds claims against the live system — the world channel. And **the
implementer deliberately keeps no ledger** — its micro-decisions are
delegated to the strongest available adjudicators (compiler, tests,
tree), and when it catches its *briefing* wrong, the finding files in
the plan's ledger: a finding lives where the failed belief lives, not
where the finder sits.

What makes the implementer's ledgerlessness safe is a partition drawn
*per fork* at plan time. A pending fork is plan-side iff it is a
one-way door (Bezos, 2016), its coupling fans out past one owner, or
committed artifacts already answer it; implementation-side iff the
tree, compiler, or tests will adjudicate it better than deliberation
would (Poppendieck & Poppendieck, 2003). Forks fitting neither test —
plan-time-*invisible* — receive a typed disposition instead of a
silent gamble: an **information purchase** (a probe buys the fact
before the fork is forced) or a **declared-open** carry with a STOP
condition the implementer *surfaces and never decides*. The partition
is empirically estimable from the defect streams (§ 7.3): over-scoped
plans show up as plan-asserted micro-decisions falling to the tree;
under-scoped forks as STOP events or as defects with zero prior paper
trail.

Three disciplines keep the roles honest at scale: **freeze the
target** (an attack runs against the verbatim text it was handed; a
colliding derivation runs blind), **derive, never copy** (a
specialized role definition reads its base live and overrides named
sections — § 5's single-canonical-source law applied to the roles
themselves, under I3's resolvability precondition: where a role's
consumer cannot resolve the live pointer, verbatim carriage with one
owning dispatcher and a coherence gate on the copy is the honest
shape), and **a written deferral is a success outcome** (a property
the current instrument cannot check is declared, never faked with a
weaker check that happens to pass). GCE's role system is the
blackboard architecture (Erman et al., 1980) with two corrections: the
arbiter must be unstaked, and the hypothesis space must persist — and
be governed — across episodes.

The same structural argument scales down from roles to questions. A
lens fan (§ 12.6) walks several angles against one item, and the
temptation is to read its plurality as a throughput device — more
questions, more findings. The mechanism is different. The failure mode
of model-as-authority is not weakness but *correlated* weakness — one
context, one prior, one hypothesis — and a fan converts one correlated
judgment into several decorrelated ones, handing their synthesis to a
party that answered none of them. The external evidence draws the
boundary from the positive and negative side at once: perspective-based
reading, where each perspective *constructs a distinct artifact*,
measurably finds defects the others miss (Basili et al., 1996), while
hat-rotation, where the perspectives share one product and one
sitting, has no measured effect after four decades. The elicitation
literature reaches the same clause from its own side: nominal groups —
members generating independently before any pooling — beat interacting
groups on non-redundant ideas and quality by large margins (Mullen,
Johnson & Salas, 1991). And question quantity is not a quality axis —
tutoring outcomes track question quality, not frequency (Graesser &
Person, 1994).

> **The fan law.** A lens fan earns its plurality only as
> decorrelation: one angle per context, a distinct product per angle,
> the adjudicator never the answerer. A fan violating any clause is a
> longer prompt, not an ensemble.

Where a lens lives follows from the same machinery. The strongest
candidate host is the examiner species itself: dispatch buys the fan
law's three clauses *structurally* — one angle per context, a distinct
product, an unstaked adjudicator — along with the independence no
in-artifact pairing can supply, and it is adopted accordingly as the
default host for tree-facing lenses. The refusal of totality turns on
one distinction: signal locality. A dispatched context can read the
tree; it cannot read the session — the introspective event streams,
the walker's just-finished work, the context that understood a steer
before it is destroyed — and the in-walk lens tier exists precisely
for signal that dies with the session.

> **The host law.** A lens is hosted where its signal lives:
> tree-facing lenses in dispatched contexts, where independence is
> structural; session-local lenses in-walk, where the signal is. A
> walk question over tree-facing signal is a standing nomination to
> migrate out.

### 14.3 Fan-out censuses

When a corpus audits itself at fan-out scale — N agents censusing a
record population in parallel — the closed-set discipline (§ 7.5)
acquires additional rules. Census agents emit rigid typed records over
a **closed join-key vocabulary**, so the aggregation is a join, never
an interpretation. The escape channel is `novel:<slug>` with a
mandatory full proposal block, attempted against the existing key set
before it counts as gap evidence; duplicated escapes fall under
§ 7.5's independence qualifier. The aggregator is never one of the
extractors (I14). Negative space is typed: a record matching no key is
declared in the grammar — a `bare_case` field — not in prose. That
field is **reporting, not an instrument**: the instrument it gestures
at is a seeded-positive control plus the two-tailed agreement
diagnostic (*total* agreement means codes too loose to discriminate).
Two caveats: agreement over self-describing proposal blocks is an
upper bound, never an inter-rater statistic; and schema-constrained
output carries a measured constraint tax at decode time.

### 14.4 The episode family

Multi-session work runs in **episodes**: premise-locked units with a
living plan-spine, just-in-time slice materialization, and a
convergence ceremony. **Premise-lock + finite convergence.** Goals are
the convergence yardstick, verified against reality at close — never
task-list fulfillment; converged episodes never re-open — a changed
premise claims a *new* episode. The lock makes convergence falsifiable
and unplanned change detectable: a surface changing with no live
episode is drift. The human-practice cousin is Shape Up's circuit
breaker (Singer, 2019), not the surveyed spec-driven products whose
living specs re-open by design (§ 15). **Plan on-policy.** The spine
holds intent; work items materialize only for the next one or two
slices, after prior slices' reality is observed — stored plans rot.
**The spine/log split.** The spine is a rewrite-in-place statement of
the *what*; the logs are the append-only *how* (§ 5 applied to plans).
**Boundary consolidation.** Ceremonies at close — surprise scoring
against frozen predictions (§ 7.3), pain-versus-hypothesis review,
fold-back into the cross-episode catalog — because boundaries are
where the human is present: a third consolidation-trigger family
beside the field's idle-triggered (sleep-time compute, 2025) and
accumulation-triggered (Park et al., 2023) designs.

### 14.5 The instantiation law and genesis

Summarizing the section as doctrine: **a new artifact class or agent
role is admitted by filling the pentad and locating its coordinates —
and by finding, for each slot, which existing family it borrows
discipline from.** An artifact that cannot say when it activates has
designed a structural zero; one whose warrant cites itself, a
self-warranting verifier; one with no consumer, a graveyard; a role
adjudicating its own proposals has collapsed the separation of powers.
The families are a coordinate space with its failure modes mapped;
growth means claiming a new point under the same contract. One
proactive exception to the wait-for-recurrence bias attaches at
admission: **schema precedes records.** A new record class is born
with its record grammar, verdict vocabulary, and named consumer
already stated, honest about emptiness — because a schema gap's cost
is silent mis-location of records, which no recurrence counter ever
sees.

Where does the coordinate space's *population* come from? **The organ
roster is an output of the loop, not an input.** A project adopts GCE
by seeding the smallest configuration that can run one full cycle: the
invariant set and the entry contract (§ 6); the separation of powers
(§ 7.2); a constitutional file with its hard cap; one episodic pile
with mandatory anchors; a case store; a trace. Everything else is
minted later, by the loop, from the project's own typed miss stream,
through the route-before-mint ladder, at the project's own bars — grow
by trigger, and let refusal be an outcome. The port calculus's genesis
posture (§ 9) obeys the same form one level down: a young kind's port
declaration begins as a materialized projection of observed occupancy
guarded by a first-occupancy gate, and obligation marks are earned per
mark, through the write gate, once the kind's defects arrive as
conforming drift or owed-but-absent ports rather than as first
occupancies. Two ordering rules govern the bootstrap. **Start the
ledgers before the checkpoints**: a young project generates
contradictions from day one, and the ledger discipline eventually
reveals which checkpoints, rules, and gates *this* project needs — the
checkpoint roster is late-bound by design. The late binding also has a
reading, off the crystallization law (§ 7.4): a domain's lens-to-gate
ratio is a maturity reading, not a defect count. And **never copy another project's roster**: a roster encodes
its origin's failure history — which is why the deployed rosters this
paper draws on are offered as evidence, never templates. In
deployment, checkpoints were born event-anchored, in codification
waves. The bootstrap also discharges an apparent circularity: the
loop's first organs cannot have been admitted by the loop, and need
not be — they are the seed. The system is self-hosting in the
compiler's sense: hand-built once, at minimum viable size, then grown
only through its own governed pipeline (§ 2).

### 14.6 Importing the doctrine

What may a corpus legitimately take from another corpus's mechanism?
**Artifact-only import**, named for the failure it prevents:
**apparatus gold-plating** — importing more apparatus than the
obligation requires. An imported mechanism decomposes at a boundary
named at import time: the *artifact* (schema, vocabulary, enrollment
bar) and the *ceremony* (the donor's telemetry, cadence, and protocol
couplings, which earned their keep against the donor's misses). Import
the artifact; decline the ceremony, each refusal a first-class clause
in the admitting record. Institutional sociology predicted the
failure — structures adopted ceremonially for legitimacy, then
decoupled from activity (Meyer & Rowan, 1977); the adoption pull,
mimetic isomorphism (DiMaggio & Powell, 1983). What sociology
describes fatalistically, the import discipline makes procedural.

Two companion rules are staged minting (§ 7.5) restated at import
scale: seed with a few proven *local* entries before the store grows;
author no gate until the schema settles on real entries — a gate
authored against an unproven schema would freeze it. (This creates a
named tension with the duty-ships-its-floor discipline; the
reconciliation is to declare the unproven-schema period best-effort
explicitly.) The third clause closes staged minting's loophole: **the
donor's entries do not discharge the recipient's instance
requirement** — mode coverage is calibrated to the donor's phenomenon
space; proof travels with instances, and instances do not transfer.
One concession from implementation science's core-components versus
adaptable-periphery distinction: **identifying the core component of
an imported mechanism is an empirical problem, not always an
inspection** — one more reason the donor's evidence cannot substitute
for the recipient's.

## 15. Lineage

GCE sits at the intersection of ten literatures; for each we name the
inheritance and the divergence.

**Self-evolving context.** Karpathy (2025) named the paradigm
*system-prompt learning*, and a growing family instantiates it with the
model as its own librarian: Reflexion (Shinn et al., 2023), Voyager
(Wang, G. et al., 2023), ExpeL (Zhao et al., 2024), Generative Agents
(Park et al., 2023), ACE (2025), among successors and surveys (Luo et
al., 2026). GCE shares this genus — system-prompt learning at project
scale — and diverges on exactly one axis: **who writes.** The field lets
the model author its own memory and measures the consequences — context
collapse (ACE, 2025), brevity bias, self-bias amplification (Xu et al.,
2024) — while GCE's write path is constitutionally removed from the
model (§ 2).

**Agent memory systems.** MemGPT (Packer et al., 2023), Letta (2025),
Mem0 (Chhikara et al., 2025), Zep's bi-temporal graph (Rasmussen et
al., 2025), and consumer memory trace a write-policy spectrum on which
no major production system pre-gates memory writes on human approval by
default; GCE occupies that unclaimed pre-gated end. Two in-field
results support its structural bets — write-time functional-role typing
pays (+28%; Ha et al., 2026; § 3) and retrieval dominates write-time
sophistication (Yuan, Su & Yao, 2026) — and two constructs mark the
divergence at finer grain: the evidence-state axis is a governed
alternative to bi-temporal auto-invalidation (a loud flag and a waiting
human, not an invalidated edge), and the pre-admission tier answers an
identity question mint-on-write systems never ask. Demonstrated memory
poisoning (MINJA, 2025; AgentPoison, 2024), codified as OWASP's agentic
risk ASI06 (OWASP, 2026), converts "who may write?" from philosophy
into security.

**Context engineering practice.** Vendors independently converged on
the same three-way loading taxonomy — always loaded, matched, on-demand
— that GCE derives as stage-one attention ownership (§ 4), and the
practice measures its failure mode, context rot (Hong, Troynikov &
Huber, 2025); but promotion-on-evidence between tiers exists only as
informal advice, and GCE supplies the missing machinery —
capacity-capped tiers with forced eviction and an evidence-graded
promotion pipeline (§ 7). The same practice ships spec-driven pipelines
whose living specs re-open by design (GitHub Spec Kit, 2025; Kiro,
2025) — the contrast § 14.4's premise-locked episodes are drawn
against.

**Retrieval-augmented generation.** GCE's read path is deliberately
RAG-shaped, so the divergence is write-side lifecycle: RAG never
promotes, never abstracts on the way up, never tiers by decay, never
credit-assigns a write. GCE additionally refuses the embedder —
retrieval keys are symbolic and legible on purpose, because the
embedding model is as rented as the generator (§ 4).

**In-context learning versus weights.** "Fine-tuning by other means"
fails at mechanism — the ICL≈gradient-descent equivalence is refuted
for real models (Shen et al., 2024) — but the *slot* claim GCE builds
on survives: for factual and procedural payloads, context injection
beats fine-tuning outright (Ovadia et al., 2024), and context-resident
knowledge stays reversible, attributable, and live across model swaps.

**Automated prompt optimization.** TextGrad, GEPA, OPRO, and kin close
the text-update loop with the model inside it (Yuksekgonul et al.,
2024; Agrawal et al., 2025; Yang et al., 2023). GCE refuses the closure
at attribution: text-space credit assignment is measured weak (Zhang et
al., 2025), so attribution runs through human-plus-strong-model
judgment damped by recurrence bars, the human as optimizer (§ 2).

**Symbolic AI and knowledge engineering.** Truth maintenance systems
are the ancestor of ledgered hypotheses (Doyle, 1979; de Kleer, 1986) —
but their propagation was automatic, where GCE inserts adjudication
between contradiction and retraction. AGM belief revision axiomatized
minimal change while staying silent on who decides it (Alchourrón,
Gärdenfors & Makinson, 1985); case-based reasoning's *utility problem*
is the ancestor of retirement legs (Smyth & Keane, 1995); Soar's
chunking is promotion-raises-abstraction, ungated (Laird, Rosenbloom &
Newell, 1986); blackboard systems supplied independent sources over a
shared hypothesis space, within one episode (Erman et al., 1980). Cyc
is the cautionary monument — human gating *alone* yields an unbounded
maintenance liability (Lenat, 1995) — and Wikipedia exhibits the
measured failure GCE must also answer: rule mass without decay
ossifies (Halfaker et al., 2013).

From organizational science GCE inherits framing rather than mechanism:
double-loop learning (Argyris, 1977), externalization of tacit
knowledge (Nonaka, 1994), typed retention bins (Walsh & Ungson, 1991),
and the transactive-memory contrast — the agent's directory resets
every session, so the corpus must *be* the directory (Wegner, 1987).
From engineering practice, working precedents: decision records
(Nygard, 2011), the RFC lifecycle's maturity tiers (Bradner, 1996),
documentation typed by reader need (Procida, 2020), pre-registration
(Nosek et al., 2018), blameless postmortems (Beyer et al., 2016),
checklists (Gawande, 2009), bounded bets with a default-to-termination
circuit breaker (Singer, 2019), and the design-rationale literature's
*capture problem* (Conklin & Begeman, 1988; Lee, 1997) — the strongest
argument that in the LLM era capture should be agent-drafted and
human-gated, since drafting is what became cheap.

**Knowledge representation and reactive activation.** The activation
calculus (§ 9) descends from two lineages, and the axis the first
family named — who writes, under what governance — refracts at this
surface as *who declares activation, and who governs its key-space*.
The knowledge-representation lineage declares activation with the
artifact and its kind: frame systems with slots, facets, and attached
demons owned by the frame type (Minsky, 1975; Bobrow & Winograd, 1977);
Arden Syntax's medical logic module, whose `evoke` slot the record
itself declares beside `logic` and `action` (HL7, 1992–; Hripcsak,
1994) — and whose documented portability failure is the key-space law's
sharpest negative: institution-local terms sat inside the data bindings
(the "curly braces problem"), so a structurally perfect hook fired
nowhere but home; and SHACL shapes binding a class to its permitted
property surface (W3C, 2017). The inheritance is the port calculus's
skeleton; the divergence is governance — none of the three governs its
key-space vocabulary, and none gives activation units settlement
lifecycles. The reactive lineage — production rules and
event-condition-action systems (Aiken, Widom & Hellerstein, 1992),
content-based publish/subscribe, aspect-oriented pointcuts (Kiczales et
al., 1997; the fragile-pointcut result, Koppen & Störzer, 2004), and
blackboard activation records scheduling on the trigger-plus-
precondition pair (Erman et al., 1980; Nii, 1986) — contributes the
edge/guard split, the reified activation record, and the cascade
analysis, and diverges constitutionally: third-party ownership over
oblivious bases, which the doctrine accepts only for its contradiction
machinery, the examiner species. Type-based publish/subscribe (Eugster
et al., 2003) is the reactive lineage's own arrival at the calculus's
center — subscription re-anchored on kind because content-keyed hooks
proved untypeable — cited as convergence from the opposite shore.
Adjacent fields supply single parts: the typestate and session-type
lineages, state-indexed admissibility (Strom & Yemini, 1986; Honda,
Vasconcelos & Kubo, 1998); legal drafting, the norm kernel's separable
condition of application (von Wright, 1963); formal ontology, the
disposition category and no machinery (Arp, Smith & Spear, 2015). And
description logic supplies the lesson the owed-act vocabulary obeys:
the frame lineage's procedural attachment made frames formally
unanalyzable, and the field deliberately dropped it to get semantics
back (Brachman & Schmolze, 1985; the critique line runs from Woods,
1975, through Hayes, 1980).

**World models for language-model systems.** The term *world model* is
owned, in the machine-learning literature, by a different object — a
learned predictive model of environment dynamics — and that ownership
has consolidated rather than loosened: the field's own comprehensive
survey organizes it around understanding the present and predicting the
future (Ding et al., 2025), neither of which is the belief store's
object. Around that core, six families touch the doctrine's territory,
and the divergences concentrate on the same axis, sharpened at the
belief store to *who writes, and what settles*. The family that owns
the name (Ha & Schmidhuber, 2018) has moved further toward simulation,
not away — latent-dynamics agents at Nature-published generality
(DreamerV3; Hafner et al., 2025), action-conditioned video world models
at zero-shot robot deployment (V-JEPA 2; Assran et al., 2025),
interactive generative environments as a product category (the Genie
line; Google DeepMind, 2025). Its world model is a simulator whose
knowledge is inseparable from its weights: the writer is the optimizer,
the truth-maker is prediction loss, and no individual belief exists as
an inspectable, retractable object — while the corpus's model is a
governed population of discrete falsifiable text commitments that can
roll nothing forward: it deliberately owns claims and their settlement,
and rents all simulation. The mainstream has widened this gap, not
closed it; the § 10 boundary is a live distinction no surveyed family
merges. The probing literature finds genuine world-structure inside the
frozen generalizer (Li et al., 2023; Gurnee & Tegmark, 2024; Shai et
al., 2024), with deflationary and inflationary re-readings contesting
what that structure is (jylin04 et al., 2024; Yuan & Søgaard, 2025; the
debate surveyed carefully in M. Mitchell, 2025), and a formal result
closes one flank: any agent that generalizes to multi-step
goal-directed tasks has necessarily learned a predictive world model,
recoverable from the agent (Richens, Everitt & Abel, 2025). The theorem
is read here as support, not threat — an agent provably carrying a
world model the project cannot read, audit, or version is precisely the
agent whose project must own its own (I12) — and the same literature
supplies the measured reasons: models that ace next-token diagnostics
hold incoherent implicit state machines under Myhill–Nerode-style
tests (Vafa et al., 2024); a foundation model that predicts the data
can still fail to carry the domain's governing structure (Vafa et al.,
2025); and models are measured poor at exactly the operation the belief
store performs — revising beliefs appropriately under new evidence
(Wilie et al., 2024) — which is why supersedure, region cuts, and
settlement live outside the model, in the corpus. A third family
repurposes the model itself as the world model inside a planning loop —
a next-state proposal distribution under search (RAP; Hao et al.,
2023), extended to trained web-environment dynamics models when the
frozen model's outcome-awareness proves absent (Chae et al., 2025) or
its imagination proves profitable (WebDreamer; Gu et al., 2024). Its
own strongest recent result is, usefully, negative: measured directly
on state transitions, GPT-4 is an unreliable text-world simulator
(Wang, R. et al., 2024). The divergence is trust — this family plans
through the model's implicit dynamics and measures the cost, while the
doctrine forbids the model any truth-maker role and does not plan
through rollouts at all. One scope honesty travels with the refusal:
the simulator posture is measured useful where candidate actions are
cheap to imagine and verification is fast (Gu et al., 2024); the
world-facing deployments' domains — seasonal outcomes, macroeconomic
regimes — are the opposite regime, where settlement is slow and a wrong
rollout costs a season. The refusal is regime-honest, not universal.
Within this family sits the nearest located neighbor to the doctrine's
write path: Guan, Valmeekam, Sreedharan & Kambhampati (2023) have a
pre-trained model *draft* an explicit, symbolic world model that humans
then correct before a sound planner uses it — AI-drafted,
human-corrected, externalized world knowledge in legible text, this
doctrine's labor split (the capture argument above). The divergence:
theirs is an operator model, corrected once at construction time, with
no hypothesis lifecycle, no pricing, no settlement stream, and no
schema under validation; the corpus's model is a standing belief
population whose corrections never end. Externalized structured memory
has adopted the term itself — AriGraph names its agent-maintained
graph a "knowledge graph world model" (Anokhin et al., 2024) — and now
includes systems in which new memories trigger automatic revision of
old ones (A-MEM; Xu et al., 2025), the register/ledger violation of § 5
made a feature; the strongest historical near-miss, NELL (T. Mitchell
et al., 2018), ran a persistent, confidence-weighted belief store under
periodic human supervision for eight years, with automatic writes,
post-hoc spot correction, nothing settling its beliefs against a future
it did not extract from — and its documented ontology drift is an
argument *for* the pre-gated write path, not against it. These systems
optimize recall of what was said; the doctrine's store optimizes
accountability of what was claimed. A directed review located no memory
system carrying typed falsification grammars with admissibility maps,
entry pricing against a frozen reference, pre-registered conditioning,
or a schema receiving validation pressure from a settlement stream. The
forecasting and judgment line —
retrieval-augmented pipelines approaching crowd accuracy on post-cutoff
questions (Halawi et al., 2024; Schoenegger et al., 2024), continuously
refreshed future-only benchmarks (ForecastBench; Karger et al., 2025),
the quarterly human-versus-bot series (Metaculus, 2024–2025) — owns
exactly the disciplines §§ 10–11 import: the freeze, temporal
out-of-sample settlement, reference-relative skill under proper
scoring. The divergence: a forecasting system is a stateless scorer of
answers, each question scored and forgotten, while the doctrine's world
model is a stateful ledger of commitments whose settlements calibrate
not just the forecaster but the store's own kind-axes and admissibility
maps. The family's measured results bear on the doctrine's
constitutional choice — through the most recent settled comparisons the
human forecasters still lead, and LLM forecasters violate the
probabilistic consistency a settling net would require (Paleka et al.,
2024) — cited as the current state of a moving field, never as a
permanent gap. Last, the pre-registration and credibility disciplines
carry no world model at all; they contribute the governance primitives
§§ 10.6–11 mechanize: pre-registration migrating into predictive
modeling and ML practice itself (Bertinetto et al., 2021; Hofman et
al., 2023), the anti-contamination benchmark lineage from adversarially
refreshed test sets to future-only questions (Kiela et al., 2021;
Karger et al., 2025), and the condition-credibility instruments (Sun et
al., 2010; the ICEMAN instrument, Schandelmaier et al., 2020; Casey,
Glennerster & Miguel, 2012; Olken, 2015). The genuine inheritance —
knowing, acknowledged — is pre-registration itself and the
forking-paths diagnosis it answers (Nosek et al., 2018; Gelman & Loken,
2014); the credibility instruments are independently derived twins,
cited as convergence. The divergence from the whole family: it governs
*analyses*, one at a time — no standing store receives its discipline,
and no agent runs under it.

**Elicitation traditions.** The question tier's neighbors (§ 12.6) are
elicitation traditions, not memory systems, and the axis refracts once
more: *who answers, and what forces contact outside the answerer*. The
structured-analytic-techniques tradition contributes the taxonomy —
diagnostic, contrarian, imaginative (U.S. Government, 2009) — and the
field's most instructive null: decades of institutional adoption, one
technique with real structure, and measured results null to negative —
form without externality (Chang & Tetlock, 2016). Expert-elicitation
practice contributes the countermeasure in its strongest form:
judgment made reliable by scoring against seed questions with known
answers (Colson & Cooke, 2018). Aviation and clinical checklist
practice contribute the ceremony diagnosis and its remedy, the
value-carrying response, plus the sobering scale result that the
artifact works only inside the social system that animates it (Haynes
et al., 2009; Urbach et al., 2014). The after-action-review tradition
contributes a measured generative instrument that doctrinally refuses
an answer store (Keiser & Arthur, 2021). And the question-set
deflations cut against the transferable-question-set hope from two
sides: the five-whys is promoted by its institutional sponsors without
evidence of effectiveness and converges prematurely on single causes
(Card, 2017), and the taxonomy most used to type questions fails both
of its internal assumptions on measurement (Larsen et al., 2022) — the
transferable universal layer is a small set of angles, never an
answer-producing question set.

**Negative results.** The novelty surface is what a directed review
failed to locate — with the scope of each search stated, since a
domain-scoped negative is honest and an unscoped one is not. No located
prior art individuates record stores by truth-maker — every near
neighbor partitions on content type, abstraction level, reader need,
provenance, or interrogative facet, and the nearest formal relative —
Hart's primary and secondary rules (Hart, 1961) — cuts within the
normative layer and carries no belief store. No located source states
the derivability discriminator (§ 12.2) — six literatures supply
vocabulary for its two outcomes, none for the rule selecting between
them (Gotel & Finkelstein, 1994, diagnosed the split without turning it
into a build rule). The decision-record literature has duty
conflation's symptom but not its mechanism (Nygard, 2011; Zimmermann,
2023). The trigger-lifecycle literature governs firing thoroughly and
the fired trigger's record not at all — no settlement concept, no
partial-fire operator.

Within world models for language-model systems and agent memory, the
directed review located no system that conditions belief refinement on
a pre-registered mechanism, and none that states any admissibility
condition on conditioning variables: the condition-admissibility rule
(§ 10.6) is novel in its domain, and its composite form — admission
gate, governed basis-frozen proxy, the decidable fork — was located
nowhere in *any* field, its clause-level cross-field twins disclosed as
convergence. Schema-validation-by-settlement decomposes into components
that each have prior art — drift detection over prediction streams
(Gama et al., 2014), dynamic contamination-free evaluation (Kiela et
al., 2021; Karger et al., 2025), the walk-forward temporal validation
of quantitative practice — while the composite — one settlement event
scored once against the judgment and simultaneously read as validation
pressure on the store's own kind-axes and admissibility maps,
firewalled by append-only supersedure — was located nowhere. In the
activation survey's fields, the composite claimed as unlocated is a
kind-level, defeasible, escape-instrumented port declaration over typed
activation units that each carry their own settlement grammar and
lifecycle, under a governed key-space vocabulary, with fires reified
into a human-disposed ledger; the components all have prior art, named
above — the composition is the doctrine's. Among the elicitation
traditions, the composite claimed as unlocated is the lens as a
governed, versioned corpus artifact — counterfactual-paired by supply,
externality-graded by truth-maker, fan-composed by decorrelation,
lifecycled by answer variance, instrumented by decoy — inside a system
whose write path already contains its outputs. And where the doctrine's
constructs have deployed industrial twins — the spec/status and
name/UID splits, computed alert state versus incident lifecycle,
applicability registers under audit — they are cited as convergence,
not lineage.

That convergence is the doctrine's strongest external evidence: its
countermeasures — append-only piles, typed stores, delta-not-rewrite,
hard-capped always-loaded tiers, human-gated writes — were in place in
deployment before the literature measured the failures they prevent
(context collapse, heterogeneous-store contamination, context rot,
memory poisoning), and the memory field's own turn toward typing,
provenance, and per-memory utility is a turn *toward* the positions
argued here. Convergent evolution from opposite directions is the
strongest validation available to a doctrine that cannot run controlled
trials on itself. It is not proof; § 16's limits stand.

## 16. Failure surface and boundary conditions

Stated honestly: the advantages and the costs are one design viewed
from two sides.

1. **Hand-maintained where products mechanize.** Much of what GCE runs
   as conventions-plus-gates, tooling products ship as features — a
   real, permanent cost. The capture problem (Lee, 1997) is the standing
   threat: the discipline survives only while capture stays near-free,
   which is why agent-drafted/human-gated is the only viable labor
   split.
2. **Precondition-bound.** The approach pays off under one consistent
   calibrating judge, many episodes, and a long horizon; outside those
   preconditions the discipline is tax. Solo calibration is
   simultaneously the enabling precondition and the largest validity
   threat — and the threat is consolidated, not distributed: every
   deployment in the evidence base, process-facing and world-facing
   alike, is governed by the same single calibrating human, with no
   inter-rater check anywhere in it. Cross-corpus convergences are
   therefore cross-cited, never independent; where deployment evidence
   is composed with literature evidence, the composition is the
   doctrine's own; and the external convergences, however exact, were
   located by directed review after the constructs stabilized —
   convergence, never lineage, and graded so (§ 15). Where the
   deployments split — whether grammar-level constraints bind into
   ports (§ 11.1) — the stated resolution is a posture, not a finding:
   two corpora cannot say which posture a third domain needs. The
   sharpest open test is § 17's: a doctrine-blind adoption under an
   independent judge, in a domain no deployed corpus touches.
3. **Presence, not quality.** The mechanical floor checks that records
   exist, parse, and carry their slots; quality stays unmechanized *by
   design* — so the system's core quality claims are exactly its
   unmeasured ones.
4. **The overhead tax.** Bookkeeping is time off product work and the
   dominant felt cost; mechanize bookkeeping relentlessly, never the
   completeness judgment.
5. **Silent misses are floors.** Every detector's observed-zero is
   detection-limited; recall — an entry that should have fired but was
   neither routed nor recalled — is unmeasurable without ground truth,
   the honest estimators being independent-judge probes and the passive
   archaeology of downstream defect stores. The few retained
   measurements are, likewise, single instances, not rates.
6. **Some instruments cannot measure themselves.** Where synthesis
   absorbs an examiner's feedback immediately, rejection never becomes a
   discrete observable, and a perfect precision score over zero
   rejections is a ceiling artifact, not a clean bill. Similarly,
   blind-coding agreement over self-describing records is an upper
   bound, never a clean inter-rater statistic (§ 14.3).
7. **Forgetting is relocated, not eliminated.** Weight-forgetting is
   traded for retrieval failure; structural zeros — records the read
   side cannot reach — are the new forgetting: unreachable, not erased
   (*When Continual Learning Moves to Memory*, 2026). And the frozen
   model is a dependency that version-bumps: a model swap silently
   re-prices every checkpoint and rule sentence, in both directions.
   The re-pricing story is complete for selection and absent for
   composition: latch keys are legible symbols that survive a swap, but
   a lens's effect is a property of the model that reads it — every
   lens is priced per model, the format-sensitivity results say the
   pricing is volatile, and with no variance or decoy telemetry
   running, nothing in any deployment would detect a swap voiding half
   the lens register. Price the swap deliberately, and watch referents,
   never aliases: in deployment, a sensing arm watching alias strings
   did not fire when the referent moved.
8. **Recall, not transfer.** The gains are in-domain (Beyond
   Perplexity, 2026), and abstraction-on-promotion is the one
   intervention pushing past pure recall. Transfer of the *system*, as
   opposed to its knowledge, is the open question § 17 states.
9. **Threshold currency under-derived — and the routing's features
   degrade exactly when needed most.** The few-instance promotion bars
   are house convention; the field's alternatives derive their
   currencies no better, and applied ÷ considered ratios are the
   nearest in-house instrument. Revision routing (§ 7.5) inherits the
   same early weakness one level up: truth-maker identity, breadth, and
   dependence are computed over small escape piles, the dependence
   feature is unreliable at small N, and payload clustering can launder
   the fast loop's own bias absent blind coding. The nominator weakens
   early by design — early vocabulary error is caught late, the
   standing cost of refusing to fire schema changes on a handful of
   instances.
10. **The fine structure carries design-stage boundary conditions.** The
    grain law (§ 8) is stated for the regime the human write gate
    creates — outside it (gate cheap relative to contradiction volume)
    the law is untested and possibly false. Leafing degenerates if most
    real contradictions are basis-free — an empirical property of the
    domain, not the doctrine, and one with a detector: the
    per-supersedure census (§§ 11.2, 11.4) records, at each supersedure,
    whether the contradiction named a predicted region, indicted the
    warrant wholesale, or was an instrument re-grade. The adoption
    register inherits certification practice's documented base rate of
    ceremonial drift (§ 12), untested against its countermeasures.
    Validity instrumentation (§ 10) does not exist: `undercut` alone is
    unimplementable without new machinery. Store-derived stage-one
    composition (§ 13) rests on one implemented instance plus one
    designed inverse. The activation calculus's finest members — edge
    and guard as declared fields, the fire ledger, the cascade lint,
    port obligation marks — are design-stage: no deployment declares
    them, and a corpus adopting them buys audit granularity with
    standing weight the route-before-mint ladder (§ 7.4) must price
    honestly. And the belief-store constructs most exposed to incentive
    complications are exactly those with the least adversarial usage.
11. **Every new floor leaves a named residue.** The settlement test's
    gate checks compliability shape, never honest scent; the register's
    gate checks that cells are triaged, never that triage was right; the
    transcription oracle's guards check readability of the fact, never
    the wisdom of the freeze; `bare_case` reports, and only a seeded
    control would test. The residue lines are the disclosure.
12. **Small-N discipline still binds.** Pre-registration, pooling, and
    interval honesty make a corpus honest about what five points cannot
    identify; they do not make it identifiable. The deployments'
    central statistical finding is negative: with a short, confounded,
    self-selected panel, the honest forecast of a sign-flipping
    conditional edge is a wide interval spanning both signs — and a
    system whose chief virtue is that it says so is functioning, not
    failing. The pooling argument itself carries a scope note (§ 11.3):
    the shrinkage dominance theorem is narrower than the posture built
    on it, which imports the direction, not the theorem.
13. **A conditioning variable can be non-identified even when
    pre-registered.** A mechanism can name a variable confounded with
    calendar, rule changes, and cohort composition; pre-registration
    (§ 10.6) makes the conditioning falsifiable and auditable, not
    identified. The causal-inference lens names the estimand and the
    confound (Pearl, 2009); it rarely supplies the experiment.
14. **Regimes can be endogenous to the beliefs they condition.** Where
    the modeled agents adapt — adoption responding to the very edge it
    erodes — the regime is reflexive (the El Farol precursor, Arthur,
    1994; its minority-game formalization, Challet & Zhang, 1997), and
    a static partition is the wrong shape for a moving equilibrium. The
    refinement structure offers nothing here; the honest posture is to
    flag the endogeneity and widen.
15. **The falsification-surface audit inherits selection risk.** An
    audit run after an adverse print is a selected sample of one; the
    retroactive-as-check framing (§ 11.4) holds only when conditions
    and disciplines predate the contradiction, and the audit must
    record which case it is in.
16. **The port declaration flirts with priming.** Declaring ports ahead
    of occupancy is minting classes ahead of instances — the exact
    failure § 7.5 names. The occupancy-projection genesis (§ 9) is the
    mitigation, and it carries a residue of its own: obligation marks
    are exactly the part a projection cannot express, so they arrive
    late by design, and the defects only marks can catch — conforming
    drift, the owed-but-absent port — go uncaught until the marks are
    earned.
17. **The derived record grammar can be empty or conflicted.** A record
    whose dispositive latches are all manual or unwatched has a join
    over nothing: its effective grammar is honestly unsettleable by
    machine, and the calculus must display that as the evidence state
    displays `unwatched` (§ 10.4) — loudly, never defaulted. A record
    whose dispositive latches disagree in grammar is the antichain case
    at the latch tier (§ 8): surfaced for human disposition, never
    silently tiebroken.
18. **The weak-model floor is real, and a lens cannot buy through it.**
    A lens redirects attention; it does not add capability.
    Discrimination advantage tracks capacity — only sufficiently large
    models avoid distractor tasks (Wei et al., 2023) — and below the
    floor the working fallback is not shape but vocabulary, the written
    principle supplying content the answerer lacks (Bai et al., 2022).
    A corpus should expect its bare-lens tier to be the first casualty
    of a weaker session model, and its vocabulary-lens tier to be the
    load-bearing fallback.
19. **The lens regime is property-exhibition, never correctness.** The
    ablations showing lens leverage live where the criterion is
    exhibiting a property; on verifiable-truth tasks the same machinery
    gains nothing or degrades — the exhibition regime is where the
    evidence itself lives. A lens asked to adjudicate correctness is a
    category error: correctness belongs to oracles, gates, and the
    world.
20. **Lens specificity is answerer-relative.** The expertise-reversal
    result — specific prompts help low-competence answerers and can
    hurt high-competence ones (Kalyuga, Ayres, Chandler & Sweller,
    2003) — means no single register is optimal across model tiers, and
    a corpus serving several (a strong planner, weaker dispatched
    workers) owes its lens rows a per-audience reading the deployments
    do not carry.
21. **The yield gap: elicitation is not action.** The soberest
    datapoint in the elicitation survey is teams generating
    seventeen-odd failure reasons per premortem and then revising their
    plans "surprisingly" rarely (Roose, Lehman & Veinott, 2023). A lens
    whose answers do not land in a routed record with a named consumer
    is theater regardless of its quality. The constitution already
    carries the remedy — no record without a standing consumer (I5),
    findings filed to their owning ledgers (I15) — and the question
    tier inherits it explicitly: every fan's product declares its
    disposition route, or the fan is not walked.
22. **The schema surface is unhomed.** The store roster (§ 3.3) names
    no store class for the registries the kind and port calculi write
    to — axis registries, port declarations: schema artifacts that are
    neither hypothesis stores nor procedures. The doctrine uses the
    organ without homing it; the store-roster account is owed (§ 17),
    and the pentad's sufficiency claim survives only together with that
    debt.

## 17. Discussion

**What GCE is not.** Not self-evolving context — it is that field with
the write path constitutionally removed from the model. Not RAG — the
read path is deliberately RAG-shaped; the write-side learning lifecycle
is what RAG lacks. Not fine-tuning by other means — the equivalence
fails at mechanism. Not a world model in the simulator's sense — the
belief store's boundary (§ 10) bounds the term to a governed set of
falsifiable commitments calibrated through settlement, never rollout
machinery, a learned transition function, or a probabilistic database.
Not automated prompt optimization — GCE refuses the closed text-update
loop at the attribution step. Not spec-driven development — GCE runs
premise-locked finite episodes with convergence held as human judgment
(§ 14.4). Not a project-management methodology and not a product — it
borrows human practice as vocabulary, never as imported apparatus, and
much of what products ship as features it runs as conventions plus
gates (§ 16). Not universal — the preconditions are stated, and outside
them the discipline is tax.

**On borrowed vocabulary.** Each borrowed ML-training term was graded
against the literature before use; the record of rejections is part of
the doctrine. "The documents are fine-tuning" fails at mechanism;
"verification is backpropagation" fails at attribution; the one
surviving form is § 2's governance polarity — mapping polarity, never
update mechanism. The grading is not confined to ML: formal ontology
enters on the same terms — a latch is a disposition in BFO's category
sense (§ 9), and BFO supplies the category and no machinery. Analogies
supply vocabulary, pathology taxonomies, and specification language;
they never justify apparatus.

**The completeness posture.** GCE makes two different completeness
claims and marks which is which. Where a closed derivation encloses a
space, totality is by construction: the pentad's five slots are the five
global functions the removed optimizer no longer provides (§ 6).
Everywhere else — the store roster, the species table, the artifact
families, the latch fan's rows (whose port declarations carry the
calculus's own escapes: the warranted exception and the first-occupancy
gate, § 9), the seam classification, the invariant set itself — the
enumeration is closed-with-escape (§ 7.5): complete relative to the
observed miss stream, with the instrument that detects incompleteness
built in (I16). The posture has operated: two organs entered the roster
through fired escapes converted into derivations — the belief store,
and the fact-and-trace floor (§ 10's zero-price theorem). A record
class fitting none of the three legs, a sixth latch type, a fifth
seam — each re-derives its table rather than embarrassing it.
"Rationally complete as far as we know" is a precise, falsifiable
posture, not a hedge.

**Open problems.** Twelve are research questions rather than backlog.
*Recall measurement*: should-have-fired ground truth without exhaustive
labeling. *Threshold derivation*: promotion bars from measured
attribution noise rather than convention. *Vocabulary timing*: when a
class set must precede the judging it serves. *The transfer question*: a
doctrine-blind adoption under an independent calibrating judge is
unrun. *Validity instrumentation*: pressure's validity component
(`undercut`) has no instrument anywhere. *The belief-store factoring of
case premises*: migrate the case store's embryonic belief records —
world-facing premises and world-keyed revisit triggers (§ 9) — into
watched belief records with wiring edges back, and measure whether
§ 8's key-space divergence closes. *Question-selection governance*: no
located mechanism closes which claims enter; neither freeze — claim
(§ 10.2) or schema (§ 11.2) — closes it. *Grain economics*: make the
storage law's regime boundary a computable property of a corpus. *The
leafing base rate*: what fraction of real contradictions localize to a
predicted region — the number deciding whether leafing is a granularity
law or an elaborate escape — is instrumented by the per-supersedure
census (§§ 11.2, 11.4) but unaccumulated; the reading, not the
instrument, is owed. *The schema-surface derivation*: derive the store class of the
registries the kind and port calculi write to — schema artifacts that
are neither hypothesis stores nor procedures — from the two partition
axes, or show which third axis is missing (§ 16). *The lens measurement
zero*: the lens telemetry contract (§ 12.6) — answer variance, decoy
rejection, the miss stream — has run nowhere; every claim about
deployed lens quality is design-stage, and the lens machinery's own
defects were caught by the examiner species and the steer stream, not
by any lens instrument. *The third-store derivation*: state the
stage-one omission rule for ledger projections from the anti-priming
variable (§ 13).

## 18. Conclusion

Under the frozen-model constraint, "how should an AI-assisted project
manage its documentation?" is mis-posed. The corpus is not
documentation *about* the system; it is the only substrate in which
the system can learn. Taking that seriously yields the doctrine argued
here: unbundle what training bundles; give every store its own decay
profile and every entry the full five-slot loop nothing global will
run for it; let contradiction come from structurally independent
sources, judged by unstaked parties; damp refinement with recurrence
bars graded by blast radius; keep a human at the write gate — the one
write policy the surveyed landscape has not falsified.

Pressed across payload classes in deployment, the statics raise three
questions the doctrine now answers. What partitions stores, besides
decay? The truth-maker, with its membership test and the derivability
discriminator (§§ 3, 12). What is the unit — of ratification,
falsification, retrieval — and why should one physical record serve
all three? It should not: canonical storage sits at the commitment
grain, the falsification grain is materialized lazily by leafing, the
retrieval grain derived as a projection (§ 8). What, exactly, is an
activation? Not a slot but a fan of typed latches under a kind-level
port declaration (§ 9) — and where an activation join acquires a
judgment duty, a checkpoint (§ 7.4). In deployment against
world-facing payloads the invariants held and the contract
transferred. The model's intelligence is rented. The learning had
better be owned.

---

## References

*Preprints are cited by arXiv identifier; practice sources by primary
URL. Where author lists, identifiers, or volume details were not
verifiable from primary sources, entries are given by title or by venue
and year.*

- ACE — *Agentic Context Engineering: Evolving Contexts for
  Self-Improving Language Models.* arXiv:2510.04618, 2025.
- AgentPoison — *AgentPoison: Red-teaming LLM Agents via Poisoning
  Memory or Knowledge Bases.* NeurIPS 2024.
- Agrawal, L.A. et al. — *GEPA: Reflective Prompt Evolution Can
  Outperform Reinforcement Learning.* arXiv:2507.19457, 2025.
- Aiken, A., Widom, J. & Hellerstein, J. — *Behavior of Database
  Production Rules: Termination, Confluence, and Observable
  Determinism.* SIGMOD 1992.
- Alchourrón, C. & Makinson, D. — *Hierarchies of Regulations and Their
  Logic.* In Hilpinen (ed.), New Studies in Deontic Logic, 1981.
- Alchourrón, C., Gärdenfors, P. & Makinson, D. — *On the Logic of
  Theory Change: Partial Meet Contraction and Revision Functions.*
  Journal of Symbolic Logic 50(2), 1985.
- Anokhin, P., Semenov, N. et al. — *AriGraph: Learning Knowledge Graph
  World Models with Episodic Memory for LLM Agents.* arXiv:2407.04363,
  2024; IJCAI 2025.
- Aphyer — *Ambiguity in Prediction Market Resolution is Harmful.*
  LessWrong, September 26, 2022.
- Argyris, C. — *Double Loop Learning in Organizations.* Harvard
  Business Review 55(5), 1977.
- Arp, R., Smith, B. & Spear, A. — *Building Ontologies with Basic
  Formal Ontology.* MIT Press, 2015.
- Arthur, W. B. — *Inductive Reasoning and Bounded Rationality* (El
  Farol). American Economic Review 84(2), 1994.
- Assran, M. et al. — *V-JEPA 2: Self-Supervised Video Models Enable
  Understanding, Prediction and Planning.* arXiv:2506.09985, 2025.
- Bai, Y. et al. — *Constitutional AI: Harmlessness from AI Feedback.*
  arXiv:2212.08073, 2022.
- Basili, V. et al. — *The Empirical Investigation of Perspective-Based
  Reading.* Empirical Software Engineering 1(2), 1996.
- Berners-Lee, T. — *Cool URIs don't change.* W3C, 1998.
- Bertinetto, L., Henriques, J.F., Albanie, S., Paganini, M. & Varol,
  G. (eds.) — *NeurIPS 2020 Workshop on Pre-registration in Machine
  Learning.* PMLR v148, 2021.
- Beyer, B., Jones, C., Petoff, J. & Murphy, N.R. (eds.) — *Site
  Reliability Engineering.* O'Reilly, 2016. Ch. 15, "Postmortem
  Culture."
- *Beyond Perplexity* — on external-memory gains as within-family
  recall. arXiv:2607.00368, 2026.
- Bezos, J. — *2015 Letter to Shareholders* (Type 1 / Type 2
  decisions). Amazon, 2016.
- Bisra, K., Liu, Q., Nesbit, J., Salimi, F. & Winne, P. — *Inducing
  Self-Explanation: A Meta-Analysis.* Educational Psychology Review
  30(3), 2018.
- Bobrow, D. & Winograd, T. — *An Overview of KRL, a Knowledge
  Representation Language.* Cognitive Science 1(1), 1977.
- Brachman, R. & Schmolze, J. — *An Overview of the KL-ONE Knowledge
  Representation System.* Cognitive Science 9(2), 1985.
- Bradner, S. — *The Internet Standards Process — Revision 3.* RFC
  2026, IETF, 1996.
- Business Rules Group — *Business Rules Manifesto*, v2.0, 2003.
  https://www.businessrulesgroup.org/brmanifesto.htm
- Card, A. — *The Problem with '5 Whys'.* BMJ Quality & Safety 26(8),
  2017.
- Casey, K., Glennerster, R. & Miguel, E. — *Reshaping Institutions:
  Evidence on Aid Impacts Using a Preanalysis Plan.* Quarterly Journal
  of Economics, 2012.
- Chae, H. et al. — *Web Agents with World Models: Learning and
  Leveraging Environment Dynamics in Web Navigation.* ICLR 2025;
  arXiv:2410.13232.
- Challet, D. & Zhang, Y.-C. — *Emergence of Cooperation and
  Organization in an Evolutionary Game* (minority game). Physica A 246,
  1997.
- Chang, W. & Tetlock, P.E. — *Rethinking the Training of Intelligence
  Analysts.* Intelligence and National Security 31(6), 2016.
- Chhikara, P. et al. — *Mem0: Building Production-Ready AI Agents with
  Scalable Long-Term Memory.* arXiv:2504.19413, 2025.
- Chia, Y.K., Chen, G., Tuan, L.A., Poria, S. & Bing, L. — *Contrastive
  Chain-of-Thought Prompting.* arXiv:2311.09277, 2023.
- Colson, A. & Cooke, R. — *Expert Elicitation: Using the Classical
  Model to Validate Experts' Judgments.* Review of Environmental
  Economics and Policy 12(1), 2018.
- Conklin, J. & Begeman, M.L. — *gIBIS: A Hypertext Tool for
  Exploratory Policy Discussion.* ACM TOIS 6(4), 1988.
- de Kleer, J. — *An Assumption-based TMS.* Artificial Intelligence
  28(2), 1986.
- Degani, A. & Wiener, E. — *Human Factors of Flight-Deck Checklists:
  The Normal Checklist.* NASA CR-177549, 1990.
  https://ntrs.nasa.gov/citations/19910017830
- Dewar, J.A. — *Assumption-Based Planning.* RAND MR-114, 1993;
  Cambridge University Press, 2002.
- Dhami, M., Belton, I. & Mandel, D. — *The "Analysis of Competing
  Hypotheses" in Intelligence Analysis.* Applied Cognitive Psychology
  33(6), 2019; Mandel, D., Karvetski, C. & Dhami, M. — Judgment and
  Decision Making 13(6), 2018.
- DiMaggio, P. & Powell, W. — *The Iron Cage Revisited: Institutional
  Isomorphism and Collective Rationality in Organizational Fields.*
  American Sociological Review 48(2), 1983.
- Ding, J. et al. — *Understanding World or Predicting Future? A
  Comprehensive Survey of World Models.* ACM Computing Surveys 58(3),
  2025; arXiv:2411.14499.
- Doyle, J. — *A Truth Maintenance System.* Artificial Intelligence
  12(3), 1979.
- Dung, P. M. — *On the Acceptability of Arguments and its Fundamental
  Role in Nonmonotonic Reasoning, Logic Programming and n-Person
  Games.* Artificial Intelligence 77(2), 1995.
- Dunlosky, J., Rawson, K., Marsh, E., Nathan, M. & Willingham, D. —
  *Improving Students' Learning with Effective Learning Techniques.*
  Psychological Science in the Public Interest 14(1), 2013.
- Efron, B. & Morris, C. — *Data Analysis Using Stein's Estimator and
  Its Generalizations.* JASA 70(350), 1975.
- Erman, L.D., Hayes-Roth, F., Lesser, V.R. & Reddy, D.R. — *The
  Hearsay-II Speech-Understanding System: Integrating Knowledge to
  Resolve Uncertainty.* ACM Computing Surveys 12(2), 1980.
- Ettinger, A. — *What BERT Is Not: Lessons from a New Suite of
  Psycholinguistic Diagnostics.* TACL 8, 2020; Truong, T. et al. —
  *Language Models Are Not Naysayers.* \*SEM 2023.
- Eugster, P., Felber, P., Guerraoui, R. & Kermarrec, A.-M. — *The Many
  Faces of Publish/Subscribe.* ACM Computing Surveys 35(2), 2003. (Its
  type-based variant: Eugster et al., *Type-Based Publish/Subscribe*,
  ACM TOPLAS.)
- Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M. & Bouchachia, A.
  — *A Survey on Concept Drift Adaptation.* ACM Computing Surveys
  46(4), 2014.
- Ganter, B. & Wille, R. — *Formal Concept Analysis: Mathematical
  Foundations.* Springer, 1999.
- Gawande, A. — *The Checklist Manifesto.* Metropolitan Books, 2009.
- Gelman, A. & Loken, E. — *The Statistical Crisis in Science* (the
  garden of forking paths). American Scientist 102(6), 2014.
- GitHub — *Spec Kit: spec-driven development toolkit.*
  https://github.com/github/spec-kit, 2025.
- Gneiting, T. & Raftery, A.E. — *Strictly Proper Scoring Rules,
  Prediction, and Estimation.* JASA 102(477), 2007.
- Google DeepMind — *Genie 3: A New Frontier for World Models.*
  Technical report, August 2025.
  https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/
- Gotel, O. & Finkelstein, A. — *An Analysis of the Requirements
  Traceability Problem.* ICRE '94, 1994.
- Graesser, A. & Person, N. — *Question Asking during Tutoring.*
  American Educational Research Journal 31(1), 1994.
- Gu, Y., Zheng, B. et al. — *Is Your LLM Secretly a World Model of the
  Internet? Model-Based Planning for Web Agents (WebDreamer).*
  arXiv:2411.06559, 2024; TMLR 2025.
- Guan, L., Valmeekam, K., Sreedharan, S. & Kambhampati, S. —
  *Leveraging Pre-trained Large Language Models to Construct and
  Utilize World Models for Model-based Task Planning.* NeurIPS 2023;
  arXiv:2305.14909.
- Gurnee, W. & Tegmark, M. — *Language Models Represent Space and
  Time.* ICLR 2024; arXiv:2310.02207.
- Ha, D. & Schmidhuber, J. — *World Models.* arXiv:1803.10122, 2018;
  NeurIPS 2018 as *Recurrent World Models Facilitate Policy Evolution*.
- Ha et al. — *MemGuard: typed functional roles against heterogeneous
  memory contamination.* arXiv:2605.28009, 2026.
- Haasnoot, M., Kwakkel, J., Walker, W. & ter Maat, J. — *Dynamic
  Adaptive Policy Pathways: A Method for Crafting Robust Decisions for
  a Deeply Uncertain World.* Global Environmental Change 23(2), 2013.
- Hafner, D., Pasukonis, J., Ba, J. & Lillicrap, T. — *Mastering
  Diverse Domains through World Models (DreamerV3).* arXiv:2301.04104,
  2023; published as *Mastering diverse control tasks through world
  models*, Nature, 2025.
- Halawi, D., Zhang, F., Yueh-Han, C. & Steinhardt, J. — *Approaching
  Human-Level Forecasting with Language Models.* NeurIPS 2024;
  arXiv:2402.18563.
- Halfaker, A., Geiger, R.S., Morgan, J. & Riedl, J. — *The Rise and
  Decline of an Open Collaboration System.* American Behavioral
  Scientist 57(5), 2013.
- Hansson, S. O. — *A Textbook of Belief Dynamics.* Kluwer, 1999.
- Hao, S., Gu, Y., Ma, H., Hong, J., Wang, Z., Wang, D. & Hu, Z. —
  *Reasoning with Language Model is Planning with World Model (RAP).*
  EMNLP 2023; arXiv:2305.14992.
- Haran, U., Moore, D. & Morewedge, C. — *A Simple Remedy for
  Overprecision in Judgment.* Judgment and Decision Making 5(7), 2010.
- Hart, H.L.A. — *The Concept of Law.* Clarendon Press, 1961.
- Hayes, P. — *The Logic of Frames.* In *Frame Conceptions and Text
  Understanding*, 1980.
- Haynes, A.B. et al. — NEJM 360, 2009; Urbach, D.R. et al. — NEJM 370,
  2014. (The surgical-checklist effect and its failed replication at
  scale.)
- Hirt, E. & Markman, K. — *Multiple Explanation: A
  Consider-an-Alternative Strategy for Debiasing Judgments.* JPSP
  69(6), 1995.
- HL7 — *Arden Syntax for Medical Logic Systems*, editions 1992–present
  (https://www.hl7.org/implement/standards/product_brief.cfm?product_id=372);
  Hripcsak, G. — *Writing Arden Syntax Medical Logic Modules.*
  Computers in Biology and Medicine 24(5), 1994.
- Hofman, J.M., Chatzimparmpas, A., Sharma, A., Watts, D.J. & Hullman,
  J. — *Pre-registration for Predictive Modeling.* arXiv:2311.18807,
  2023.
- Honda, K., Vasconcelos, V. & Kubo, M. — *Language Primitives and Type
  Discipline for Structured Communication-Based Programming.* ESOP
  1998.
- Hong, K., Troynikov, A. & Huber, J. — *Context Rot: How Increasing
  Input Tokens Impacts LLM Performance.* Chroma technical report, July
  2025.
- Horty, J., Thomason, R. & Touretzky, D. — *A Skeptical Theory of
  Inheritance in Nonmonotonic Semantic Networks.* Artificial
  Intelligence 42(2–3), 1990.
- Huang, J. et al. — *Large Language Models Cannot Self-Correct
  Reasoning Yet.* ICLR 2024; arXiv:2310.01798.
- ISO/IEC 27001:2022 — clause 6.1.3(d), the Statement of Applicability;
  ISO 9001:2015 — clause 4.3, the scope statement. (Described from
  certification practice.)
- James, W. & Stein, C. — *Estimation with Quadratic Loss.* Proc. 4th
  Berkeley Symposium, 1961.
- jylin04 et al. — *OthelloGPT Learned a Bag of Heuristics.* AI
  Alignment Forum, July 2024. (Interim report; cited as the
  deflationary side of the implicit-world-model debate.)
- Kalyuga, S., Ayres, P., Chandler, P. & Sweller, J. — *The Expertise
  Reversal Effect.* Educational Psychologist 38(1), 2003.
- Karger, E., Bastani, H., Yueh-Han, C., Jacobs, Z., Halawi, D., Zhang,
  F. & Tetlock, P.E. — *ForecastBench: A Dynamic Benchmark of AI
  Forecasting Capabilities.* ICLR 2025. https://www.forecastbench.org
- Karpathy, A. — *On system prompt learning.* X, May 10, 2025.
- Keiser, N. & Arthur, W., Jr. — *A Meta-Analysis of the Effectiveness
  of the After-Action Review.* Journal of Applied Psychology 106(7),
  2021.
- Kiczales, G. et al. — *Aspect-Oriented Programming.* ECOOP 1997.
- Kiela, D. et al. — *Dynabench: Rethinking Benchmarking in NLP.* NAACL
  2021.
- Kim, Y. et al. — *InvThink: Premortem Reasoning for Safer Language
  Models.* arXiv:2510.01569, 2025 (revised 2026).
- King, A. — *Parse, Don't Validate.* 2019.
  https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/
- Kiro (AWS) — *Steering.* https://kiro.dev/docs/steering/, 2025.
- Koppen, C. & Störzer, M. — *PCDiff: Attacking the Fragile Pointcut
  Problem.* European Interactive Workshop on Aspects in Software, 2004.
- Kruchten, P. — *An Ontology of Architectural Design Decisions.* 2004.
- Kubernetes documentation — *Object Names and IDs* (names vs UIDs);
  *Controllers* (spec/status). https://kubernetes.io/docs/
- Laird, J.E., Rosenbloom, P.S. & Newell, A. — *Chunking in Soar: The
  Anatomy of a General Learning Mechanism.* Machine Learning 1(1),
  1986.
- Larsen, T., Endo, B., Yee, A. & Do, T. — CBE—Life Sciences Education,
  2022. (Cited by venue and year; the revised Bloom taxonomy's
  dimension-independence test over 940 assessment items.)
- Lee, J. — *Design Rationale Systems: Understanding the Issues.* IEEE
  Expert 12(3), 1997.
- Lenat, D.B. — *CYC: A Large-Scale Investment in Knowledge
  Infrastructure.* CACM 38(11), 1995.
- Letta — *Sleep-time compute.* letta.com, 2025; see also *Sleep-time
  Compute: Beyond Inference Scaling at Test-time.* arXiv:2504.13171,
  2025.
- Li, K., Hopkins, A.K., Bau, D., Viégas, F., Pfister, H. & Wattenberg,
  M. — *Emergent World Representations: Exploring a Sequence Model
  Trained on a Synthetic Task.* ICLR 2023; arXiv:2210.13382.
- Lord, C., Lepper, M. & Preston, E. — *Considering the Opposite: A
  Corrective Strategy for Social Judgment.* JPSP 47(6), 1984.
- Lou, D. & Polk, C. — *Comomentum: Inferring Arbitrage Activity from
  Return Correlations.* Review of Financial Studies 35(7), 2022.
- Luo, J. et al. — *From Storage to Experience: A Survey on the
  Evolution of LLM Agent Memory Mechanisms.* arXiv:2605.06716, Findings
  of ACL 2026.
- Madaan, A. et al. — *Self-Refine: Iterative Refinement with
  Self-Feedback.* NeurIPS 2023; arXiv:2303.17651.
- McNamara, P. & Van De Putte, F. — *Deontic Logic.* Stanford
  Encyclopedia of Philosophy.
- Metaculus — *AI Forecasting Benchmark Series*, quarterly results
  2024–2025. https://www.metaculus.com/aib/
- Meyer, J.W. & Rowan, B. — *Institutionalized Organizations: Formal
  Structure as Myth and Ceremony.* American Journal of Sociology 83(2),
  1977.
- MINJA — *Memory Injection Attacks on LLM Agents.* arXiv:2503.03704,
  2025.
- Minsky, M. — *A Framework for Representing Knowledge.* In Winston
  (ed.), *The Psychology of Computer Vision*, 1975.
- Mitchell, D., Russo, J. & Pennington, N. — *Back to the Future:
  Temporal Perspective in the Explanation of Events.* Journal of
  Behavioral Decision Making 2(1), 1989.
- Mitchell, M. — *LLMs and World Models*, Parts 1–2. AI: A Guide for
  Thinking Humans, February 2025.
  https://aiguide.substack.com/p/llms-and-world-models-part-1
- Mitchell, T. et al. — *Never-Ending Learning.* Communications of the
  ACM 61(5), 2018.
- Mullen, B., Johnson, C. & Salas, E. — *Productivity Loss in
  Brainstorming Groups: A Meta-Analytic Integration.* Basic and Applied
  Social Psychology 12(1), 1991.
- Murphy, A.H. — *A New Vector Partition of the Probability Score.*
  Journal of Applied Meteorology 12, 1973.
- NARA — 36 CFR Part 1220 (non-record materials) and § 1222.12 (working
  files as records); NARA Bulletin 2013-03.
- Nii, H.P. — *Blackboard Systems.* AI Magazine 7(2)–(3), 1986.
- Nonaka, I. — *A Dynamic Theory of Organizational Knowledge Creation.*
  Organization Science 5(1), 1994.
- Nosek, B.A., Ebersole, C.R., DeHaven, A.C. & Mellor, D.T. — *The
  Preregistration Revolution.* PNAS 115(11), 2018.
- Nygard, M. — *Documenting Architecture Decisions.* November 2011.
- Olken, B.A. — *Promises and Perils of Pre-Analysis Plans.* Journal of
  Economic Perspectives, 2015.
- Ovadia, O. et al. — *Fine-Tuning or Retrieval? Comparing Knowledge
  Injection in LLMs.* arXiv:2312.05934; EMNLP 2024.
- OWASP — *Agentic AI Top 10: ASI06, Memory and Context Poisoning.*
  2026.
- Packer, C. et al. — *MemGPT: Towards LLMs as Operating Systems.*
  arXiv:2310.08560, 2023.
- Paleka, D. et al. — *Consistency Checks for Language Model
  Forecasters.* arXiv:2412.18544, 2024.
- Parasuraman, R. & Riley, V. — *Humans and Automation: Use, Misuse,
  Disuse, Abuse.* Human Factors 39(2), 1997.
- Park, J.S. et al. — *Generative Agents: Interactive Simulacra of
  Human Behavior.* arXiv:2304.03442, 2023.
- Pearl, J. — *Causality*, 2nd ed. Cambridge University Press, 2009.
- Pollock, J. — *A Theory of Defeasible Reasoning* (1991); *Defeasible
  Reasoning with Variable Degrees of Justification.* Artificial
  Intelligence 133, 2001.
- Poole, D. — *On the Comparison of Theories: Preferring the Most
  Specific Explanation.* IJCAI-85, 1985.
- Popper, K. — *The Logic of Scientific Discovery.* 1934/1959.
- Poppendieck, M. & Poppendieck, T. — *Lean Software Development: An
  Agile Toolkit.* Addison-Wesley, 2003.
- Prentice, R.L. — *Surrogate Endpoints in Clinical Trials: Definition
  and Operational Criteria.* Statistics in Medicine 8, 1989.
- Procida, D. — *Diátaxis.* https://diataxis.fr/, 2020.
- Rasmussen, P. et al. — *Zep: A Temporal Knowledge Graph Architecture
  for Agent Memory.* arXiv:2501.13956, 2025.
- Richens, J., Everitt, T. & Abel, D. — *General Agents Need World
  Models.* ICML 2025.
- Roose, K., Lehman, S. & Veinott, E. — Proceedings of the Human
  Factors and Ergonomics Society 67(1), 2023. (Cited by venue and year;
  the premortem plan-revision field study.)
- Schandelmaier, S., Briel, M., Varadhan, R. et al. — *Development of
  the Instrument to Assess the Credibility of Effect Modification
  Analyses (ICEMAN) in Randomized Controlled Trials and Meta-analyses.*
  CMAJ 192(32), 2020.
- Schoenegger, P., Tuminauskaite, I., Park, P.S., Bastos, R.V.S. &
  Tetlock, P.E. — *Wisdom of the Silicon Crowd: LLM Ensemble Prediction
  Capabilities Rival Human Crowd Accuracy.* Science Advances 10(45),
  2024.
- Sclar, M., Choi, Y., Tsvetkov, Y. & Suhr, A. — *Quantifying Language
  Models' Sensitivity to Spurious Features in Prompt Design.* ICLR
  2024; arXiv:2310.11324.
- Shai, A., Marzen, S.E., Teixeira, L., Oldenziel, A. & Riechers, P.M.
  — *Transformers Represent Belief State Geometry in their Residual
  Stream.* NeurIPS 2024; arXiv:2405.15943.
- Shen, L. et al. — *Do Pretrained Transformers Learn In-Context by
  Gradient Descent?* ICML 2024; arXiv:2310.08540.
- Shingo, S. — *Zero Quality Control: Source Inspection and the
  Poka-Yoke System.* Productivity Press, 1986.
- Shinn, N. et al. — *Reflexion: Language Agents with Verbal
  Reinforcement Learning.* arXiv:2303.11366, 2023.
- Simpson, E.H. — *The Interpretation of Interaction in Contingency
  Tables.* JRSS B 13(2), 1951.
- Singer, R. — *Shape Up: Stop Running in Circles and Ship Work that
  Matters.* Basecamp, 2019. https://basecamp.com/shapeup
- Smyth, B. & Keane, M. — *Remembering to Forget: A
  Competence-Preserving Case Deletion Policy for Case-Based Reasoning
  Systems.* IJCAI 1995.
- Strom, R. & Yemini, S. — *Typestate: A Programming Language Concept
  for Enhancing Software Reliability.* IEEE TSE 12(1), 1986.
- Sun, X., Briel, M., Walter, S.D. & Guyatt, G.H. — *Is a Subgroup
  Effect Believable? Updating Criteria to Evaluate the Credibility of
  Subgroup Analyses.* BMJ 340:c117, 2010.
- Tam, Z.R. et al. — *Let Me Speak Freely? A Study on the Impact of
  Format Restrictions on Performance.* EMNLP 2024 Industry;
  arXiv:2408.02442.
- Touretzky, D. — *The Mathematics of Inheritance Systems.* Morgan
  Kaufmann, 1986.
- *United States v. Detroit Timber & Lumber Co.*, 200 U.S. 321 (1906).
- U.S. Army — *A Leader's Guide to After-Action Reviews.* Training
  Circular 25-20, 1993.
- U.S. Government — *A Tradecraft Primer: Structured Analytic
  Techniques for Improving Intelligence Analysis.* 2009.
  https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf
- Vafa, K., Chen, J.Y., Rambachan, A., Kleinberg, J. & Mullainathan, S.
  — *Evaluating the World Model Implicit in a Generative Model.*
  NeurIPS 2024; arXiv:2406.03689.
- Vafa, K., Chang, P.G., Rambachan, A. & Mullainathan, S. — *What Has a
  Foundation Model Found? Using Inductive Bias to Probe for World
  Models.* ICML 2025, PMLR 267; arXiv:2507.06952.
- von Wright, G.H. — *Norm and Action: A Logical Enquiry.* Routledge,
  1963.
- W3C — *SHACL: Shapes Constraint Language*, 2017.
  https://www.w3.org/TR/shacl/
- Walley, P. — *Statistical Reasoning with Imprecise Probabilities.*
  Chapman & Hall, 1991.
- Walsh, J.P. & Ungson, G.R. — *Organizational Memory.* Academy of
  Management Review 16(1), 1991.
- Wang, D., Hagger, M. & Chatzisarantis, N. — *Ironic Effects of
  Thought Suppression: A Meta-Analysis.* Perspectives on Psychological
  Science 15(3), 2020.
- Wang, G. et al. — *Voyager: An Open-Ended Embodied Agent with Large
  Language Models.* arXiv:2305.16291, 2023.
- Wang, R., Todd, G., Xiao, Z., Yuan, X., Côté, M.-A., Clark, P. &
  Jansen, P. — *Can Language Models Serve as Text-Based World
  Simulators?* ACL 2024 (short); arXiv:2406.06485.
- Wegner, D.M. — *Transactive Memory: A Contemporary Analysis of the
  Group Mind.* In *Theories of Group Behavior*, Springer, 1987.
- Wei, J. et al. — *Inverse Scaling Can Become U-Shaped.* EMNLP 2023.
- WFD/Agora — practitioner guide on sunset clauses and post-legislative
  scrutiny, 2022. (Cited from secondary summaries.)
- *When Continual Learning Moves to Memory* — on forgetting relocated
  into retrieval and instance-versus-insight transfer. arXiv:2604.27003,
  2026.
- Wilie, B., Cahyawijaya, S., Ishii, E., He, J. & Fung, P. — *Belief
  Revision: The Adaptability of Large Language Models Reasoning.* EMNLP
  2024; arXiv:2406.19764.
- Winkler, R.L. — *Evaluating Probabilities: Asymmetric Scoring Rules.*
  Management Science 40(11), 1994.
- Witkowski, J., Freeman, R., Vaughan, J.W., Pennock, D.M. & Krause, A.
  — *Incentive-Compatible Forecasting Competitions.* Management
  Science, 2022; arXiv:2101.01816.
- Woods, W. — *What's in a Link: Foundations for Semantic Networks.* In
  *Representation and Understanding*, 1975.
- Xu, W. et al. — *Pride and Prejudice: LLM Amplifies Self-Bias in
  Self-Refinement.* arXiv:2402.11436, 2024.
- Xu, W., Liang, Z., Mei, K., Gao, H., Tan, J. & Zhang, Y. — *A-MEM:
  Agentic Memory for LLM Agents.* arXiv:2502.12110, 2025.
- Yang, C. et al. — *Large Language Models as Optimizers (OPRO).*
  arXiv:2309.03409, 2023.
- Yao, Y., Vehtari, A., Simpson, D. & Gelman, A. — *Using Stacking to
  Average Bayesian Predictive Distributions.* Bayesian Analysis 13(3),
  2018.
- Yao, Y., Pirš, G., Vehtari, A. & Gelman, A. — *Bayesian Hierarchical
  Stacking: Some Models Are (Somewhere) Useful.* Bayesian Analysis
  17(4), 2022.
- Yuan, Y. & Søgaard, A. — *Revisiting the Othello World Model
  Hypothesis.* arXiv:2503.04421, 2025; ICLR 2025.
- Yuan, Su & Yao — *Diagnosing Retrieval vs. Utilization Bottlenecks in
  LLM Agent Memory.* arXiv:2603.02473, 2026.
- Yuksekgonul, M. et al. — *TextGrad: Automatic "Differentiation" via
  Text.* arXiv:2406.07496, 2024.
- Zhang, S. et al. — *Which Agent Causes Task Failures and When?
  (Who&When).* arXiv:2505.00212, 2025.
- Zhao, A. et al. — *ExpeL: LLM Agents Are Experiential Learners.* AAAI
  2024; arXiv:2308.10144.
- Zheng, H.S. et al. — *Take a Step Back: Evoking Reasoning via
  Abstraction in Large Language Models.* arXiv:2310.06117, 2023.
- Zimmermann, O. — *How to Create Architectural Decision Records (ADRs)
  — and How Not To.* 2023, updated 2025.

---

*Provenance note. This paper is the consolidated statement of the
Governed Corpus Evolution doctrine, distilled from production
deployments spanning two payload classes — process knowledge and
world-facing domain beliefs — two of them world-facing corpora run at
population scale under one calibrating judge. Deployment claims herein
are experience reports, not measured results — censuses, checkpoint
classifications, and lexicon histories, never rates; literature claims
carry their own citations. Where a novelty claim rests on absence, its
posture is a directed review that failed to locate, scoped where stated
(§ 15). The doctrine's sharpest open test is the one § 17 names: a
doctrine-blind adoption under an independent calibrating judge.*
