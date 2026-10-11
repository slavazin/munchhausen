"""Readings (SPEC § 11). Evaluation side; pure over rows fetched by `EvidenceRepository.snapshot`.

Every reading returns `{name, value, unit, population, n, interval?, level?, query, note?}` (`Reading`):
a figure is re-derivable from Atlas by its `query` (the snapshot's find over a named store, then the named
function here). Arms are iterated from `ArmSpec`s; arm names appear only in `conf/forecasts.yaml`.

Conventions (corpus/EVIDENCE.md § 4):
- "stream episodes" = `episodes` with `stream: "stream"`; a first attempt is `correct`; self-assessed accuracy
  is the mean `confidence`; the calibration gap is mean(confidence − correct), in accuracy points.
- Arms share the stream by index, so an arm-vs-arm comparison is paired on `idx` (`metrics/paired.py`).
- A reading without its inputs is `unread` with a note naming what is missing; it never falls back silently.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from munchhausen.domain.arm import ArmSpec, ConsultationMode
from munchhausen.domain.ids import decision_id as _decision_id
from munchhausen.metrics.paired import PairedReading, difference_of_means, paired_difference

Row = dict[str, Any]

SNAPSHOT = "EvidenceRepository.snapshot(run_id)"


def q_find(store: str, filt: str, fn: str) -> str:
    """The named query of a figure: a find over one store of the run, then one function of this module."""
    return f"munchhausen.{store}.find({{run_id: R, {filt}}}) | metrics.readings.{fn}"


@dataclass(frozen=True)
class Reading:
    name: str
    value: Any
    unit: str
    population: str
    n: int
    query: str
    interval: tuple[float, float] | None = None
    level: float | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: _clean(v) for k, v in d.items() if v is not None or k in ("value",)}


def _clean(v: Any) -> Any:
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, tuple):
        return [_clean(x) for x in v]
    return v


@dataclass(frozen=True)
class Context:
    run_id: str
    arms: Mapping[str, ArmSpec]
    round_size: int
    run_length: int
    drift_at: Mapping[str, int]                # drift id → stream index (from the knob the pack names)
    drift_quirk: Mapping[str, str]             # drift id → quirk id it moves
    template_quirk: Mapping[str, str]          # template → its one quirk id (evaluation side, from the pack)
    label_horizon: int
    drift_window: int
    bootstrap_n: int
    ci_level: float
    seed: int
    premise_first: int
    premise_share: float
    forecasts: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    rolling_window: int = 90                   # PAIRED_ROLLING_WINDOW
    notes: tuple[str, ...] = ()                # context caveats printed at the top of the report (e.g. pack hash)


# --- row helpers ------------------------------------------------------------------------------------------


def stream_of(rows: Mapping[str, list[Row]], arm: str) -> list[Row]:
    es = (e for e in rows.get("episodes", []) if e.get("arm") == arm and e.get("stream", "stream") == "stream")
    return sorted(es, key=lambda e: e["idx"])


def _gap(e: Row) -> float:
    return float(e.get("confidence", 0.0)) - (1.0 if e.get("correct") else 0.0)


def _mean(xs: Sequence[float]) -> float:
    return float(sum(xs) / len(xs)) if xs else float("nan")


def admitted_idx(decision: Row, drafts_round: Mapping[str, int], round_size: int) -> int | None:
    """Index at which a decision was admitted: `admitted_at_idx` if the record carries it; else the
    lifecycle index while still admitted; else the end of its draft's round (draft id → decision id)."""
    if decision.get("admitted_at_idx") is not None:
        return int(decision["admitted_at_idx"])
    lc = decision.get("lifecycle", {})
    if lc.get("status") == "admitted":
        return int(lc.get("at_idx", 0))
    r = drafts_round.get(decision["_id"])
    return (r + 1) * round_size - 1 if r is not None else None


def drafts_round(rows: Mapping[str, list[Row]]) -> dict[str, int]:
    """decision id → round of the draft it was minted from."""
    return {_decision_id(d["_id"]): int(d.get("round", 0)) for d in rows.get("drafts", [])}


def mapping(rows: Mapping[str, list[Row]]) -> dict[str, Row]:
    return {m["decision_id"]: m for m in rows.get("planted_map", [])}


def quirk_matches(qid: str | None, prefix: str) -> bool:
    return qid is not None and (qid == prefix or qid.startswith(prefix + "_"))


# --- per arm, per round -----------------------------------------------------------------------------------


