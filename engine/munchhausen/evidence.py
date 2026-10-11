"""Composition root, evidence half (ORCHESTRATION.md § Evidence): the run record at start, the round record at
each round close, the run's end, and the readings over a finished (or running) run. Composition-level, so it
may read git, the store's capabilities, the pack (evaluation side) and the config. Owner: telemetry (S5).
Called by `bootstrap`/the `run` command (S2): `start_run` before the first episode, `close_round` after the
backward hook of each round, `finish_run` at the end.

One-way doors (corpus/EVIDENCE.md § 1): the run id is the unit of pre-registration. A run's forecasts and knobs
are written once, before its first episode, and never edited; re-registering means a new RUN_ID.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from munchhausen.config import REPO_ROOT, Settings
from munchhausen.domain.arm import ArmSpec
from munchhausen.domain.registers import RunRecord
from munchhausen.metrics import readings as R

PARTIES_DIR = Path(__file__).resolve().parent / "impl" / "parties"
PRESENCE_ONLY_KNOBS = frozenset({"anthropic_workspace_id"})


class PreRegistrationError(RuntimeError):
    """Episodes exist for a run that has no run record: its forecasts cannot be registered after the fact."""


# --- pieces of the run record (pure or local I/O) ------------------------------------------------------


def git_state(root: Path = REPO_ROOT) -> tuple[str | None, bool | None]:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True,
                             check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True,
                                    check=True).stdout.strip())
        return sha, dirty
    except (OSError, subprocess.CalledProcessError):
        return None, None


def prompt_hashes(parties_dir: Path = PARTIES_DIR) -> dict[str, str]:
    """party → sha256 of its module source (prompt, wire schema and mapping live together in one module, so a
    changed prompt changes the hash). The exact system prompt of each call is hashed on its `spend` row."""
    return {p.stem: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(parties_dir.glob("*.py")) if p.stem != "__init__"}


def file_sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def forecast_register(settings: Settings) -> dict[str, dict[str, Any]]:
    return {fid: dict(entry) for fid, entry in settings.forecasts().items()}


def build_run_record(settings: Settings, *, selection: dict[str, dict[str, str]], capabilities: dict[str, Any],
                     git: tuple[str | None, bool | None], prompts: dict[str, str], pack_hash: str | None,
                     world_counts: dict[str, int], now: datetime) -> RunRecord:
    """The `runs` document (pure). Knobs exclude every secret; keys appear as presence only."""
    register = forecast_register(settings)
    knobs = settings.knobs()
    present = settings.keys_present()
    for k in PRESENCE_ONLY_KNOBS:          # account identifiers: recorded as presence, like keys
        if k in knobs:
            present[k] = knobs.pop(k) is not None
    return RunRecord(
        _id=settings.run_id, world=f"{settings.world_adapter}+{settings.world_pack}", pack=settings.world_pack,
        seeds={"world": settings.world_seed, "stream": settings.stream_seed, "v": settings.v_seed},
        knobs=knobs, ports=selection,
        forecasts={fid: str(e.get("claim", "")) for fid, e in register.items()},
        capabilities=capabilities, started_at=now,
        git_sha=git[0], git_dirty=git[1], isolation=settings.isolation(), models=settings.model_ids(),
        prompt_hashes=prompts, pack_hash=pack_hash, world_counts=world_counts, forecast_register=register,
        keys_present=present, auth_mode=settings.anthropic_auth_mode(),
    )


async def _world_facts(h: Any, settings: Settings) -> tuple[str | None, dict[str, int]]:
    """Pack hash and world counts: `World.pack_hash` / `World.inventory()` when the world offers them (S1),
    else the pack file's sha256 and no counts. Never fails the run start."""
    pack_hash, counts = file_sha256(settings.pack_path()), {}
    try:
        world = h.world()
        pack_hash = getattr(world, "pack_hash", None) or pack_hash
        inv = getattr(world, "inventory", None)
        if callable(inv):
            got = inv()
            got = await got if hasattr(got, "__await__") else got
            counts = {str(k): int(v) for k, v in dict(got).items() if isinstance(v, int)}
    except Exception as e:   # world not built yet, truth DB unreachable, …: recorded as absent
        print(f"[evidence] world facts not read ({type(e).__name__})", file=sys.stderr)
    return pack_hash, counts


def _trace(h: Any, name: str, payload: dict[str, Any]) -> None:
    try:
        h.shared("trace", h.settings.trace_impl).event(name, payload)
    except Exception:
        return


# --- the seams S2 calls ------------------------------------------------------------------------------


