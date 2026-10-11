"""Execute (SPEC § 6.1, § 8): resolve the logical collection through the arm's tool-access register and
run the pipeline read-only. Floor decisions act here — a rewired view enforces its `$match` on every
pipeline against that collection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from munchhausen.domain.common import Answer
from munchhausen.domain.episode import Proposal
from munchhausen.ports.store import DocumentReader


class ExecutionError(RuntimeError):
    """An irreducible failure: syntax, timeout, empty result, bad answer_path (the noise filter's class)."""


@dataclass(frozen=True)
class Execution:
    answer: Answer
    resolved: str            # the view or collection actually queried
    rows: int


async def execute(proposal: Proposal, view_map: dict[str, str], world: DocumentReader, *,
                  max_time_ms: int) -> Execution:
    target = view_map.get(proposal.collection, proposal.collection)
    try:
        rows = await world.aggregate(target, proposal.pipeline, max_time_ms=max_time_ms)
    except Exception as e:   # driver errors are data here: they classify the miss as irreducible
        raise ExecutionError(f"{type(e).__name__}: {e}") from e
    return Execution(answer=read_path(rows, proposal.answer_path), resolved=target, rows=len(rows))


def read_path(rows: list[dict[str, Any]], path: str) -> Answer:
    """`answer_path` grammar: `0.total` (row index then dotted keys), or `*.ticker` (a list over rows)."""
    if not rows:
        raise ExecutionError("empty result")
    head, _, rest = path.partition(".")
    if head == "*":
        return [str(_dig(r, rest)) for r in rows]
    value = _dig(rows[int(head)] if head.isdigit() else rows[0], rest if head.isdigit() else path)
    if isinstance(value, (int, float)) or value is None:
        return value
    try:
        return float(value)
    except (TypeError, ValueError) as e:
        raise ExecutionError(f"answer_path {path!r} is not numeric: {value!r}") from e


def _dig(doc: Any, path: str) -> Any:
    for key in filter(None, path.split(".")):
        if not isinstance(doc, dict) or key not in doc:
            raise ExecutionError(f"answer_path segment {key!r} missing")
        doc = doc[key]
    return doc
