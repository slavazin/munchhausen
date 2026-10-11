"""Munchhausen: a harness that admits only what the world confirms.

Layers (dependencies point inward only; enforced by tests/test_architecture.py):

    domain/   pure models and invariants                         (imports nothing else in the package)
    ports/    Protocols for every seam (SPEC § 21)                (imports domain)
    agent/ loop/ learn/ metrics/   application services          (import domain + ports)
    world/ truth/                  the evaluation side of the boundary; reached only through ports
    store/ impl/                   infrastructure implementing ports (the only SDK importers)
    bootstrap.py cli.py            composition root
"""
