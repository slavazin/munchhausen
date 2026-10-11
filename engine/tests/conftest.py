from __future__ import annotations

import pytest

from munchhausen.config import Settings


@pytest.fixture
def settings_offline(tmp_path) -> Settings:  # noqa: ANN001
    """Settings that ignore the developer's .env (no network, no keys)."""
    return Settings(_env_file=None, var_dir=tmp_path)
