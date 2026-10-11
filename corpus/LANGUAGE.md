# LANGUAGE — the register of every sentence the system writes

The one home of the lexicon from M0 on (SPEC § 22). SPEC § 2 is not maintained beside it.
The world's term vocabulary is data in Atlas (`terms`); this file states its rules and never lists its rows.
`munchhausen/lint_language.py` is the mechanical half; its `TELLS` list is the authority for banned tells.

## 0. Lexicon

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

## 1. Purpose

It blocks three drifts, each paired with its countermeasure:
- **Term drift:** a hook written in words the question never presents. The countermeasure is the shared vocabulary and the escape (§ 22.4).
- **State narration:** a payload or observation that describes the run instead of the world. The countermeasure is the laws (§ 22.2).
- **Claim drift:** a README or report sentence wider than the reading behind it. The countermeasure is the claim language (§ 22.6).

## 2. The three laws

Every directive ships as a Do plus its named overshoot (Don't).
- **L1 Run-invariance.** No payload, hook, observation or lens names a run, an arm, an episode index, a party ("the agent", "I", "we") or a moment ("now", "recently", "this round"). A banned-tells table lists each tell with its legal replacement, and the lint's `TELLS` list is the authority.
- **L2 State-invariance.** Every sentence in a record is a premise (it holds until named evidence falsifies it), a dated fact (it carries `at_idx` or an ISO date), or a directive. Records hold no prose about the past; the ledgers hold the past.
- **L3 Bounded directives.** Every Do carries the overshoot it guards against, named as a recognizable case.

### Banned tells (L1)

Mirrors `TELLS` in `munchhausen/lint_language.py`; where the two differ, the code holds.

| Tell | Legal replacement |
|---|---|
| "the agent" | name the field or the population |
| "I", "we", "our", "us" | impersonal present tense |
| "now", "currently", "recently", "this round", "so far", "again" | a dated fact (`at_idx`) or a premise |
| "arm 3", "episode #120", "run 2" | anchor through warrant ids, not prose |
| an arm's name (`governed`, `naive`, …) | never name an arm in a record |

## 3. Lexicon

The closed vocabulary of § 2 (term | means | not to be confused with), extended by Part II: `port`, `representation`, `capability`, `amendment`, `moot`, `converged`, `lease`, `mirror`. A term outside the lexicon enters through the escape `other(<what>)` with a definition, then becomes usable.

## 4. Term vocabulary (the world register)

The vocabulary hooks key on. It lives in the `terms` collection: `{term, aliases[], source: schema|question|authority|nominator, admitted_at_idx, decision_id?}`. It compiles into the `term_synonyms` mapping that `terms_search` reads (§ 20.3).
- A term is a lower-case noun phrase naming how a question **presents** ("active customers", "fiscal quarter", "revenue"), never a definition ("`st` in {2, 7}") and never a quirk id.
- **Seeding:** from the adapter's schema summary (field and collection names) and noun phrases mined from the first `VOCAB_WARMUP` stream questions. It is never seeded from the pack. A test asserts that no pack id, definition string or transform parameter appears in `terms`.
- **Growth:** the nominator proposes a missing term as `other(<term>): <presentation gloss>` inside a draft. The term is admitted with the draft and refused with it. An authority phrasing that names a concept adds an alias, never a term with a definition.
- **No edits:** a term is never renamed. A better word becomes an alias of the old one.

## 5. Voice by surface

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

## 6. The authoring register

One register with two faces, kept apart:
- **Latch language** (the key-space face): key on the presentation, bias broad, build from the vocabulary (§ 6.2's Do/Don't, owned here).
- **Consultation language** (the proposer's prompt): presume the store ("apply each consulted decision whose hook matched"), and report count and provenance through `consulted[]`, never a bare assurance.
- **Lens language** (the adjudicator's prompt): counterfactual pairing, refutation phrasing, stipulated certainty for generative lenses.

A form on the wrong side is the failure. A presumed-existence phrasing on a lens manufactures agreement; a refutation phrasing in the proposer's prompt makes it doubt an admitted decision instead of applying it.

## 7. Claim language

For the README, the report and the demo voice-over:
- A claim is no wider than its reading.
- Every quantity carries a unit, a population and an n.
- A forecast (§ 11) is printed beside its reading, and a disagreement stands as one.
- Status words (admitted, superseded, moot) are the lifecycle values, never synonyms.

## 8. Mechanical checks

`munchhausen/lint_language.py` runs at L0 on every draft and on every observation write:
- the banned tells
- hook terms in vocabulary or escape
- no source figure in the payload
- a non-empty `contrast` on each `not_this` row
- vacuous counterfactual patterns refused in `lenses.yaml` at load

Residue, disclosed: the lint does not check that a payload is true, that a hook is a good net, or that a counterfactual names a real overshoot.
