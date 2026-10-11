# Munchhausen

**An agent harness that admits a learned rule only when an outside authority's figures reproduce it out of sample.**
Built in one day for the [MongoDB SF Hackathon](https://cerebralvalley.ai/e/mongodb-sftw-hackathon), on MongoDB Atlas.

> Baron Munchausen swore he pulled himself out of a swamp by his own hair. An agent that grades itself is the
> Baron. This harness checks his story against someone else's numbers.

## The problem

An agent that learns only from itself learns only what its prior already holds. Self-critique, "act as the
expert" prompting and self-graded memory share three blind spots:

1. **Counter-prior facts.** The local truth contradicts a confident convention, and reflection reinforces the convention.
2. **Uninferable constants.** Thresholds, code sets, fees and offsets can't be reasoned out; they have to be measured.
3. **World shift.** After the world changes, a self-graded agent checks each answer with the same stale rule that
   produced it, and stays confidently wrong.

Munchhausen gives the agent an outside signal (the figure a stakeholder *expected* when the agent missed), and
puts a gate between that signal and the agent's memory.

## How it works

A data agent answers business questions over a MongoDB dataset whose meaning lives in hidden tribal knowledge
("an active customer is status 2 or 7", "revenue is net of a 0.5% fee", "rows with `rs = 3` are withdrawn").
When it misses, an **authority** returns the figure it expected. Then:

1. **Observe.** Each miss becomes an observation: what the agent did, what the authority expected, and how far apart they are.
2. **Shape.** Every round (30 episodes) the episodic pass groups observations into *shapes*: misses that look like
   one cause across several question templates. A shape must clear a bar (enough observations, at least two
   templates, a direction read showing the misses concentrate there).
3. **Nominate.** A nominator model drafts one decision that would settle the shape, with a read-only tool on the
   world. One template is held out of what it sees.
4. **Adjudicate.** Cheapest layer first: shape and language checks (L0–L1), a lens panel that is recorded but never
   trusted (L2–L3), then the dispositive layer:
5. **Paired backtest (L4).** Past episodes the authority already confirmed are replayed with and without the
   draft. The draft is admitted only if it **fixes** misses (including at least one on the held-out template) and
   **breaks** no answers that were right. Otherwise it's refused, or held until a new template arrives.
6. **Consult through hooks.** An admitted decision reaches the agent only when the question's terms match its
   hook. No semantic top-k leaks it into unrelated questions.
7. **Revisit.** Every decision carries a revisit trigger that reads residuals against the authority. When the
   world drifts, the trigger fires and a backtested successor supersedes it, leaving a tombstone, never an overwrite.
8. **Floors become views.** A guardrail decision ("exclude withdrawn batches") becomes a MongoDB view, and the
   agent's tool access is rewired to it, so the agent can't forget it.

The claim is deliberately narrow: **the backtest reads the authority, not the world.** An authority that is wrong
the same way every time would pass it.

## The experiment: five arms, same questions

| Arm | Outside signal | How it learns | How it recalls |
|---|---|---|---|
| `frozen` | none | doesn't | — (the paired baseline) |
| `self_ref` | none | grades itself, writes a lesson on a self-judged miss | semantic top-k |
| `naive` | authority | one lesson per miss, admitted directly | semantic top-k |
| `ungated` | authority | `governed`'s shaping and nominator, admitted without the gate | hooks |
| `governed` | authority | shaping → nominator → adjudicator → paired backtest | hooks |

Every arm answers the same stream of questions in the same order, so arms are compared as **paired differences
with bootstrap intervals**. `governed − ungated` differ only in the gate, so that pair isolates what governance adds.
Forecasts are registered in the run record before a run starts and printed beside their readings; a disagreement stands.

## Results (2026-10-11)

Two runs of 600 questions per arm: **Run A** (honest authority, a drift at episode 300 that changes what "active
customer" means) and **Run B** (the same, with the authority lying on 20% of its corrections). Full reports with
every figure's population and query: [`docs/evidence/run-a`](docs/evidence/run-a/report.md), [`docs/evidence/run-b`](docs/evidence/run-b/report.md).

- **Learning from the authority works.** On a sealed set of 40 questions never used for learning, read on the
  end-of-run stores: `frozen` 14/40, `self_ref` 13, `naive` 19 (Run A), `ungated` 36, `governed` 29 (Run A) and 25 (Run B).
  `governed` beat `naive` on quirk questions after the drift (F5: +0.23 [+0.17, +0.28] in Run A, +0.15 in Run B).
- **Self-grading learns nothing.** `self_ref` stored 339 decisions in Run A; none maps to a real quirk.
- **The drift beat landed.** `governed` admitted the active-customer rule at 60, its trigger fired 7 episodes after
  the drift, it refused three wrong successors, and admitted the right one at 450.
- **The gate cost more than it bought in this world.** Pre-registered F6 (`governed` above `ungated`) disagreed:
  −0.22 [−0.27, −0.16] in Run A, −0.47 [−0.52, −0.42] in Run B. Before the drift the two were level; the gap
  opened in recovery. In Run B random lies never formed a coherent wrong rule in any arm, so the gate's
  protection was never needed, while `governed` lost two quirks to its own shaping (see Limits).
- **The case the gate exists for.** The same injected lie was refused by `governed` (fixed 0 of 8 replays) and
  admitted by `ungated`, where it superseded the correct rule and took it from 36/40 to 29/40 on the sealed set.
  One demonstration per arm, not a statistic.

## Key features

**Governance**
- Entry contract on every decision: warrant (the backtest that admitted it), hook, revisit trigger, scope, residue.
- Paired out-of-sample backtest with a held-out template fold and hold-to-accrue.
- Hook-only consultation with `not_this` exclusions and persona scope.
- Revisit triggers, dispositive fires, supersession with tombstones, lineage you can query (`munchhausen why active_customer`).
- Decisions are frozen at admission; only lifecycle fields change, through six lifecycle functions.

**MongoDB Atlas**
- Gold isolation enforced by **database roles**, not convention: the learner can't read `truth` (`munchhausen verify-roles`).
- **Multi-document transactions** for admission (successor in, predecessor flipped, fires disposed, tool access rewired, in one commit).
- **Views** as tool access for floor decisions.
- **Atlas Search** with a synonyms collection compiled from the term vocabulary, plus a multikey index for hook matching.
- **Vector Search** (Voyage `voyage-4` embeddings, `rerank-3`) for the `naive`/`self_ref` recall and the nominator's neighbours, with an embedding cache in Atlas.
- **Change streams** with pre/post images drive the live viewer.
- `$merge` round records, `$facet` + `$sample` for the backtest's balanced sample, `$setWindowFields`/`$densify` for curves, `$graphLookup` for lineage.
- **Time-series** collection for per-call model spend; **TTL** leases so interrupted runs resume without a scan.

**Evidence**
- Every reading names its population, n, interval and the query that produced it.
- A planted-truth map (an Opus judge, evaluation only) says which stored decisions correspond to a real quirk.
- Live operator view with alarms (`munchhausen status`), and a viewer with replay, injection and `why`.

## Running it

### Prerequisites

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- A MongoDB Atlas cluster with the **`sample_analytics`** sample dataset loaded
- An Anthropic API key and a Voyage AI key (paid tier; the free tier's 3 RPM is too slow)
- Optional: a Raindrop write key (trace sink), a TypeSafe key (lens panel)

### Install and check

```bash
uv sync --all-packages
uv run pytest                     # ~440 tests, including architecture rules
cp .env.example .env              # fill MONGODB_URI and the model keys
uv run munchhausen doctor         # which knobs and keys are set (never prints values)
uv run munchhausen ping           # Atlas connectivity and server capabilities
```

No Atlas yet? `uv run munchhausen viewer --synthetic` and `uv run munchhausen report-demo` run on a synthetic run
with no database and no model calls.

### Prepare the world (once)

```bash
uv run munchhausen setup          # collections, validators, indexes, search indexes
uv run munchhausen build-world    # materialize `world` + sealed `truth` from sample_analytics (deterministic)
```

Optional but recommended: create the three per-role database users described in `.env.example`
(`MONGODB_URI_LEARNER`, `_EVALUATOR`, `_EXECUTOR`) and check them with `uv run munchhausen verify-roles`.
Without them every role falls back to `MONGODB_URI` and isolation is by convention.

### Run an experiment

```bash
RUN_ID=my-run WORKERS_PER_ARM=10 uv run munchhausen run --length 600     # all five arms, concurrently
uv run munchhausen status my-run --length 600 --watch                    # progress + ALARM lines
```

A 600-episode run took about 35–40 minutes with 10 workers per arm, and $4–8 per learning arm at list price
(`frozen` costs under $1). Runs resume from
their cursors if interrupted. Pick arms with `--arm governed --arm ungated`.

Every knob lives in [`engine/munchhausen/config.py`](engine/munchhausen/config.py) and can be set as an
upper-case environment variable (`D1_AT`, `ROUND_SIZE`, `AUTHORITY_POISON_RATE`, model ids…). Arms and
forecasts live in [`engine/conf/`](engine/conf/); point `CONF_DIR` elsewhere for a variant, as Run B did:

```bash
RUN_ID=my-run-b CONF_DIR=$PWD/engine/conf/run-b AUTHORITY_POISON_RATE=0.20 uv run munchhausen run --length 600
```

### Read the results

```bash
uv run munchhausen planted-map my-run              # evaluation only: map decisions to planted quirks (Opus)
uv run munchhausen report my-run --against my-run-b
# → var/reports/my-run/{report.md, report.html, readings.json, manifest.json}
uv run munchhausen viewer --run my-run             # http://127.0.0.1:8766
RUN_ID=my-run uv run munchhausen why active_customer   # lineage of a decision or term
```

To use the viewer's injection beat (feed a false authority figure and watch the gate), start the viewer with
`RUN_ID` set to the run you're viewing; injection only writes to the engine's own run.

## Repository layout

```
engine/munchhausen/
  domain/    pure models and invariants (entry contract, lifecycle, backtest read, admission plan)
  ports/     Protocols for every seam; registry maps implementation names → classes
  agent/ loop/ learn/ metrics/   application services (forward pass, backward pass, readings)
  world/ truth/   evaluation side (hidden tags, gold), reached only through the World port
  store/     Atlas (the only pymongo importer)
  impl/      vendor implementations (Anthropic, Voyage, TypeSafe, Raindrop)
engine/conf, engine/packs   arms, forecasts, lenses; the quirk pack `analytics-v1`
viewer/      the live viewer
docs/evidence/   exported run reports
```

## Limits and known weaknesses

Found in the runs and written up with proposed fixes in [`corpus/LESSONS.md`](corpus/LESSONS.md) §§ 9–12:
- The backtest samples from a rule's source questions, not from everything its hook reaches, so an over-broad
  rule can miss on questions it was never tested on.
- Revisit triggers read consistent rounding residuals as drift.
- Shaping can split one multi-template quirk into single-template shapes that never clear the bar.
- A refused draft returns its evidence unmarked, so poisoned observations get re-drafted.
- The sealed verification set is 40 questions; intervals are wide, and its questions are new instances of known templates.

## Further reading

- [`SPEC.md`](SPEC.md): the design
- [`corpus/LANGUAGE.md`](corpus/LANGUAGE.md): the lexicon (one meaning per term)
- [`CARRY_FORWARD.md`](CARRY_FORWARD.md): build log, binding decisions, run readings
- [`corpus/EVIDENCE.md`](corpus/EVIDENCE.md): the event catalog
- Concepts are drawn from the GCE doctrine ([`gce/GCE-DOCTRINE.md`](gce/GCE-DOCTRINE.md)), cited as ideas, not shipped code.

## Provenance

Schemas imported from prior projects live under [`prior/`](prior/) in a single commit. Everything under `engine/`
and `viewer/` was written on the day by one person orchestrating parallel Claude Code agents, each surface
adversarially reviewed.

## License

MIT