async def start_run(h: Any) -> RunRecord:
    """Write `runs` before the first episode. Idempotent on resume: an existing record is returned unedited
    (forecasts and knobs never change after the first episode; a diff against the current config is warned).
    Refuses to register a run that already has episodes and no record."""
    s: Settings = h.settings
    existing = await h.store.runs.get(s.run_id)
    if existing is not None:
        if existing.forecast_register and existing.forecast_register != forecast_register(s):
            print(f"[evidence] run {s.run_id}: conf/forecasts.yaml differs from the registered forecasts; "
                  "the registered ones hold. Re-register under a new RUN_ID.", file=sys.stderr)
        return existing
    if await h.store.evidence.episode_count(s.run_id) > 0:
        raise PreRegistrationError(f"run {s.run_id} has episodes but no run record: forecasts must be "
                                   "registered before the first episode. Start a new RUN_ID.")
    try:
        caps = await h.store.capabilities()
    except Exception as e:
        caps = {"error": type(e).__name__}
    pack_hash, counts = await _world_facts(h, s)
    record = build_run_record(s, selection=h.selection(), capabilities=caps, git=git_state(),
                              prompts=prompt_hashes(), pack_hash=pack_hash, world_counts=counts,
                              now=datetime.now(UTC))
    stored = await h.store.runs.start(record)
    _trace(h, "run_start", {"git_sha": stored.git_sha, "arms": sorted(stored.ports)})
    return stored


async def close_round(h: Any, arm: str, round_: int, idx_range: tuple[int, int]) -> None:
    """`$merge` the round's record into `rounds` (computed in Atlas). `idx_range` = (first, last), inclusive."""
    await h.store.runs.merge_round(h.settings.run_id, arm, round_, idx_range)
    _trace(h, "round_close", {"arm": arm, "round": round_, "idx": idx_range[1]})


async def finish_run(h: Any) -> None:
    """Stamp `ended_at` and `models_served` (per stage: requested vs served model ids, ok and failed calls by
    error), read from `spend`. A party whose model never answered shows here as failed calls, not as silence."""
    served = R.models_served(await h.store.evidence.spend_summary(h.settings.run_id))
    await h.store.runs.finish(h.settings.run_id, datetime.now(UTC), served)
    _trace(h, "run_finish", {})


# --- readings over a run -------------------------------------------------------------------------------


def reading_context(settings: Settings, run: RunRecord) -> R.Context:
    """Readings use the run's registered knobs and forecasts, never the current config's. The pack (evaluation
    side) supplies template → quirk and the drift schedule; a missing pack leaves those readings unread."""
    k = {**settings.knobs(), **run.knobs}
    arms_all = settings.arms()
    arms: dict[str, ArmSpec] = {a: arms_all[a] for a in (run.ports or arms_all) if a in arms_all}
    template_quirk: dict[str, str] = {}
    drift_at: dict[str, int] = {}
    drift_quirk: dict[str, str] = {}
    try:
        from munchhausen.world.pack import load_pack

        pack = load_pack(settings.pack_path(run.pack))
        for q in pack.quirks:
            for t in q.templates:
                template_quirk[t] = q.id
        for d, spec in pack.drift_schedule.items():
            knob = str(spec.get("at_knob", "")).lower()
            if knob in k:
                drift_at[d] = int(k[knob])
                if spec.get("quirk"):
                    drift_quirk[d] = str(spec["quirk"])
    except Exception as e:
        print(f"[evidence] pack not read ({type(e).__name__}): quirk-bearing readings are unread", file=sys.stderr)
    return R.Context(
        run_id=run.id, arms=arms, round_size=int(k["round_size"]), run_length=int(k["run_length"]),
        drift_at=drift_at, drift_quirk=drift_quirk, template_quirk=template_quirk,
        label_horizon=int(k["label_horizon"]), drift_window=int(k.get("drift_window", settings.drift_window)),
        bootstrap_n=int(k["bootstrap_n"]), ci_level=float(k["ci_level"]),
        seed=int(k.get("readings_seed", settings.readings_seed)),
        premise_first=int(k.get("backtest_premise_first", settings.backtest_premise_first)),
        premise_share=float(k.get("backtest_premise_share", settings.backtest_premise_share)),
        forecasts=run.forecast_register or forecast_register(settings),
    )


async def readings_for(h: Any, run_id: str) -> tuple[RunRecord, dict[str, Any]]:
    from munchhausen.impl.sinks import read_events

    run = await h.store.runs.get(run_id)
    if run is None:
        raise KeyError(f"no run record for {run_id}")
    rows = await h.store.evidence.snapshot(run_id)
    spend = await h.store.evidence.spend_summary(run_id)
    ctx = reading_context(h.settings, run)
    out = R.all_readings(rows, ctx, spend=spend, events=read_events(h.settings.var_dir, run_id),
                         priced=h.settings.model_prices_usd_per_mtok)
    if not run.forecast_register:
        out["note"] = "run record carries no forecast_register: forecasts read from the current conf (not registered)"
    return run, out
