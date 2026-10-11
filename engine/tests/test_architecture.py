"""Layer boundaries as tests (SPEC § 21 port invariants, § 7.4 Don't, § 10.2 Frozen at admission)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1] / "munchhausen"


def _modules() -> dict[str, set[str]]:
    """module path (relative, dotted) → set of imported top-level-qualified module names."""
    out: dict[str, set[str]] = {}
    for py in PKG.rglob("*.py"):
        rel = py.relative_to(PKG.parent).with_suffix("")
        name = ".".join(rel.parts).removesuffix(".__init__")
        imports: set[str] = set()
        for node in ast.walk(ast.parse(py.read_text())):
            if isinstance(node, ast.Import):
                imports |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports.add(node.module)
        out[name] = imports
    return out


MODULES = _modules()


def _importers(prefix: str) -> set[str]:
    return {m for m, imps in MODULES.items() if any(i == prefix or i.startswith(prefix + ".") for i in imps)}


def _under(module: str, *packages: str) -> bool:
    return any(module == f"munchhausen.{p}" or module.startswith(f"munchhausen.{p}.") for p in packages)


def test_pymongo_only_in_store() -> None:
    offenders = {m for m in _importers("pymongo") | _importers("bson") if not _under(m, "store")}
    assert not offenders, f"pymongo imported outside store/: {sorted(offenders)}"


@pytest.mark.parametrize("sdk", ["anthropic", "voyageai", "typesafe", "raindrop"])
def test_vendor_sdks_only_in_impl(sdk: str) -> None:
    offenders = {m for m in _importers(sdk) if not _under(m, "impl")}
    assert not offenders, f"{sdk} imported outside impl/: {sorted(offenders)}"


def test_domain_is_pure() -> None:
    allowed_internal = "munchhausen.domain"
    for m, imps in MODULES.items():
        if not _under(m, "domain"):
            continue
        internal = {i for i in imps if i.startswith("munchhausen")}
        assert all(i.startswith(allowed_internal) for i in internal), f"{m} imports {internal}"
        assert not imps & {"pymongo", "anthropic", "voyageai", "yaml", "pydantic_settings"}, m


def test_ports_depend_only_on_domain() -> None:
    for m, imps in MODULES.items():
        if not _under(m, "ports"):
            continue
        internal = {i for i in imps if i.startswith("munchhausen")}
        assert all(i.startswith(("munchhausen.domain", "munchhausen.ports")) for i in internal), (m, internal)


@pytest.mark.parametrize("package", ["learn", "agent", "loop"])
def test_gold_isolation(package: str) -> None:
    """Truth and world (which holds hidden tags) are reachable from the learning path only through ports."""
    for m, imps in MODULES.items():
        if _under(m, package):
            bad = {i for i in imps if i.startswith(("munchhausen.truth", "munchhausen.world"))}
            assert not bad, f"{m} imports {bad}"


def test_truth_importers() -> None:
    allowed = ("metrics", "world", "truth")
    offenders = {m for m in _importers("munchhausen.truth") if not _under(m, *allowed)
                 and m != "munchhausen.ports.registry"}
    assert not offenders, f"truth imported from {sorted(offenders)}"


def test_application_does_not_import_infrastructure() -> None:
    for m, imps in MODULES.items():
        if _under(m, "agent", "loop", "learn", "metrics"):
            bad = {i for i in imps if i.startswith(("munchhausen.store", "munchhausen.impl", "munchhausen.bootstrap"))}
            assert not bad, f"{m} imports infrastructure {bad}"


def test_only_decision_store_updates_decisions() -> None:
    """No module but store/decisions.py issues a write against the `decisions` collection."""
    writes = ("update_one", "update_many", "replace_one", "find_one_and_update", "insert_one", "insert_many",
              "delete_one", "delete_many", "bulk_write", "find_one_and_replace")
    for py in PKG.rglob("*.py"):
        if py.name == "decisions.py" and py.parent.name == "store":
            continue
        src = py.read_text()
        if "C.DECISIONS" not in src and '"decisions"' not in src:
            continue
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in writes:
                target = ast.unparse(node.func.value)
                assert "DECISIONS" not in target and "decisions" not in target, f"{py}: {ast.unparse(node)}"
