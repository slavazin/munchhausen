from __future__ import annotations

from munchhausen.config import Settings
from munchhausen.domain.arm import ConsultationMode, WritePath


def test_seed_knobs_match_spec(settings_offline: Settings) -> None:
    s = settings_offline
    assert (s.world_seed, s.run_length, s.d1_at, s.d2_at, s.round_size) == (7, 900, 300, 600, 30)
    assert (s.backtest_min_fixed, s.backtest_max_broken, s.backtest_min_fixed_heldout) == (2, 1, 1)
    assert s.proposer_model == "claude-haiku-4-5" and s.nominator_model == "claude-sonnet-5-5"


def test_arms_load(settings_offline: Settings) -> None:
    arms = settings_offline.arms()
    assert set(arms) == {"frozen", "self_ref", "naive", "governed"}
    assert arms["governed"].consultation is ConsultationMode.HOOKS
    assert arms["governed"].write_path is WritePath.EPISODIC
    assert arms["governed"].ports["lens_panel"] == "jev"
    assert arms["naive"].ports["lens_panel"] == "none"
    assert arms["frozen"].stream is False
    assert not arms["self_ref"].authority


def test_lenses_load_and_are_never_dispositive(settings_offline: Settings) -> None:
    lenses = settings_offline.lenses()
    assert len(lenses) >= 5
    assert all(lens.role.value != "dispositive" for lens in lenses)
    assert settings_offline.seed_lens_weights().weights["case_leak"] == -2.0


def test_knobs_exclude_secrets(settings_offline: Settings) -> None:
    knobs = settings_offline.knobs()
    assert "mongodb_uri" not in knobs and "anthropic_api_key" not in knobs
    assert knobs["round_size"] == 30


def test_forecasts_preregistered(settings_offline: Settings) -> None:
    assert set(settings_offline.forecasts()) == {"F1", "F2", "F3", "F4", "F5"}
