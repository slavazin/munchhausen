"""Every registered implementation resolves, constructs uniformly, and satisfies its port."""

from __future__ import annotations

import pytest

from munchhausen.ports import registry
from munchhausen.ports.curation import LensPanel
from munchhausen.ports.grouper import SignalSource
from munchhausen.ports.representation import Representation, Reranker
from munchhausen.ports.sinks import MemorySink, Trace

PROTOCOLS = {"representation": Representation, "reranker": Reranker, "lens_panel": LensPanel,
             "memory_sink": MemorySink, "trace": Trace, "signal_source": SignalSource}

ALL = [(p, n) for p, impls in registry.REGISTRY.items() for n in impls]


@pytest.mark.parametrize(("port", "name"), ALL)
def test_resolves(port: str, name: str) -> None:
    obj = registry.resolve(port, name)
    if port != "curator":
        assert hasattr(obj, "create"), f"{port}:{name} lacks create(name, settings, store)"


def test_every_port_with_an_offline_variant_has_one() -> None:
    for port, name in registry.NULL_IMPLEMENTATION.items():
        assert name in registry.REGISTRY[port]


@pytest.mark.parametrize(("port", "name"), list(registry.NULL_IMPLEMENTATION.items()))
def test_null_implementations_satisfy_ports(port: str, name: str, settings_offline) -> None:  # noqa: ANN001
    if port == "similarity":
        pytest.skip("numpy similarity needs a store loader (M2)")
    impl = registry.resolve(port, name).create(name, settings_offline, None)
    assert isinstance(impl, PROTOCOLS[port])


def test_unknown_name_is_a_clear_error() -> None:
    with pytest.raises(registry.UnknownImplementation, match="known"):
        registry.resolve("trace", "nope")
