# ruff: noqa: E501  (HTML/CSS/JS templates read better unwrapped)
"""Report rendering (pure): readings → `report.md`, `report.html`, `manifest.json` (corpus/EVIDENCE.md § 5).

Claim language (corpus/LANGUAGE.md § 7): a sentence is no wider than its reading; every quantity carries
unit, population and n; each forecast is printed beside its reading; a disagreement stands as one; status
words are lifecycle values. The renderer only prints what `readings.json` holds, so a report sentence is
re-derivable from the reading it names.
"""

from __future__ import annotations

import html
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

VERDICT_TEXT = {
    "above": "above the margin: the reading agrees with the forecast",
    "below": "below the negative margin: the reading disagrees with the forecast",
    "within": "within the margin: the reading does not resolve the forecast at this margin",
    "agrees": "the reading agrees with the forecast",
    "disagrees": "the reading disagrees with the forecast",
    "unread": "unread: the reading's inputs are missing or an arm did not resolve (see note)",
    "unread (proxy)": "unread (proxy): the population is a proxy (no planted map), so no verdict is claimed",
}


def fmt(x: Any, digits: int = 3, signed: bool = True) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, float):
        if abs(x) >= 10:
            return f"{x:+,.1f}" if signed else f"{x:,.1f}"
        return f"{x:+.{digits}f}" if signed else f"{x:.{digits}f}"
    return str(x)


def _signed(r: Mapping[str, Any]) -> bool:
    """Differences carry a sign; levels do not."""
    return bool(r.get("interval")) or "−" in r["unit"] or str(r["name"]).startswith(("F", "paired"))


def sentence(r: Mapping[str, Any]) -> str:
    """One reading as one claim-language sentence: value, unit, interval, n, population."""
    s = f"`{r['name']}` = {fmt(r.get('value'), signed=_signed(r))} {r['unit']}"
    if r.get("interval"):
        lo, hi = r["interval"]
        s += f", {int(round(100 * r.get('level', 0)))}% interval [{fmt(lo)}, {fmt(hi)}]"
    s += f"; n = {r['n']}; population: {r['population']}."
    if r.get("note"):
        s += f" Note: {str(r['note']).rstrip('.')}."
    return s


