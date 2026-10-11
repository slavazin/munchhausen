"""Composition root, backward half: builds each arm's round-close hook from its `ArmSpec`.

`bootstrap.py` wires the forward pass and the `ArmRunner`; it asks this module for the `on_round_close`
hook of an arm. The hook is chosen by the arm's `write_path` (none | direct | self_grade | episodic) and
its `curator`, never by the arm's name. Owner: adjudication surface (M3).
"""

from __future__ import annotations

from typing import Any

from munchhausen.loop.runner import RoundHook


def backward_for(h: Any, arm: str) -> RoundHook:
    """Return `async (round, (lo, hi)) -> None`: observe the round's misses, then the arm's write path
    (episodic pass → curator → lifecycle, or the direct writer), then revisit/retire bookkeeping."""
    raise NotImplementedError("M3: observer → write path by ArmSpec.write_path → curator → lifecycle")