def stream_curve(rows: Mapping[str, list[Row]], ctx: Context, arm: str) -> list[dict[str, Any]]:
    """Per round: n scored, n errored, stream accuracy, self-assessed accuracy, calibration gap."""
    by_round: dict[int, list[Row]] = defaultdict(list)
    for e in stream_of(rows, arm):
        by_round[e["idx"] // ctx.round_size].append(e)
    out = []
    for r in sorted(by_round):
        es = [e for e in by_round[r] if not errored(e)]
        acc = _mean([1.0 if e.get("correct") else 0.0 for e in es])
        conf = _mean([float(e.get("confidence", 0.0)) for e in es])
        out.append({"round": r, "idx_lo": r * ctx.round_size, "idx_hi": (r + 1) * ctx.round_size - 1, "n": len(es),
                    "n_error": len(by_round[r]) - len(es), "acc": acc, "conf": conf, "gap": conf - acc})
    return out


def v_points(rows: Mapping[str, list[Row]], arm: str) -> list[dict[str, Any]]:
    """V accuracy per read point (`v_at`, else `idx`), over the sealed V set."""
    by_at: dict[int, list[Row]] = defaultdict(list)
    for e in rows.get("episodes", []):
        if e.get("arm") == arm and e.get("stream") == "v":
            by_at[int(e.get("v_at", e["idx"]))].append(e)
    return [{"at": at, "n": len(es), "acc": _mean([1.0 if e.get("correct") else 0.0 for e in es])}
            for at, es in sorted(by_at.items())]


def arm_summary(rows: Mapping[str, list[Row]], ctx: Context, arm: str) -> list[Reading]:
    all_ = stream_of(rows, arm)
    es = [e for e in all_ if not errored(e)]
    n, n_err = len(es), len(all_) - len(es)
    pop = f"stream episodes of arm {arm} without error ({n_err} errored excluded)"
    q = q_find("episodes", f"arm: '{arm}', stream: 'stream', error: null", "arm_summary")
    acc = _mean([1.0 if e.get("correct") else 0.0 for e in es])
    gap = _mean([_gap(e) for e in es])
    return [
        Reading(f"{arm}.stream_accuracy", acc, "accuracy (fraction)", pop, n, q),
        Reading(f"{arm}.calibration_gap", gap, "accuracy points (mean confidence − accuracy)", pop, n, q),
        Reading(f"{arm}.errored_episodes", n_err, "episodes", f"stream episodes of arm {arm}", len(all_),
                q_find("episodes", f"arm: '{arm}', stream: 'stream', error: {{$ne: null}}", "arm_summary")),
    ]


# --- paired readings (F5, F6) -----------------------------------------------------------------------------


def _pairs(rows: Mapping[str, list[Row]], a: str, b: str, keep: Any
           ) -> tuple[list[float], list[float], list[int], dict[str, int]]:
    """Pairs on `idx` where neither side has `error` and both answered the same `question_id`. Returns the
    dropped counts: errors per arm and question mismatches."""
    ea = {e["idx"]: e for e in stream_of(rows, a) if keep(e)}
    eb = {e["idx"]: e for e in stream_of(rows, b) if keep(e)}
    common = sorted(ea.keys() & eb.keys())
    drop = {f"error.{a}": 0, f"error.{b}": 0, "question_mismatch": 0}
    idx = []
    for i in common:
        if errored(ea[i]) or errored(eb[i]):
            drop[f"error.{a}"] += int(errored(ea[i]))
            drop[f"error.{b}"] += int(errored(eb[i]))
            continue
        if ea[i].get("question_id") != eb[i].get("question_id"):
            drop["question_mismatch"] += 1
            continue
        idx.append(i)
    return ([1.0 if ea[i].get("correct") else 0.0 for i in idx], [1.0 if eb[i].get("correct") else 0.0 for i in idx],
            idx, drop)


def paired_accuracy(rows: Mapping[str, list[Row]], ctx: Context, a: str, b: str, *, population: str,
                    after_round: int, margin: float) -> tuple[Reading, str]:
    after_idx = after_round * ctx.round_size
    if population == "quirk_bearing":
        if not ctx.template_quirk:
            r = Reading(f"paired_accuracy.{a}-{b}", None, "accuracy (fraction)", "unread", 0,
                        q_find("episodes", "stream: 'stream'", "paired_accuracy"),
                        note="pack template→quirk map unavailable: quirk-bearing population cannot be read")
            return r, "unread"
        keep = lambda e: e["idx"] >= after_idx and e.get("template") in ctx.template_quirk  # noqa: E731
        pop = f"quirk-bearing stream questions with idx ≥ {after_idx} (round ≥ {after_round}), paired by idx"
    else:
        keep = lambda e: e["idx"] >= after_idx  # noqa: E731
        pop = f"stream questions with idx ≥ {after_idx}, paired by idx"
    xa, xb, _, drop = _pairs(rows, a, b, keep)
    pr = paired_difference(xa, xb, n_boot=ctx.bootstrap_n, level=ctx.ci_level, seed=ctx.seed)
    return _paired_reading(f"paired_accuracy.{a}-{b}", pr, "accuracy (fraction)", pop + ", same question_id, no error",
                           q_find("episodes", f"arm: {{$in: ['{a}', '{b}']}}, stream: 'stream'",
                                  f"paired_accuracy(a='{a}', b='{b}', after_round={after_round})"),
                           _drop_note(drop)), verdict3(pr, margin)


def _paired_reading(name: str, pr: PairedReading, unit: str, pop: str, query: str, note: str | None = None) -> Reading:
    return Reading(name, pr.diff, unit, pop, pr.n, query, interval=(pr.lo, pr.hi), level=pr.level, note=note)


def verdict3(pr: PairedReading, margin: float, *, proxy: bool = False) -> str:
    """above / within / below the margin; `unread` with no pairs; `unread (proxy)` when the reading's
    population is a proxy (no planted map): a proxy reading never earns an agreement verdict."""
    if pr.n == 0 or math.isnan(pr.diff):
        return "unread"
    if proxy:
        return "unread (proxy)"
    return pr.verdict(margin)


# --- drift readings (F1, F4, stale-applied) -------------------------------------------------------------


def _drift(ctx: Context, drift: str) -> tuple[int, str | None]:
    return ctx.drift_at[drift], ctx.drift_quirk.get(drift)


def pre_drift_holders(rows: Mapping[str, list[Row]], ctx: Context, drift: str, prefix: str
                      ) -> tuple[dict[str, list[Row]], bool]:
    """arm → decisions admitted before the drift and still admitted at it. With a planted map, only decisions
    mapped to the drifting quirk; without one, every such decision (a proxy, flagged by the second value)."""
    at, _ = _drift(ctx, drift)
    pm, dr = mapping(rows), drafts_round(rows)
    mapped = bool(pm)
    out: dict[str, list[Row]] = defaultdict(list)
    for d in rows.get("decisions", []):
        adm = admitted_idx(d, dr, ctx.round_size)
        if adm is None or adm >= at:
            continue
        lc = d.get("lifecycle", {})
        if lc.get("status") != "admitted" and int(lc.get("at_idx", 0)) < at:
            continue                                   # gone before the drift
        if mapped and not quirk_matches(pm.get(d["_id"], {}).get("quirk"), prefix):
            continue
        out[d["arm"]].append(d)
    return out, not mapped


def drift_calibration(rows: Mapping[str, list[Row]], ctx: Context, *, drift: str, prefix: str, reference: str,
                      margin: float) -> list[tuple[Reading, str]]:
    """F1: per holding arm, calibration gap after the drift minus before (two windows of `DRIFT_WINDOW`; the
    after-window ends at the first supersession or retirement of a held decision — a converge does not end
    holding), with the reference arm's difference-in-differences paired by idx beside it. Errored episodes are
    excluded. Without a planted map the holders are a proxy and the verdict is `unread (proxy)`."""
    at, _ = _drift(ctx, drift)
    holders, proxy = pre_drift_holders(rows, ctx, drift, prefix)
    w = ctx.drift_window
    out: list[tuple[Reading, str]] = []
    ref = {e["idx"]: _gap(e) for e in scored_of(rows, reference)} if reference in ctx.arms else {}
    for arm in ctx.arms:
        if arm not in holders:
            continue
        ends = [int(d["lifecycle"]["at_idx"]) for d in holders[arm]
                if d.get("lifecycle", {}).get("status") in ("superseded", "retired")]
        stop = min([at + w, *ends])
        es = scored_of(rows, arm)
        before = [e for e in es if at - w <= e["idx"] < at]
        after = [e for e in es if at <= e["idx"] < stop]
        pr = difference_of_means([_gap(e) for e in after], [_gap(e) for e in before], n_boot=ctx.bootstrap_n,
                                 level=ctx.ci_level, seed=ctx.seed)
        dd = None
        if ref:
            da = [_gap(e) - ref[e["idx"]] for e in after if e["idx"] in ref]
            db = [_gap(e) - ref[e["idx"]] for e in before if e["idx"] in ref]
            rr = difference_of_means(da, db, n_boot=ctx.bootstrap_n, level=ctx.ci_level, seed=ctx.seed)
            dd = (f"{reference}-referenced difference-in-differences {_fmt(rr.diff)} "
                  f"[{_fmt(rr.lo)}, {_fmt(rr.hi)}], n = {rr.n} paired indices per window (smaller)")
        held = ", ".join(d["_id"] for d in holders[arm])
        note = f"held: {held}. " + (dd or f"reference arm {reference} not read") + (
            ". PROXY: no planted map; every decision admitted before the drift counts as held" if proxy else "")
        pop = (f"stream episodes of arm {arm} without error: idx {at - w}…{at - 1} (before) vs {at}…{stop - 1} "
               f"(after); n = smaller window")
        r = _paired_reading(f"F1.{arm}", pr, "accuracy points (calibration gap, after − before)", pop,
                            q_find("episodes", f"arm: '{arm}', stream: 'stream', idx: {{$gte: {at - w}, $lt: {stop}}}",
                                   f"drift_calibration(drift='{drift}')"), note)
        out.append((r, verdict3(pr, margin, proxy=proxy)))
    return out


def resolution_idx(rows: Mapping[str, list[Row]], ctx: Context, arm: str, *, drift: str, prefix: str
                   ) -> tuple[int | None, str, bool]:
    """(index, how, held). The drift is resolved only by a held pre-drift decision `superseded` at or after the
    drift with a successor present in the store; a converge (a merge) or a retirement is not resolution.
    `held` False: the arm never held a pre-drift decision on the drifting quirk."""
    at, _ = _drift(ctx, drift)
    holders, proxy = pre_drift_holders(rows, ctx, drift, prefix)
    ids = {d["_id"] for d in rows.get("decisions", [])}
    held = holders.get(arm, [])
    tag = " (proxy: no planted map)" if proxy else ""
    if not held:
        return None, "never held" + tag, False
    cands = []
    for d in held:
        lc = d.get("lifecycle", {})
        if (lc.get("status") == "superseded" and int(lc.get("at_idx", 0)) >= at
                and lc.get("superseded_by") in ids):
            cands.append((int(lc["at_idx"]), f"{d['_id']} superseded by {lc['superseded_by']}"))
    if not cands:
        statuses = ", ".join(f"{d['_id']} {d.get('lifecycle', {}).get('status')}" for d in held)
        return None, f"held but unresolved ({statuses})" + tag, True
    i, how = min(cands)
    return i, how + tag, True


def drift_latency(rows: Mapping[str, list[Row]], ctx: Context, *, drift: str, prefix: str, a: str,
                  others: Sequence[str], margin: float) -> list[tuple[Reading, str]]:
    """F4: latency (supersession idx − drift idx) per arm; difference other − a, verdict by sign beyond the
    margin. If either arm did not resolve the drift (never held, or held but unresolved) the comparison is
    `unread`, with the reason; a proxy (no planted map) is `unread (proxy)`."""
    at, _ = _drift(ctx, drift)
    _, proxy = pre_drift_holders(rows, ctx, drift, prefix)
    ia, how_a, _ = resolution_idx(rows, ctx, a, drift=drift, prefix=prefix)
    out = []
    for o in others:
        if o not in ctx.arms:
            continue
        io, how_o, _ = resolution_idx(rows, ctx, o, drift=drift, prefix=prefix)
        la = None if ia is None else ia - at
        lo_ = None if io is None else io - at
        if la is None or lo_ is None:
            d, v = None, "unread"
        else:
            d = float(lo_ - la)
            v = "unread (proxy)" if proxy else "above" if d > margin else "below" if d < -margin else "within"
        note = (f"{a}: {la if la is not None else '—'} ({how_a}); {o}: {lo_ if lo_ is not None else '—'} ({how_o}). "
                "One drift event per arm: no interval")
        out.append((Reading(f"F4.{o}-{a}", d, "episodes", f"drift {drift} at idx {at}; arms {o}, {a}",
                            int(d is not None), q_find("decisions", f"arm: {{$in: ['{o}', '{a}']}}",
                                                       f"drift_latency(drift='{drift}')"), note=note), v))
    return out


def stale_applied(rows: Mapping[str, list[Row]], ctx: Context, *, drift: str, prefix: str) -> list[Reading]:
    """Share of eligible stream episodes after the drift that applied a held pre-drift decision. L11: an
    episode is eligible for decision d only at idx ≥ max(drift, admission(d) + LABEL_HORIZON). Denominator:
    eligible episodes on templates of the drifting quirk (all eligible stream episodes without a pack map)."""
    at, quirk = _drift(ctx, drift)
    holders, proxy = pre_drift_holders(rows, ctx, drift, prefix)
    dr = drafts_round(rows)
    out = []
    for arm in ctx.arms:
        held = holders.get(arm, [])
        if not held:
            continue
        starts = {d["_id"]: max(at, (admitted_idx(d, dr, ctx.round_size) or 0) + ctx.label_horizon) for d in held}
        first = min(starts.values())
        es = [e for e in scored_of(rows, arm) if e["idx"] >= first
              and (not ctx.template_quirk or ctx.template_quirk.get(e.get("template")) == quirk)]
        stale = sum(1 for e in es if any(c.get("disposition") == "applied" and c.get("decision_id") in starts
                                         and e["idx"] >= starts[c["decision_id"]] for c in e.get("consulted", [])))
        note = "PROXY: no planted map" if proxy else None
        out.append(Reading(f"stale_applied.{arm}", stale / len(es) if es else None, "share of episodes",
                           f"stream episodes of arm {arm} with idx ≥ {first} on {quirk or 'any'} templates "
                           f"(L11: ≥ LABEL_HORIZON after admission)", len(es),
                           q_find("episodes", f"arm: '{arm}', stream: 'stream'", f"stale_applied(drift='{drift}')"),
                           note=note))
    return out


# --- planted map (F2, F3, recall) -----------------------------------------------------------------------


def planted_count(rows: Mapping[str, list[Row]], ctx: Context, *, prefix: str, expect: Mapping[str, Mapping[str, int]]
                  ) -> tuple[list[Reading], str]:
    pm = {k: m for k, m in mapping(rows).items() if m.get("subject", "decision") == "decision"}
    if not pm:
        return [Reading(f"planted_count.{prefix}", None, "decisions", "unread", 0,
                        q_find("planted_map", "", "planted_count"), note="planted map not run")], "unread"
    counts = Counter(m["arm"] for m in pm.values() if quirk_matches(m.get("quirk"), prefix))
    n_arm = Counter(m["arm"] for m in pm.values())
    out, ok = [], True
    for arm in ctx.arms:
        c = counts.get(arm, 0)
        out.append(Reading(f"planted_count.{prefix}.{arm}", c, "decisions",
                           f"decisions of arm {arm} mapped by the planted-map judge", n_arm.get(arm, 0),
                           q_find("planted_map", f"arm: '{arm}'", f"planted_count(prefix='{prefix}')")))
        e = expect.get(arm, {})
        if ("max" in e and c > e["max"]) or ("min" in e and c < e["min"]):
            ok = False
    missing = sorted(set(expect) - set(ctx.arms))
    if missing:
        return out, "unread"
    return out, "agrees" if ok else "disagrees"


def planted_scope(rows: Mapping[str, list[Row]], ctx: Context, *, prefix: str, expect: Mapping[str, Sequence[str]]
                  ) -> tuple[list[Reading], str]:
    pm = {k: m for k, m in mapping(rows).items() if m.get("subject", "decision") == "decision"}
    if not pm:
        return [Reading(f"planted_scope.{prefix}", None, "decisions", "unread", 0,
                        q_find("planted_map", "", "planted_scope"), note="planted map not run")], "unread"
    out, ok = [], True
    for arm in ctx.arms:
        scopes = sorted({m["scope"] for m in pm.values() if m["arm"] == arm and quirk_matches(m.get("quirk"), prefix)})
        held = scopes or ["none"]
        out.append(Reading(f"planted_scope.{prefix}.{arm}", held, "scope labels",
                           f"decisions of arm {arm} mapped to {prefix}", len(scopes),
                           q_find("planted_map", f"arm: '{arm}'", f"planted_scope(prefix='{prefix}')")))
        if arm in expect and not set(held) <= set(expect[arm]):
            ok = False
    if set(expect) - set(ctx.arms):
        return out, "unread"
    return out, "agrees" if ok else "disagrees"


def quirk_recall(rows: Mapping[str, list[Row]], ctx: Context) -> list[Reading]:
    pm = mapping(rows)
    quirks = sorted(set(ctx.template_quirk.values()))
    if not pm or not quirks:
        return []
    out = []
    for arm in ctx.arms:
        hit = {m["quirk"] for m in pm.values() if m["arm"] == arm and m.get("quirk") in quirks}
        out.append(Reading(f"quirk_recall.{arm}", len(hit) / len(quirks), "share of template quirks",
                           f"template quirks of the pack; decisions of arm {arm}", len(quirks),
                           q_find("planted_map", f"arm: '{arm}'", "quirk_recall"), note=", ".join(sorted(hit)) or None))
    return out


# --- backtests (§ 12 premise) ---------------------------------------------------------------------------


def backtest_summary(rows: Mapping[str, list[Row]], ctx: Context) -> list[Reading]:
    """Per arm with organic backtests (drafts whose `source` is `injection` are excluded and counted
    elsewhere): admit rate, fixed/broken distributions, and the § 12 premise over the first
    `BACKTEST_PREMISE_FIRST` backtests (ordered by draft round): the share of encoded misses — samples whose
    baseline replay missed on a template of the quirk the draft encodes (planted map of the draft) — that the
    replay with the draft fixed. A draft without a mapping falls back to every baseline miss, flagged proxy."""
    drafts = {d["_id"]: d for d in rows.get("drafts", [])}
    pm = mapping(rows)
    by_arm: dict[str, list[Row]] = defaultdict(list)
    for b in rows.get("backtests", []):
        if not _is_injection(drafts.get(b.get("draft_id"), {})):
            by_arm[b["arm"]].append(b)
    out = []
    for arm in ctx.arms:
        bts = sorted(by_arm.get(arm, []),
                     key=lambda b: (int(drafts.get(b.get("draft_id"), {}).get("round", 0)), b["_id"]))
        if not bts:
            continue
        n = len(bts)
        admits = sum(1 for b in bts if b.get("verdict") == "admit")
        q = q_find("backtests", f"arm: '{arm}'", "backtest_summary")
        out.append(Reading(f"backtest.admit_rate.{arm}", admits / n, "share of backtests",
                           f"organic backtests of arm {arm}", n, q))
        for field_ in ("fixed", "broken"):
            hist = dict(sorted(Counter(int(b.get(field_, 0)) for b in bts).items()))
            out.append(Reading(f"backtest.{field_}_hist.{arm}", hist, f"backtests per {field_} count",
                               f"organic backtests of arm {arm}", n, q))
        first = bts[: ctx.premise_first]
        misses, proxied = [], 0
        for b in first:
            quirk = pm.get(b.get("draft_id"), {}).get("quirk")
            base = [s for s in b.get("sampled", []) if not s.get("baseline_correct")]
            if quirk is None or not ctx.template_quirk:
                proxied += 1
                misses += base
            else:
                misses += [s for s in base if ctx.template_quirk.get(s.get("template")) == quirk]
        fixed = sum(1 for s in misses if s.get("replay_correct"))
        share = fixed / len(misses) if misses else None
        holds = None if share is None or proxied else share >= ctx.premise_share
        verdict = "holds" if holds else "fails" if holds is not None else ("unread (proxy)" if proxied and misses
                                                                            else "unread")
        out.append(Reading(f"backtest.premise.{arm}", share, "share of encoded misses fixed",
                           f"paired-replay samples whose baseline missed on the draft's quirk, first {len(first)} "
                           f"organic backtests of arm {arm}", len(misses), q,
                           note=(f"§ 12 premise (≥ {ctx.premise_share:.0%}): {verdict}"
                                 + (f"; PROXY for {proxied} of {len(first)} backtests (draft not quirk-mapped): "
                                    "every baseline miss counted" if proxied else ""))))
    return out


def supersession_audit(rows: Mapping[str, list[Row]], ctx: Context) -> list[Reading]:
    """Doctrine § 11.2: every supersession should follow a declared fire. Counts superseded decisions with and
    without a dispositive fire at or before the supersession index. 'Without' is a verdict that moved while
    every stated falsifier stayed quiet."""
    fires: dict[str, list[int]] = defaultdict(list)
    for f in rows.get("fires", []):
        if f.get("role") == "dispositive":
            fires[f["decision_id"]].append(int(f.get("at_idx", 0)))
    out = []
    for arm in ctx.arms:
        sup = [d for d in rows.get("decisions", [])
               if d["arm"] == arm and d.get("lifecycle", {}).get("status") == "superseded"]
        if not sup:
            continue
        quiet = [d["_id"] for d in sup if not any(i <= int(d["lifecycle"]["at_idx"]) for i in fires.get(d["_id"], []))]
        out.append(Reading(f"supersession_audit.{arm}", len(sup) - len(quiet), "supersessions after a dispositive fire",
                           f"superseded decisions of arm {arm}", len(sup),
                           q_find("decisions", f"arm: '{arm}', 'lifecycle.status': 'superseded'", "supersession_audit"),
                           note=("superseded with no declared fire: " + ", ".join(quiet)) if quiet else None))
    return out


# --- E9 retrieval lead --------------------------------------------------------------------------------


def retrieval_lead(rows: Mapping[str, list[Row]], ctx: Context) -> list[Reading]:
    """E9 (§ 24.1): for each semantic-consultation arm s and hook-consultation arm h, over quirk-bearing stream
    indices (same question, no error) where h missed and s hit: the share where s applied a decision (mapped to
    the question's quirk, when a planted map exists) and no hook matched in h (`matched_ids` empty). A lower
    bound on what hooks miss. Episodes without `matched_ids` fall back to `consulted`, flagged."""
    pm = mapping(rows)
    sem = [a for a, s in ctx.arms.items() if s.consultation is ConsultationMode.SEMANTIC]
    hooks = [a for a, s in ctx.arms.items() if s.consultation is ConsultationMode.HOOKS]
    out = []
    for s in sem:
        for h in hooks:
            keep = lambda e: not ctx.template_quirk or e.get("template") in ctx.template_quirk  # noqa: E731
            _, _, idx_all, drop = _pairs(rows, s, h, keep)
            es = {e["idx"]: e for e in stream_of(rows, s)}
            eh = {e["idx"]: e for e in stream_of(rows, h)}
            idx = [i for i in idx_all if not eh[i].get("correct") and es[i].get("correct")]
            fallback = any("matched_ids" not in eh[i] for i in idx)

            def right(e: Row) -> bool:
                q = ctx.template_quirk.get(e.get("template"))
                return any(c.get("disposition") == "applied"
                           and (not pm or pm.get(c.get("decision_id"), {}).get("quirk") == q)
                           for c in e.get("consulted", []))

            def unmatched(e: Row) -> bool:
                return not (e["matched_ids"] if "matched_ids" in e else e.get("consulted"))

            lead = [i for i in idx if right(es[i]) and unmatched(eh[i])]
            notes = [n for n in (None if pm else "no planted map: any applied decision counts as the right one",
                                 "matched_ids absent on some episodes: consulted used" if fallback else None,
                                 _drop_note(drop)) if n]
            out.append(Reading(f"E9.{s}-over-{h}", len(lead) / len(idx) if idx else None, "share of lead indices",
                               f"quirk-bearing stream indices where {h} missed and {s} hit", len(idx),
                               q_find("episodes", f"arm: {{$in: ['{s}', '{h}']}}, stream: 'stream'", "retrieval_lead"),
                               note="; ".join(notes) or None))
    return out


# --- spend and sandbox -------------------------------------------------------------------------------


def spend_readings(summary: Sequence[Row], rows: Mapping[str, list[Row]], ctx: Context,
                   priced: Iterable[str]) -> list[Reading]:
    q = ("munchhausen.spend.aggregate($match meta.run_id = R; $group arm × stage × model)"
         " | metrics.readings.spend_readings")
    out = []
    usd_arm: dict[str, float] = defaultdict(float)
    calls_arm: Counter[str] = Counter()
    err_arm: Counter[str] = Counter()
    for r in summary:
        usd_arm[r["arm"]] += float(r.get("usd", 0.0))
        calls_arm[r["arm"]] += int(r.get("calls", 0))
        err_arm[r["arm"]] += int(r.get("errors", 0))
    for arm in sorted(usd_arm):
        n_eps = len(stream_of(rows, arm))
        out.append(Reading(f"spend.usd.{arm}", usd_arm[arm], "USD (list price)", f"model calls tagged arm {arm}",
                           calls_arm[arm], q, note=f"{err_arm[arm]} failed calls" if err_arm[arm] else None))
        if n_eps:
            out.append(Reading(f"spend.usd_per_episode.{arm}", usd_arm[arm] / n_eps, "USD per stream episode",
                               f"model calls tagged arm {arm} / stream episodes", n_eps, q))
    unpriced = sorted({r["model"] for r in summary} - set(priced))
    if unpriced:
        out.append(Reading("spend.unpriced_models", unpriced, "model ids", "spend rows", len(unpriced), q,
                           note="priced at 0: add them to MODEL_PRICES_USD_PER_MTOK"))
    return out


def models_served(summary: Sequence[Row]) -> dict[str, dict[str, Any]]:
    """stage → {requested, served, ok, failed{error: n}} from the spend summary. A stage whose requested
    model never answered has `served: []` and its failures listed: unavailability is evidence."""
    out: dict[str, dict[str, Any]] = {}
    for r in summary:
        st = out.setdefault(r["stage"], {"requested": [], "served": [], "ok": 0, "failed": {}})
        if r["model"] not in st["requested"]:
            st["requested"].append(r["model"])
        for m in r.get("served", []) or []:
            if m not in st["served"]:
                st["served"].append(m)
        st["ok"] += int(r.get("calls", 0)) - int(r.get("errors", 0))
        for e in r.get("error_kinds", []) or []:
            st["failed"][e] = st["failed"].get(e, 0) + 1
    return out


def models_served_readings(summary: Sequence[Row]) -> list[Reading]:
    q = ("munchhausen.spend.aggregate($match meta.run_id = R; $group arm × stage × model; served_model, error)"
         " | metrics.readings.models_served")
    out = []
    for stage, st in sorted(models_served(summary).items()):
        n = st["ok"] + sum(st["failed"].values())
        failed = ", ".join(f"{k} × {v}" for k, v in sorted(st["failed"].items()))
        note = (f"requested {', '.join(st['requested'])}" + (f"; failed: {failed}" if failed else "")
                + ("; NO call answered" if st["ok"] == 0 else ""))
        out.append(Reading(f"models.served.{stage}", st["served"] or ["none"], "model ids",
                           f"model calls of stage {stage}", n, q, note=note))
    return out


def sandbox_readings(rows: Mapping[str, list[Row]], events: Sequence[Row], ctx: Context) -> list[Reading]:
    """Guard refusals per arm: episodes whose `error` starts `PipelineRefused` (always read), with the refusing
    party from `guard_refusal` trace events when Trace wrote them (`unknown` otherwise)."""
    q_ep = q_find("episodes", "error: /^PipelineRefused/", "sandbox_readings")
    party: dict[str, str] = {}
    for e in events:
        if e.get("name") == "guard_refusal" and e.get("episode_id"):
            party[e["episode_id"]] = str(e.get("party") or "unknown")
    out = []
    for arm in ctx.arms:
        ref = [e for e in rows.get("episodes", []) if e.get("arm") == arm
               and str(e.get("error") or "").startswith("PipelineRefused")]
        n_eps = len([e for e in rows.get("episodes", []) if e.get("arm") == arm])
        by = Counter(party.get(e["_id"], "unknown") for e in ref)
        out.append(Reading(f"sandbox.guard_refusals.{arm}", len(ref), "refused pipelines", f"episodes of arm {arm}",
                           n_eps, q_ep, note=("by party: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))
                           if ref else None))
    return out


# --- lifecycle timeline -------------------------------------------------------------------------------


def timeline(rows: Mapping[str, list[Row]], ctx: Context) -> list[dict[str, Any]]:
    dr = drafts_round(rows)
    pm = mapping(rows)
    out = []
    for d in rows.get("decisions", []):
        lc = d.get("lifecycle", {})
        out.append({"arm": d["arm"], "id": d["_id"], "title": d.get("title"), "kind": d.get("kind"),
                    "admitted_idx": admitted_idx(d, dr, ctx.round_size), "status": lc.get("status"),
                    "status_idx": lc.get("at_idx"), "superseded_by": lc.get("superseded_by"),
                    "quirk": pm.get(d["_id"], {}).get("quirk")})
    for f in rows.get("fires", []):
        out.append({"arm": f["arm"], "id": f["_id"], "fire_of": f.get("decision_id"), "role": f.get("role"),
                    "status_idx": f.get("at_idx"), "status": f"fire:{f.get('disposition')}"})
    return sorted(out, key=lambda r: (r["arm"], r.get("status_idx") or 0))


# --- forecasts ----------------------------------------------------------------------------------------


def read_forecast(fid: str, entry: Mapping[str, Any], rows: Mapping[str, list[Row]], ctx: Context) -> dict[str, Any]:
    """One forecast beside its reading(s) and verdict(s). A forecast naming an arm that did not run is
    `unread`, never silently dropped."""
    spec = dict(entry.get("read", {}))
    kind = spec.pop("kind", None)
    margin = float(entry.get("margin", 0))
    base = {"id": fid, "claim": entry.get("claim"), "reading": entry.get("reading"), "margin": margin,
            "unit": entry.get("unit")}
    missing = [a for a in [spec.get("a"), spec.get("b"), *spec.get("others", [])] if a and a not in ctx.arms]
    if missing:
        return {**base, "verdict": "unread", "readings": [], "note": f"arms not in this run: {missing}"}
    if kind == "paired_accuracy":
        r, v = paired_accuracy(rows, ctx, spec["a"], spec["b"], population=spec.get("population", "all"),
                               after_round=int(spec.get("after_round", 0)), margin=margin)
        return {**base, "verdict": v, "readings": [r.to_dict()]}
    if kind == "drift_calibration":
        if spec["drift"] not in ctx.drift_at:
            return {**base, "verdict": "unread", "readings": [], "note": f"drift {spec['drift']} not scheduled"}
        rs = drift_calibration(rows, ctx, drift=spec["drift"], prefix=spec["quirk_prefix"],
                               reference=spec.get("reference", ""), margin=margin)
        if not rs:
            return {**base, "verdict": "unread", "readings": [],
                    "note": "no arm held a pre-drift decision on the drifting quirk"}
        return {**base, "verdict": {r.name: v for r, v in rs}, "readings": [r.to_dict() for r, _ in rs]}
    if kind == "drift_latency":
        if spec["drift"] not in ctx.drift_at:
            return {**base, "verdict": "unread", "readings": [], "note": f"drift {spec['drift']} not scheduled"}
        rs = drift_latency(rows, ctx, drift=spec["drift"], prefix=spec["quirk_prefix"], a=spec["a"],
                           others=spec.get("others", []), margin=margin)
        return {**base, "verdict": {r.name: v for r, v in rs}, "readings": [r.to_dict() for r, _ in rs]}
    if kind == "planted_count":
        rs, v = planted_count(rows, ctx, prefix=spec["quirk_prefix"], expect=spec.get("expect", {}))
        return {**base, "verdict": v, "readings": [r.to_dict() for r in rs]}
    if kind == "planted_scope":
        rs, v = planted_scope(rows, ctx, prefix=spec["quirk_prefix"], expect=spec.get("expect", {}))
        return {**base, "verdict": v, "readings": [r.to_dict() for r in rs]}
    return {**base, "verdict": "unread", "readings": [], "note": f"no reading kind {kind!r}"}


def errored(e: Row) -> bool:
    return bool(e.get("error"))


def scored_of(rows: Mapping[str, list[Row]], arm: str) -> list[Row]:
    """Stream episodes with no `error` (S2's `episode_failed` episodes are excluded from every rate)."""
    return [e for e in stream_of(rows, arm) if not errored(e)]


def _drop_note(drop: Mapping[str, int]) -> str | None:
    parts = [f"{k} {v}" for k, v in drop.items() if v]
    return ("pairs dropped: " + ", ".join(parts)) if parts else None


def rolling_paired(rows: Mapping[str, list[Row]], ctx: Context, reference: str) -> dict[str, list[dict[str, Any]]]:
    """Demo beat 1: per arm, the paired accuracy difference arm − reference over a rolling window of
    `PAIRED_ROLLING_WINDOW` stream indices, one point per round, with its interval and n."""
    if reference not in ctx.arms:
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    w = ctx.rolling_window
    for arm in ctx.arms:
        if arm == reference or not stream_of(rows, arm):
            continue
        pts = []
        for end in range(ctx.round_size, ctx.run_length + 1, ctx.round_size):
            lo = max(0, end - w)
            xa, xb, _, _ = _pairs(rows, arm, reference, lambda e, lo=lo, end=end: lo <= e["idx"] < end)
            if not xa:
                continue
            pr = paired_difference(xa, xb, n_boot=ctx.bootstrap_n, level=ctx.ci_level, seed=ctx.seed)
            pts.append({"idx_lo": lo, "idx_hi": end - 1, "diff": pr.diff, "lo": pr.lo, "hi": pr.hi, "n": pr.n})
        out[arm] = pts
    return out


def _is_injection(d: Row) -> bool:
    return d.get("source") == "injection"


def injection_readings(rows: Mapping[str, list[Row]], ctx: Context, events: Sequence[Row]) -> list[Reading]:
    """Injection (S6's live beat) counted apart from organic readings: drafts with `source: injection`, their
    backtests and verdicts, injection episodes, and `injection.*` trace events."""
    drafts = [d for d in rows.get("drafts", []) if _is_injection(d)]
    ids = {d["_id"] for d in drafts}
    bts = [b for b in rows.get("backtests", []) if b.get("draft_id") in ids]
    eps = [e for e in rows.get("episodes", []) if e.get("stream") == "injection"]
    ev = Counter(e["name"] for e in events if str(e.get("name", "")).startswith("injection."))
    q = q_find("drafts", "source: 'injection'", "injection_readings")
    return [
        Reading("injection.drafts", len(drafts), "drafts", "drafts with source injection", len(drafts), q),
        Reading("injection.backtests", dict(Counter(b.get("verdict") for b in bts)), "backtests per verdict",
                "backtests of injection drafts", len(bts), q),
        Reading("injection.episodes", len(eps), "episodes", "episodes with stream injection", len(eps),
                q_find("episodes", "stream: 'injection'", "injection_readings")),
        Reading("injection.events", dict(ev), "trace events", "injection.* trace events", sum(ev.values()),
                "var/runs/R/events.jsonl name ^injection. | metrics.readings.injection_readings"),
    ]


def floor_readings(rows: Mapping[str, list[Row]], ctx: Context) -> list[Reading]:
    """The floor beat: `tool_access` rewires (logical → view, owning decision) and stream episodes whose
    pipeline ran through a rewired view (`view_map` non-empty), per arm."""
    out = []
    ta = rows.get("tool_access", [])
    for arm in ctx.arms:
        rw = [{"logical": t.get("logical"), "view": t.get("view"), "decision_id": t.get("decision_id")}
              for t in ta if t.get("arm") == arm]
        es = stream_of(rows, arm)
        vf = [e for e in es if e.get("view_map")]
        if not rw and not vf:
            continue
        out.append(Reading(f"floor.rewires.{arm}", rw, "rewired collections", f"tool_access rows of arm {arm}",
                           len(rw), q_find("tool_access", f"arm: '{arm}'", "floor_readings")))
        out.append(Reading(f"floor.view_filtered.{arm}", len(vf), "episodes",
                           f"stream episodes of arm {arm} whose pipeline ran through a view", len(es),
                           q_find("episodes", f"arm: '{arm}', stream: 'stream', view_map: {{$ne: {{}}}}",
                                  "floor_readings"),
                           note=(f"first at idx {vf[0]['idx']}" if vf else None)))
    return out


def lifecycle_counts(rows: Mapping[str, list[Row]], ctx: Context) -> list[Reading]:
    """Decisions by lifecycle status per arm; converged (merge successors) apart from superseded."""
    out = []
    for arm in ctx.arms:
        ds = [d for d in rows.get("decisions", []) if d.get("arm") == arm]
        if not ds:
            continue
        c = Counter(d.get("lifecycle", {}).get("status") for d in ds)
        out.append(Reading(f"lifecycle.{arm}", dict(sorted(c.items())), "decisions per lifecycle status",
                           f"decisions of arm {arm}", len(ds), q_find("decisions", f"arm: '{arm}'", "lifecycle_counts"),
                           note="converged = merged into a successor; not a supersession, never a drift resolution"))
    return out


def unmetered(ctx: Context) -> list[Reading]:
    """Disclosure: calls no call path meters (no cheap hook in this build). Voyage embed and rerank are metered
    by `impl/voyage.py` (stages EMBED_STAGE / RERANK_STAGE; cache hits write no row)."""
    return [Reading("spend.not_metered", ["typesafe lens panel"], "call kinds",
                    "model calls outside the Anthropic and Voyage call paths", 0, "none: not recorded in spend",
                    note="these calls are not metered: spend readings exclude their cost and tokens")]


# --- everything ---------------------------------------------------------------------------------------


def all_readings(rows: Mapping[str, list[Row]], ctx: Context, *, spend: Sequence[Row] = (),
                 events: Sequence[Row] = (), priced: Iterable[str] = ()) -> dict[str, Any]:
    arms = [a for a in ctx.arms if any(e.get("arm") == a for e in rows.get("episodes", []))]
    reference = next((str(e.get("read", {}).get("reference")) for e in ctx.forecasts.values()
                      if e.get("read", {}).get("reference")), "")
    curves = {a: stream_curve(rows, ctx, a) for a in arms}
    v = {a: v_points(rows, a) for a in arms}
    summary = [r for a in arms for r in arm_summary(rows, ctx, a)]
    drift_rows = []
    for d in ctx.drift_at:
        q = ctx.drift_quirk.get(d, "")
        prefix = q.split("_")[0] if q else d
        drift_rows += stale_applied(rows, ctx, drift=d, prefix=prefix)
    return {
        "run_id": ctx.run_id,
        "arms": arms,
        "drifts": dict(ctx.drift_at),
        "curves": curves,
        "v_points": v,
        "reference": reference,
        "paired_curves": rolling_paired(rows, ctx, reference),
        "notes": list(ctx.notes),
        "forecasts": [read_forecast(fid, e, rows, ctx) for fid, e in ctx.forecasts.items()],
        "readings": [r.to_dict() for r in (summary + drift_rows + quirk_recall(rows, ctx)
                                           + backtest_summary(rows, ctx) + supersession_audit(rows, ctx)
                                           + retrieval_lead(rows, ctx) + spend_readings(spend, rows, ctx, priced)
                                           + models_served_readings(spend) + lifecycle_counts(rows, ctx)
                                           + floor_readings(rows, ctx) + injection_readings(rows, ctx, events)
                                           + sandbox_readings(rows, events, ctx) + unmetered(ctx))],
        "timeline": timeline(rows, ctx),
        "spend": list(spend),
    }


def _fmt(x: float | None) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.3f}"