def knob_diff(this: Mapping[str, Any], other: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = sorted(set(this) | set(other))
    return [{"knob": k, "this": this.get(k), "other": other.get(k)} for k in keys if this.get(k) != other.get(k)]


RUN_FIELDS_DIFFED = ("git_sha", "ports", "arm_specs", "forecast_register", "prompt_hashes", "pack_hash",
                     "pack_file_hash", "length")


def run_diff(this: Mapping[str, Any], other: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Knobs that moved, plus every registered field that moved (sha, ports, arm specs, forecasts, prompt
    hashes, pack hash, length): the pilot rule's diff (SPEC § 11)."""
    out = knob_diff(this.get("knobs", {}), other.get("knobs", {}))
    out += [{"knob": f, "this": this.get(f), "other": other.get(f)} for f in RUN_FIELDS_DIFFED
            if this.get(f) != other.get(f)]
    return out


def _verdicts(f: Mapping[str, Any]) -> list[tuple[str, str]]:
    v = f.get("verdict")
    return list(v.items()) if isinstance(v, dict) else [(f["id"], v)]


def markdown(readings: Mapping[str, Any], run: Mapping[str, Any], *, against: Mapping[str, Any] | None = None) -> str:
    rid = readings["run_id"]
    out = [f"# Evidence report — run `{rid}`", ""]
    if readings.get("note"):
        out += [f"> **{readings['note']}**", ""]
    out.append(f"Started {run.get('started_at', '—')}, ended {run.get('ended_at') or '—'}; git `{run.get('git_sha') or '—'}`"
               f"{' (dirty)' if run.get('git_dirty') else ''}; isolation `{run.get('isolation', '—')}`; "
               f"pack hash `{(run.get('pack_hash') or '—')[:12]}`; arms read: {', '.join(readings['arms']) or 'none'}.")
    out.append("")
    out.append(f"Anthropic auth mode: `{run.get('auth_mode', '—')}` (presence only); run length "
               f"{run.get('length') or 'RUN_LENGTH'}; spend rows lost: {run.get('lost_spend_writes', 0)}.")
    out.append("")
    for n in readings.get("notes", []):
        out.append(f"> Note: {n}.")
    if readings.get("notes"):
        out.append("")
    for i, r in enumerate(run.get("resumes") or [], 1):
        moved = ", ".join(sorted(r.get("moved", {})))
        out.append(f"> Resume {i} at {r.get('at')}: moved since registration: {moved or 'nothing'} "
                   "(registered forecasts and knobs hold).")
    if run.get("resumes"):
        out.append("")
    if run.get("models") or run.get("models_served"):
        out.append("| model knob | configured |")
        out.append("|---|---|")
        for k, v in sorted((run.get("models") or {}).items()):
            out.append(f"| {k} | {v} |")
        out.append("")
        for stage, st in sorted((run.get("models_served") or {}).items()):
            failed = ", ".join(f"{k} × {v}" for k, v in sorted(st.get("failed", {}).items())) or "none"
            out.append(f"- stage `{stage}`: requested {', '.join(st.get('requested', []))}; served "
                       f"{', '.join(st.get('served', [])) or 'NONE'}; {st.get('ok', 0)} calls answered; failed: {failed}.")
        out.append("")
    out.append("Every figure below names the query that produced it (`manifest.json`). A forecast is printed beside "
               "its reading; a disagreement stands as one. Forecasts are the ones registered in `runs` at start, "
               "not the current `conf/forecasts.yaml`.")
    out.append("")
    out.append("## Forecasts beside their readings")
    out.append("")
    for f in readings["forecasts"]:
        out.append(f"### {f['id']}")
        out.append("")
        out.append(f"- **Forecast:** {f['claim']} (margin {f['margin']} {f['unit']}).")
        out.append(f"- **Reading:** {f.get('reading')}.")
        for r in f["readings"]:
            out.append(f"  - {sentence(r)}")
        for name, v in _verdicts(f):
            out.append(f"- **Verdict** `{name}`: {VERDICT_TEXT.get(v, v)}.")
        if f.get("note"):
            out.append(f"- Note: {f['note']}.")
        out.append("")
    if readings.get("paired_curves"):
        out.append(f"## Paired difference against `{readings.get('reference')}` (rolling, by stream index)")
        out.append("")
        out.append("| arm | idx | difference | interval | n pairs |")
        out.append("|---|---|---|---|---|")
        for arm, pts in readings["paired_curves"].items():
            for p_ in pts:
                out.append(f"| {arm} | {p_['idx_lo']}–{p_['idx_hi']} | {fmt(p_['diff'])} | "
                           f"[{fmt(p_['lo'])}, {fmt(p_['hi'])}] | {p_['n']} |")
        out.append("")
    out.append("## Readings")
    out.append("")
    for r in readings["readings"]:
        out.append(f"- {sentence(r)}")
    out.append("")
    out.append("## Curves (per arm, per round of stream episodes)")
    out.append("")
    out.append("| arm | round | idx | n | accuracy | self-assessed | calibration gap |")
    out.append("|---|---|---|---|---|---|---|")
    for arm, pts in readings["curves"].items():
        for p in pts:
            out.append(f"| {arm} | {p['round']} | {p['idx_lo']}–{p['idx_hi']} | {p['n']} | {p['acc']:.3f} | "
                       f"{p['conf']:.3f} | {p['gap']:+.3f} |")
    out.append("")
    if any(readings["v_points"].values()):
        out.append("## V accuracy (sealed V set)")
        out.append("")
        for arm, pts in readings["v_points"].items():
            for p in pts:
                out.append(f"- `{arm}` at idx {p['at']}: {p['acc']:.3f} accuracy (fraction), n = {p['n']} V questions.")
        out.append("")
    out.append("## Lifecycle")
    out.append("")
    out.append("| arm | id | status | at idx | admitted idx | superseded by | quirk (planted map) |")
    out.append("|---|---|---|---|---|---|---|")
    for t in readings["timeline"]:
        out.append(f"| {t['arm']} | {t['id']} | {t['status']} | {t.get('status_idx')} | {t.get('admitted_idx', '')} | "
                   f"{t.get('superseded_by') or ''} | {t.get('quirk') or ''} |")
    out.append("")
    if readings["spend"]:
        out.append("## Spend (list price)")
        out.append("")
        out.append("| arm | stage | model | calls | errors | tokens in | tokens out | USD |")
        out.append("|---|---|---|---|---|---|---|---|")
        for s in readings["spend"]:
            out.append(f"| {s['arm']} | {s['stage']} | {s['model']} | {s['calls']} | {s.get('errors', 0)} | "
                       f"{s['tokens_in']} | {s['tokens_out']} | {s['usd']:.4f} |")
        out.append("")
    if against is not None:
        diff = run_diff(run, against)
        out.append(f"## Knob diff against run `{against.get('_id')}`")
        out.append("")
        if diff:
            out.append("Forecasts of a run whose knobs moved are that run's own registration (SPEC § 11, pilot rule).")
            out.append("")
            out.append("| knob | this run | other run |")
            out.append("|---|---|---|")
            for d in diff:
                out.append(f"| {d['knob']} | {json.dumps(d['this'])} | {json.dumps(d['other'])} |")
        else:
            out.append("No knob moved.")
        out.append("")
    return "\n".join(out)


def manifest(readings: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    """figure → {query, n}. Every figure in the report has an entry; a test asserts it."""
    figs: dict[str, dict[str, Any]] = {}
    for arm, pts in readings["curves"].items():
        q = f"munchhausen.episodes.find({{run_id: '{run_id}', arm: '{arm}', stream: 'stream'}}) | metrics.readings.stream_curve"
        figs[f"curve.accuracy.{arm}"] = {"query": q, "n": sum(p["n"] for p in pts), "unit": "accuracy (fraction)"}
        figs[f"curve.calibration_gap.{arm}"] = {"query": q, "n": sum(p["n"] for p in pts),
                                                "unit": "accuracy points (mean confidence − accuracy)"}
    for arm, pts in readings["v_points"].items():
        if pts:
            figs[f"curve.v_accuracy.{arm}"] = {
                "query": f"munchhausen.episodes.find({{run_id: '{run_id}', arm: '{arm}', stream: 'v'}}) | metrics.readings.v_points",
                "n": sum(p["n"] for p in pts), "unit": "accuracy (fraction)"}
    for f in readings["forecasts"]:
        for r in f["readings"]:
            figs[f"forecast.{f['id']}.{r['name']}"] = {"query": r["query"], "n": r["n"], "unit": r["unit"]}
    for r in readings["readings"]:
        figs[r["name"]] = {"query": r["query"], "n": r["n"], "unit": r["unit"]}
    ref = readings.get("reference")
    for arm, pts in (readings.get("paired_curves") or {}).items():
        figs[f"curve.paired_vs_{ref}.{arm}"] = {
            "query": f"munchhausen.episodes.find({{run_id: '{run_id}', arm: {{$in: ['{arm}', '{ref}']}}, stream: 'stream'}}) | metrics.readings.rolling_paired",
            "n": sum(p["n"] for p in pts), "unit": "accuracy (fraction), paired difference"}
    figs["timeline"] = {"query": f"munchhausen.decisions.find({{run_id: '{run_id}'}}) + fires | metrics.readings.timeline",
                        "n": len(readings["timeline"]), "unit": "records"}
    figs["spend"] = {"query": "munchhausen.spend.aggregate($match meta.run_id; $group arm × stage × model)",
                     "n": sum(int(s.get("calls", 0)) for s in readings["spend"]), "unit": "calls"}
    return {"run_id": run_id, "figures": figs}


# --- HTML ---------------------------------------------------------------------------------------------

_CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1b;--mut:#6b6b66;--line:#dedcd6;--card:#fff;--pos:#2f7d4f;--neg:#b23b3b;--acc:#3b5bb2}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--mut:#9a9a93;--line:#34332f;--card:#1f1f1d;--pos:#6cc28f;--neg:#e57d7d;--acc:#8fa6ea}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px}h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 8px}
.mut{color:var(--mut)}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:8px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
table{border-collapse:collapse;width:100%;font-size:12.5px}td,th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
.tw{overflow-x:auto}code{font-size:12px}.v-above,.v-agrees{color:var(--pos)}.v-below,.v-disagrees{color:var(--neg)}.v-within,.v-unread{color:var(--mut)}
canvas{max-width:100%}
"""


def _interval_svg(r: Mapping[str, Any], margin: float) -> str:
    """A paired difference with its interval against 0 and ±margin."""
    lo, hi = r["interval"]
    v = r.get("value")
    if any(x is None for x in (lo, hi, v)):
        return '<span class="mut">no interval</span>'
    span = max(abs(lo), abs(hi), abs(margin), 1e-9) * 1.25
    w = 320

    def x(t: float) -> float:
        return w / 2 + t / span * (w / 2 - 10)

    return (f'<svg viewBox="0 0 {w} 40" width="100%" height="40" role="img" aria-label="interval">'
            f'<line x1="{x(0)}" y1="4" x2="{x(0)}" y2="36" stroke="currentColor" stroke-opacity=".5"/>'
            f'<line x1="{x(margin)}" y1="8" x2="{x(margin)}" y2="32" stroke="currentColor" stroke-dasharray="3 3" stroke-opacity=".5"/>'
            f'<line x1="{x(-margin)}" y1="8" x2="{x(-margin)}" y2="32" stroke="currentColor" stroke-dasharray="3 3" stroke-opacity=".5"/>'
            f'<line x1="{x(lo)}" y1="20" x2="{x(hi)}" y2="20" stroke="var(--acc)" stroke-width="3"/>'
            f'<circle cx="{x(v)}" cy="20" r="5" fill="var(--acc)"/>'
            f'<text x="{x(lo)}" y="38" font-size="9" fill="currentColor" text-anchor="middle">{lo:+.3f}</text>'
            f'<text x="{x(hi)}" y="38" font-size="9" fill="currentColor" text-anchor="middle">{hi:+.3f}</text></svg>')


def html_report(readings: Mapping[str, Any], run: Mapping[str, Any], md_sentences: Sequence[str] = (), *,
                chartjs_url: str) -> str:
    e = html.escape
    data = json.dumps({"curves": readings["curves"], "v": readings["v_points"], "drifts": readings["drifts"],
                       "paired": readings.get("paired_curves") or {}})
    parts = [f"<!doctype html><html lang=en><head><meta charset=utf-8>"
             f"<meta name=viewport content='width=device-width,initial-scale=1'><title>Evidence {e(readings['run_id'])}</title>"
             f"<style>{_CSS}</style><script src='{e(chartjs_url)}'></script></head><body><main>"]
    parts.append(f"<h1>Evidence — run <code>{e(readings['run_id'])}</code></h1>"
                 f"<div class=mut>git {e(str(run.get('git_sha') or '—'))[:12]}{' (dirty)' if run.get('git_dirty') else ''} · "
                 f"isolation {e(str(run.get('isolation', '—')))} · started {e(str(run.get('started_at', '—')))} · "
                 f"drifts {e(json.dumps(readings['drifts']))}</div>"
                 + (f"<p class=card><b>{e(readings['note'])}</b></p>" if readings.get("note") else ""))
    parts.append("<h2>Curves</h2><div class=grid>"
                 "<div class=card><b>Stream accuracy per round</b> <span class=mut>(fraction; stream episodes; dashed: drifts)</span><canvas id=acc></canvas></div>"
                 "<div class=card><b>Calibration gap per round</b> <span class=mut>(mean confidence − accuracy)</span><canvas id=gap></canvas></div>"
                 f"<div class=card><b>Paired difference vs {e(str(readings.get('reference') or '—'))}</b> <span class=mut>(accuracy, rolling window; dashed: interval)</span><canvas id=pair></canvas></div></div>")
    parts.append("<h2>Forecasts beside their readings</h2>")
    for f in readings["forecasts"]:
        rows = []
        for r in f["readings"]:
            viz = _interval_svg(r, f["margin"]) if r.get("interval") else ""
            rows.append(f"<tr><td><code>{e(r['name'])}</code></td><td>{e(fmt(r.get('value')))} {e(r['unit'])}</td>"
                        f"<td>{viz}</td><td>n = {r['n']}<br><span class=mut>{e(r['population'])}</span>"
                        f"{'<br><span class=mut>' + e(r['note']) + '</span>' if r.get('note') else ''}</td></tr>")
        verdicts = " ".join(f"<span class='v-{e(str(v))}'>{e(name)}: {e(VERDICT_TEXT.get(v, str(v)))}</span><br>"
                            for name, v in _verdicts(f))
        parts.append(f"<div class=card><b>{e(f['id'])}</b> {e(str(f['claim']))} "
                     f"<span class=mut>(margin {f['margin']} {e(str(f['unit']))})</span><br>{verdicts}"
                     f"{'<span class=mut>' + e(f['note']) + '</span>' if f.get('note') else ''}"
                     f"<div class=tw><table>{''.join(rows)}</table></div></div>")
    parts.append("<h2>Readings</h2><div class='card tw'><table><tr><th>reading</th><th>value</th><th>n</th><th>population</th><th>query</th></tr>")
    for r in readings["readings"]:
        iv = f" [{fmt(r['interval'][0])}, {fmt(r['interval'][1])}]" if r.get("interval") else ""
        parts.append(f"<tr><td><code>{e(r['name'])}</code></td><td>{e(fmt(r.get('value')))}{e(iv)} {e(r['unit'])}"
                     f"{'<br><span class=mut>' + e(r['note']) + '</span>' if r.get('note') else ''}</td>"
                     f"<td>{r['n']}</td><td>{e(r['population'])}</td><td><code>{e(r['query'])}</code></td></tr>")
    parts.append("</table></div>")
    parts.append("<h2>Lifecycle</h2><div class='card tw'><table><tr><th>arm</th><th>id</th><th>status</th><th>idx</th>"
                 "<th>admitted idx</th><th>superseded by</th><th>quirk</th></tr>")
    for t in readings["timeline"]:
        parts.append(f"<tr><td>{e(t['arm'])}</td><td><code>{e(t['id'])}</code></td><td>{e(str(t['status']))}</td>"
                     f"<td>{e(str(t.get('status_idx')))}</td><td>{e(str(t.get('admitted_idx', '')))}</td>"
                     f"<td>{e(str(t.get('superseded_by') or ''))}</td><td>{e(str(t.get('quirk') or ''))}</td></tr>")
    parts.append("</table></div>")
    if readings["spend"]:
        parts.append("<h2>Spend (list price, USD)</h2><div class='card tw'><table><tr><th>arm</th><th>stage</th><th>model</th>"
                     "<th>calls</th><th>errors</th><th>tokens in</th><th>tokens out</th><th>USD</th></tr>")
        for s in readings["spend"]:
            parts.append(f"<tr><td>{e(s['arm'])}</td><td>{e(s['stage'])}</td><td>{e(s['model'])}</td><td>{s['calls']}</td>"
                         f"<td>{s.get('errors', 0)}</td><td>{s['tokens_in']}</td><td>{s['tokens_out']}</td><td>{s['usd']:.4f}</td></tr>")
        parts.append("</table></div>")
    parts.append(f"<script>const D={data};" + _JS + "</script></main></body></html>")
    return "".join(parts)


_JS = """
(function(){if(!window.Chart){return}
const cs=getComputedStyle(document.documentElement),fg=cs.getPropertyValue('--fg'),mut=cs.getPropertyValue('--mut');
const pal=['#3b5bb2','#c0702a','#2f7d4f','#9b3fa6','#b23b3b','#5a8f9a'];
function chart(id,key,lo,hi){const ds=Object.entries(D.curves).map(([arm,pts],i)=>({label:arm,data:pts.map(p=>({x:p.idx_hi,y:p[key]})),
borderColor:pal[i%pal.length],backgroundColor:pal[i%pal.length],pointRadius:1.5,borderWidth:1.6,tension:.15}));
Object.entries(D.drifts).forEach(([d,at])=>ds.push({label:d,data:[{x:at,y:lo},{x:at,y:hi}],borderColor:mut,borderDash:[4,4],pointRadius:0,borderWidth:1}));
new Chart(document.getElementById(id),{type:'line',data:{datasets:ds},options:{animation:false,parsing:true,
scales:{x:{type:'linear',title:{display:true,text:'stream idx',color:mut},ticks:{color:mut}},y:{min:lo,max:hi,ticks:{color:mut}}},
plugins:{legend:{labels:{color:fg,boxWidth:10}}}}})}
chart('acc','acc',0,1);chart('gap','gap',-0.5,1);
const pd=[];Object.entries(D.paired).forEach(([arm,pts],i)=>{const c=pal[(i+1)%pal.length];
pd.push({label:arm,data:pts.map(p=>({x:p.idx_hi,y:p.diff})),borderColor:c,backgroundColor:c,pointRadius:1.5,borderWidth:1.6});
pd.push({label:arm+' lo',data:pts.map(p=>({x:p.idx_hi,y:p.lo})),borderColor:c,borderWidth:0.6,pointRadius:0,borderDash:[2,2]});
pd.push({label:arm+' hi',data:pts.map(p=>({x:p.idx_hi,y:p.hi})),borderColor:c,borderWidth:0.6,pointRadius:0,borderDash:[2,2]});});
Object.entries(D.drifts).forEach(([d,at])=>pd.push({label:d,data:[{x:at,y:-1},{x:at,y:1}],borderColor:mut,borderDash:[4,4],pointRadius:0,borderWidth:1}));
new Chart(document.getElementById('pair'),{type:'line',data:{datasets:pd},options:{animation:false,
scales:{x:{type:'linear',ticks:{color:mut}},y:{min:-1,max:1,ticks:{color:mut}}},plugins:{legend:{labels:{color:fg,boxWidth:10,filter:i=>!/ (lo|hi)$/.test(i.text)}}}}});})();
"""
