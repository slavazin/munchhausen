"""Shared construction contract: every implementation exposes `create(name, settings, store)`, so the
composition root resolves a name and calls one factory — adding an implementation touches only the
registry and its own module (open/closed)."""

from __future__ import annotations

from typing import Any, Self

from munchhausen.config import Settings


def key(settings: Settings, name: str) -> str | None:
    v = getattr(settings, name)
    return v.get_secret_value() if v is not None else None


class NoDeps:
    @classmethod
    def create(cls, name: str, settings: Settings, store: Any = None) -> Self:
        return cls()
