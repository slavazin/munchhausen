"""The learning path reaches the world only through the World port (SPEC § 21). The import test forbids
importing `world/` and `truth/`; this grep forbids reaching the evaluation-side attributes of a World object
that the composition root hands in (`.truth`, `.bank`, `.pack`, `.hidden(`, `.inventory(`, `.poisoned(`).
`instances(` stays allowed: the injection beat (S6, `loop/inject.py`) uses it."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1] / "munchhausen"
EVALUATION_SIDE = re.compile(r"\.(truth|bank|pack|pack_hash)\b|\.(hidden|inventory|poisoned)\(")


@pytest.mark.parametrize("package", ["learn", "agent", "loop"])
def test_learning_path_never_reaches_world_internals(package: str) -> None:
    hits = []
    for py in (PKG / package).rglob("*.py"):
        for n, line in enumerate(py.read_text().splitlines(), 1):
            code = line.split("#", 1)[0]
            if EVALUATION_SIDE.search(code):
                hits.append(f"{py.relative_to(PKG)}:{n}: {line.strip()}")
    assert not hits, hits
