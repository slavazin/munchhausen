"""CLI command groups, one module per surface, so surfaces add commands without editing `cli.py`.

Each module exposes `register(app: typer.Typer) -> None`. A module that fails to import (an optional SDK
missing) is skipped with a note on stderr, so one surface never breaks another's commands.
"""

from __future__ import annotations

import importlib
import sys

import typer

SURFACES = ("world", "forward", "learn", "telemetry", "viewer")


def register(app: typer.Typer) -> None:
    for name in SURFACES:
        try:
            mod = importlib.import_module(f"munchhausen.commands.{name}")
        except ModuleNotFoundError as e:
            if e.name == f"munchhausen.commands.{name}":
                continue
            print(f"[commands] {name} skipped: {e}", file=sys.stderr)
            continue
        mod.register(app)
