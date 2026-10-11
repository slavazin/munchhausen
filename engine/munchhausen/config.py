"""Every knob, model, threshold, size and path (SPEC § 15, § 16, § 24 knob list).

Do: add a knob here before using a literal in a module. Don't: inline a literal because the knob is
missing. Values come from the environment (UPPER_CASE) or the repo-root `.env`; YAML registers live
under `engine/conf/` and `engine/packs/`. Where this file and SPEC § 16 differ, this file holds.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from munchhausen.domain.arm import ArmSpec
from munchhausen.domain.backtest import BacktestThresholds
from munchhausen.domain.common import AuthorityLevel
from munchhausen.domain.lens import LensEntry, LensWeights

ENGINE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ENGINE_ROOT.parent

Role = Literal["learner", "evaluator", "executor"]
AuthMode = Literal["api_key_workspace", "oauth_fallback", "oauth", "api_key", "none"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore", frozen=True)

    # --- run identity -------------------------------------------------------------------------------
    run_id: str = "dev"

    # --- Atlas ---------------------------------------------------------------------------------------
    mongodb_uri: SecretStr | None = None
    mongodb_uri_learner: SecretStr | None = None
    mongodb_uri_evaluator: SecretStr | None = None
    mongodb_uri_executor: SecretStr | None = None
    store_db: str = "munchhausen"
    world_db: str = "world"
    truth_db: str = "truth"
    source_db: str = "sample_analytics"
    execute_max_time_ms: int = 3000
    exact_below: int = 2000
    lease_ttl_s: int = 120
    poll_interval_s: float = 2.0
    search_index_cap: int = 3           # M0/Flex sandbox: 3 search-type indexes in total; verify at M0

    # --- keys (SDKs also read their own env vars; held here so `doctor` can report presence) ---------
    # Aliases accept the names the user's `.env` carries; the canonical UPPER_CASE names still win.
    anthropic_api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("ANTHROPIC_API_KEY", "anthropic_api_key", "anthropic_munch_key"))
    # An organization-level key not scoped to a workspace must send `anthropic-workspace-id` on every request.
    anthropic_workspace_id: str | None = Field(
        default=None, validation_alias=AliasChoices(
            "ANTHROPIC_WORKSPACE_ID", "anthropic_workspace_id", "anthropic_workspace_key"))
    anthropic_auth_token: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("ANTHROPIC_AUTH_TOKEN", "anthropic_auth_token", "claude_oauth_key"))
    voyage_api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("VOYAGE_API_KEY", "voyage_api_key", "voyage_key"))
    typesafe_api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("TYPESAFE_API_KEY", "typesafe_api_key", "typesafe_key"))
    raindrop_write_key: SecretStr | None = None
    raindrop_query_key: SecretStr | None = None

    # --- world ---------------------------------------------------------------------------------------
    world_impl: str = "pack"
    world_adapter: str = "sample_analytics"
    world_pack: str = "analytics-v1"
    world_seed: int = 7
    stream_seed: int = 11
    v_seed: int = 13
    quirk_share: float = 0.65
    run_length: int = 900
    d1_at: int = 300
    d2_at: int = 600
    authority_level: AuthorityLevel = AuthorityLevel.TERM
    authority_poison_rate: float = 0.05
    v_size: int = 40
    v_every: int = 150                  # V points per arm: 6 over RUN_LENGTH; ±15pp at V_SIZE 40, so read as paired
    v_offset: int = 75                  # first V read; with V_EVERY 150 no read lands on D1_AT or D2_AT
    frozen_stream: bool = True          # frozen runs the stream: the paired no-learning baseline
    vocab_warmup: int = 40
    schema_sample_docs: int = 50        # docs per collection sampled for the schema summary (names + types)
    schema_max_depth: int = 2           # nesting depth the schema summary walks (`transactions.symbol`)
    pilot_n: int = 40                   # SPEC § 12 pilot gate: stream questions answered by the frozen proposer
    pilot_quirk_max: float = 0.35       # gate holds if quirk-bearing accuracy ≤ this …
    pilot_control_min: float = 0.70     # … and control accuracy ≥ this
    kickoff_max_time_ms: int = 60_000   # source-profile aggregations in `kickoff-check` / `build-world`
    gold_check_combos: int = 12         # parameter combinations per template in the build-time gold checks

    # --- scoring -------------------------------------------------------------------------------------
    score_rel_tol: float = 1e-4
    score_abs_tol_rounded: float = 0.5

    # --- forward pass --------------------------------------------------------------------------------
    workers_per_arm: int = 6
    context_budget_tokens: int = 900
    naive_top_k: int = 8
    naive_merge_cosine: float = 0.92
    fire_min_residuals: int = 2
    fire_window: int = 30
    # S2 (M2) forward pass, consultation and runtime sandbox
    proposer_temperature: float = 0.0   # 0 reduces replay noise in the paired backtest; recorded in runs.knobs
    proposer_max_tokens: int = 4000
    propose_attempts: int = 2           # proposer calls per episode before the episode records an error
    episode_attempts: int = 2           # runner re-runs of an episode that raised before leaving it orphaned
    pipeline_row_cap: int = 5000        # sandbox: a world read past this many rows is refused
    pipeline_max_time_ms: int = 10000   # sandbox: ceiling on any caller's maxTimeMS against `world`
    vocab_min_questions: int = 2        # warmup questions that must present a noun phrase
    vocab_max_phrase_tokens: int = 3    # longest noun phrase mined from warmup questions
    terms_search_limit: int = 100       # candidate terms read from `terms_search` per text
    fire_fetch_factor: int = 2          # consultations read per guard-window slot (V ones filtered)
    rounding_unit_base: int = 10        # rounding signature: unit = largest power of this base dividing the figure
    vocab_report_sample: int = 40       # terms printed by `seed-vocab`

    # --- backward pass -------------------------------------------------------------------------------
    round_size: int = 30
    carry_rounds: int | None = None     # None: carry every open observation until a shape spends it
    cluster_distance: float = 0.35
    embed_mask: Literal["none", "surfaces"] = "none"
    bar_min_obs: int = 2
    bar_min_templates: int = 2
    bar_min_templates_floor: int = 3
    bar_min_gap: float = 0.10           # E4 direction read: miss rate inside the shape's presentation − outside
    bar_min_matched: int = 10           # episodes the presentation must match before the gap is read
    neighbour_k: int = 5                # admitted neighbours shown to the nominator and routed at L2
    neighbour_rerank: float = 0.85
    lens_mode: Literal["record", "gate"] = "record"   # record: L3 scores, every draft reaches the backtest
    lens_threshold: float = 0.5
    lens_explore_eps: float = 0.1
    lens_call_mode: Literal["isolated", "joint"] = "isolated"
    backtest_n: int = 8
    backtest_min_fixed: int = 2
    backtest_min_fixed_heldout: int = 1
    backtest_max_broken: int = 1
    retire_idle: int = 300
    retire_fires: int = 6
    seed_decisions: str = "empty"
    not_this_min: int = 3
    fusion: Literal["rank", "score"] = "rank"
    # adjudication surface (S4, M3b)
    backtest_sample: Literal["hashed", "random"] = "hashed"   # hashed: `$facet` + seeded hash order (replayable)
    backtest_seed: int = 17             # seed of the hashed balanced sample
    backtest_concurrency: int = 4       # paired replays in flight per backtest (2 × BACKTEST_N calls in total)
    backtest_min_n: int = 4             # scored pairs below this: L4 holds (`insufficient`), never refuses
    backtest_recent: int | None = 300   # a new draft's population: the last N episodes (None: all); a
    #                                     supersede reads from the predecessor's fire instead
    l2_route_contested: bool = False    # L2 also routes a `new` draft as supersede when exactly one contested
    #                                     neighbour shares a hook term (off: minimum configuration, § 3a)
    direct_merge: bool = True           # lessons merge into an admitted decision at NAIVE_MERGE_COSINE
    lesson_max_tokens: int = 2000
    self_grade_max_tokens: int = 2000
    lens_max_concurrency: int = 5       # isolated Jev calls in flight per draft
    lens_phrasings: int = 3             # phrasings asked per lens (1–3); > 1 logs hedging, mean 4p(1−p) (§ 24.2 L6)
    lens_model: str | None = None       # TypeSafe model; None: the SDK default (jev-latest)
    lens_timeout_s: float = 20.0

    # --- shaping (S3: observer, episodic pass, nominator) ---------------------------------------------
    observer_max_tokens: int = 4000
    nominator_max_tokens: int = 16000
    nominator_max_tool_turns: int = 12      # model turns in the nominator's world-tool loop before it must submit
    nominator_tool_max_rows: int = 50       # rows one world-tool call returns to the nominator ($limit appended)
    nominator_tool_max_time_ms: int = 5000  # maxTimeMS per world-tool aggregate
    nominator_tool_result_chars: int = 6000 # characters of one tool result shown to the nominator
    nominator_residual_window: int = 4     # recent consultations read per neighbour for its residuals
    nominator_min_options: int = 2          # options rows: >= 1 prior (rejected) + the chosen definition
    # Direction read window when no contested neighbour dates a drift: the last N episodes the shape's
    # presentation matches (and the same idx window outside it). 40 = 4 x BAR_MIN_MATCHED: a miss-rate gap
    # of BAR_MIN_GAP reads above the ~0.08 standard error of a rate at n=40, and the window spans a few
    # rounds of matched episodes, so a post-drift gap is not diluted by every pre-drift episode.
    direction_window: int = 40
    error_prompt_chars: int = 300           # characters of a driver error shown to a party (code + errmsg)

    # --- second-order loop ---------------------------------------------------------------------------
    label_horizon: int = 150
    lensfit_min_labels: int = 20
    lens_fold_rho: float = 0.8
    lens_mint_min: int = 4

    # --- readings ------------------------------------------------------------------------------------
    bootstrap_n: int = 2000             # resamples for paired arm differences
    ci_level: float = 0.90              # interval level for every paired difference and forecast verdict
    readings_seed: int = 17             # bootstrap seed for every reading (a report re-derives byte-identically)
    drift_window: int = 150             # F1: episodes before and after a drift index read for the gap
    backtest_premise_first: int = 10    # § 12 premise: the first N backtests per arm
    backtest_premise_share: float = 0.5 # § 12 premise: share of encoded misses the replay must fix
    # USD per million tokens, per model id (Anthropic first-party list prices, read 2026-10-11).
    # cache_write is the 5-minute write rate (1.25 × input). A model missing here is priced at 0 and the
    # report says so (`unpriced_models`).
    model_prices_usd_per_mtok: dict[str, dict[str, float]] = {
        "claude-haiku-4-5": {"in": 1.0, "out": 5.0, "cache_read": 0.10, "cache_write": 1.25},
        "claude-haiku-5-5": {"in": 0.10, "out": 0.50, "cache_read": 0.01, "cache_write": 0.125},
        "claude-sonnet-5-5": {"in": 2.0, "out": 10.0, "cache_read": 0.20, "cache_write": 2.50},
        "claude-opus-5-5": {"in": 4.0, "out": 20.0, "cache_read": 0.20, "cache_write": 5.0},
    }
    response_cache: bool = False        # cache parsed model responses under var/cache/ (trace-invariance replay)
    planted_map_concurrency: int = 4    # concurrent planted-map judge calls (evaluation only)
    anthropic_oauth_beta: str = "oauth-2025-04-20"   # beta header sent when authenticating with an OAuth token
    chartjs_url: str = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"

    # --- models --------------------------------------------------------------------------------------
    proposer_model: str = "claude-haiku-4-5"
    observer_model: str = "claude-haiku-4-5"
    nominator_model: str = "claude-sonnet-5-5"
    nominator_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    naive_lesson_model: str = "claude-sonnet-5-5"   # = nominator model: the payload's author is not a confound
    lens_fallback_model: str = "claude-opus-5-5"
    planted_map_model: str = "claude-opus-5-5"
    embed_model: str = "voyage-4"
    embed_dim: int = 1024
    rerank_model: str = "rerank-3"
    model_max_retries: int = 4

    # --- global port selections (per-arm overrides live in conf/arms.yaml) ---------------------------
    store_impl: str = "atlas"
    models_impl: str = "anthropic"
    trace_impl: str = "null"
    signal_source_impl: str = "none"

    # --- paths ---------------------------------------------------------------------------------------
    conf_dir: Path = ENGINE_ROOT / "conf"
    packs_dir: Path = ENGINE_ROOT / "packs"
    var_dir: Path = REPO_ROOT / "var"

    # --- viewer and injection (S6, SPEC § 17) --------------------------------------------------------
    viewer_host: str = "127.0.0.1"      # loopback by default; the viewer exposes no secret but drives the engine
    viewer_port: int = 8766
    viewer_run_id: str | None = None    # run shown first; None: RUN_ID
    viewer_arm: str = "governed"        # the decision pane's first arm (SPEC § 17); a switcher reaches the others
    viewer_reference_arm: str | None = None   # paired reference; None: the arm whose write_path is none
    viewer_watch: tuple[str, ...] = ("fires", "decisions", "rounds", "tool_access", "episodes")
    viewer_consumer: str = "viewer"     # change-stream consumer name for its resume token in `cursors`
    viewer_fire_limit: int = 200
    viewer_draft_limit: int = 50
    viewer_why_depth: int = 8           # `$graphLookup` maxDepth for lineage
    viewer_curve_window: int | None = None    # rolling window in episodes; None: ROUND_SIZE
    viewer_floor_rows: int = 3          # result rows shown per side in the floor beat's before/after
    viewer_sse_keepalive_s: float = 15.0
    inject_seed: int = 101              # question instances for injection: never the stream's seed
    inject_per_template: int = 1        # questions per chosen template (≥ BAR_MIN_OBS in total)
    inject_scan_max: int = 5000         # questions scanned to find instances of the chosen templates
    inject_idx_base: int = -1_000_000   # injection episodes take free idx <= this: far below V's -(1 + k*V_SIZE + j)
    inject_max_templates: int = 3       # distinct templates per injection (cost: forward passes + 2*BACKTEST_N)
    inject_stage: str = "inject"        # spend `meta.stage` of the injection's proposer calls; rounds exclude it
    viewer_max_jobs: int = 20           # injection jobs kept in memory; the oldest finished are dropped
    viewer_allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost")   # Host header check (plus VIEWER_HOST)
    viewer_allow_public: bool = False   # refuse binding a non-loopback address unless set

    # ------------------------------------------------------------------------------------------------

    def uri_for(self, role: Role) -> str:
        """Per-role connection string, falling back to MONGODB_URI (gold isolation, SPEC § 20.2)."""
        specific = getattr(self, f"mongodb_uri_{role}")
        uri = specific or self.mongodb_uri
        if uri is None:
            raise RuntimeError("MONGODB_URI is not set (see .env.example)")
        return uri.get_secret_value()

    @property
    def backtest_thresholds(self) -> BacktestThresholds:
        return BacktestThresholds(min_fixed=self.backtest_min_fixed,
                                  min_fixed_heldout=self.backtest_min_fixed_heldout,
                                  max_broken=self.backtest_max_broken, min_n=self.backtest_min_n)

    def knobs(self) -> dict[str, Any]:
        """Every non-secret knob, for `runs.knobs` at run start (SPEC § 11 pre-registration)."""
        secrets = {k for k, f in type(self).model_fields.items() if "SecretStr" in str(f.annotation)}
        return self.model_dump(mode="json", exclude=secrets)

    # --- YAML registers ----------------------------------------------------------------------------

    def arms(self) -> dict[str, ArmSpec]:
        raw = _yaml(self.conf_dir / "arms.yaml")
        defaults = raw.get("default_ports", {})
        out: dict[str, ArmSpec] = {}
        for name, spec in raw["arms"].items():
            spec = {**spec, "name": name, "ports": {**defaults, **spec.get("ports", {})}}
            if "stream_knob" in spec:                     # e.g. frozen: stream follows FROZEN_STREAM
                spec["stream"] = getattr(self, spec.pop("stream_knob"))
            out[name] = ArmSpec.model_validate(spec)
        return out

    def lenses(self) -> list[LensEntry]:
        return [LensEntry.model_validate(e) for e in _yaml(self.conf_dir / "lenses.yaml")["lenses"]]

    def seed_lens_weights(self) -> LensWeights:
        return LensWeights.model_validate(_yaml(self.conf_dir / "lenses.yaml")["weights_v0"])

    def latch_ports(self) -> dict[str, Any]:
        return _yaml(self.conf_dir / "latch_ports.yaml")

    def forecasts(self) -> dict[str, dict[str, Any]]:
        return _yaml(self.conf_dir / "forecasts.yaml")["forecasts"]

    def pack_path(self, name: str | None = None) -> Path:
        return self.packs_dir / f"{name or self.world_pack}.yaml"

    def usd(self, model: str, tokens_in: int, tokens_out: int, cache_read: int = 0, cache_write: int = 0) -> float:
        """List-price USD of one call from `MODEL_PRICES_USD_PER_MTOK`; 0 for an unpriced model."""
        p = self.model_prices_usd_per_mtok.get(model)
        if p is None:
            return 0.0
        return (tokens_in * p["in"] + tokens_out * p["out"] + cache_read * p.get("cache_read", 0.0)
                + cache_write * p.get("cache_write", 0.0)) / 1e6

    def isolation(self) -> Literal["roles", "convention"]:
        """`roles` iff every per-role Atlas URI is set (SPEC § 20.2); otherwise gold isolation is by convention."""
        roles = (self.mongodb_uri_learner, self.mongodb_uri_evaluator, self.mongodb_uri_executor)
        return "roles" if all(r is not None for r in roles) else "convention"

    def keys_present(self) -> dict[str, bool]:
        """Presence of every secret knob. Never a value."""
        secrets = [k for k, f in type(self).model_fields.items() if "SecretStr" in str(f.annotation)]
        return {k: getattr(self, k) is not None for k in secrets}

    def anthropic_auth_mode(self) -> AuthMode:
        """Which credential the Anthropic client uses (recorded in `runs`, never a value):
        `api_key_workspace` — API key with `ANTHROPIC_WORKSPACE_ID` (an org-level key needs the header);
        `oauth_fallback` — an API key is present but no workspace id, so the OAuth token is used;
        `oauth` — only the token; `api_key` — a key with neither workspace id nor token; `none`."""
        key_, token = self.anthropic_api_key is not None, self.anthropic_auth_token is not None
        if key_ and self.anthropic_workspace_id:
            return "api_key_workspace"
        if key_ and token:
            return "oauth_fallback"
        if token:
            return "oauth"
        return "api_key" if key_ else "none"

    def model_ids(self) -> dict[str, str]:
        return {k: v for k, v in self.knobs().items() if k.endswith("_model") and isinstance(v, str)}


def _yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
