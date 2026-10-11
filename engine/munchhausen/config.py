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
    anthropic_workspace_id: str | None = None
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

    # --- second-order loop ---------------------------------------------------------------------------
    label_horizon: int = 150
    lensfit_min_labels: int = 20
    lens_fold_rho: float = 0.8
    lens_mint_min: int = 4

    # --- readings ------------------------------------------------------------------------------------
    bootstrap_n: int = 2000             # resamples for paired arm differences
    ci_level: float = 0.90              # interval level for every paired difference and forecast verdict

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
                                  max_broken=self.backtest_max_broken)

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


def _yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
