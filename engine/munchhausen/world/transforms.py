"""Transform registry (SPEC § 4.1). Packs reference these by name with parameters; they never carry code.

Three registries, all evaluation-side:
- `MATERIALIZE[name](data, params, seed) -> data`: writes quirk fields into the documents that become `world`.
  Deterministic under `WORLD_SEED` through `stable_bucket`.
- `GOLD[name](params) -> {slot: value}`: a quirk's definition, as overrides of named **slots** that every
  measure reads (`customer_kept`, `bucket_kept`, `active_customer`, `revenue`, `present`, …). A quirk changes
  only the slots it names; the gold isolation test proves no other template reads them on the built data.
- `MEASURE[name](data, slots, qparams, args) -> Answer`: what a template asks, computed in Python over the
  materialized documents. Every measure applies the `*_kept` slot of each collection it reads, so a floor
  quirk added later reaches every template that touches its population (and the isolation test fails if a
  template outside the quirk is touched).

Gold is computed in Python, not as an Atlas pipeline: the same functions run over fixtures offline and over
`world` live, and a gold bug is indistinguishable from poison (SPEC § 4.3 Don't).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

Doc = dict[str, Any]
Data = dict[str, list[Doc]]
Slots = dict[str, Any]
MaterializeFn = Callable[[Data, dict[str, Any], int], Data]
GoldFn = Callable[[dict[str, Any]], Slots]
MeasureFn = Callable[[Data, Slots, dict[str, Any], dict[str, Any]], Any]

MATERIALIZE: dict[str, MaterializeFn] = {}
GOLD: dict[str, GoldFn] = {}
MEASURE: dict[str, MeasureFn] = {}


def materialize(name: str) -> Callable[[MaterializeFn], MaterializeFn]:
    def deco(fn: MaterializeFn) -> MaterializeFn:
        MATERIALIZE[name] = fn
        return fn
    return deco


def gold(name: str) -> Callable[[GoldFn], GoldFn]:
    def deco(fn: GoldFn) -> GoldFn:
        GOLD[name] = fn
        return fn
    return deco


def measure(name: str) -> Callable[[MeasureFn], MeasureFn]:
    def deco(fn: MeasureFn) -> MeasureFn:
        MEASURE[name] = fn
        return fn
    return deco


def stable_bucket(key: str, seed: int, buckets: int = 10_000) -> int:
    """Deterministic hash assignment (e.g. Q1's 50/20/15/15% status split) under WORLD_SEED."""
    return int(hashlib.sha256(f"{seed}:{key}".encode()).hexdigest(), 16) % buckets


def stable_unit(key: str, seed: int) -> float:
    """`stable_bucket` scaled to [0, 1)."""
    return stable_bucket(key, seed) / 10_000


def pick_share(u: float, values: list[Any], shares: list[float]) -> Any:
    """The value whose cumulative share first exceeds u (shares need not sum to 1; the last value absorbs)."""
    acc = 0.0
    for v, s in zip(values, shares, strict=True):
        acc += s
        if u < acc:
            return v
    return values[-1]


# --- base slots: the conventional meaning before any quirk ------------------------------------------


class UndefinedConcept(LookupError):
    """A template read a slot no quirk defines: the pack is missing the quirk the template names."""


def _undefined(name: str) -> Callable[..., Any]:
    def fn(*_: Any) -> Any:
        raise UndefinedConcept(f"slot {name!r} has no definition in this pack")
    return fn


def base_slots() -> Slots:
    return {
        "customer_kept": lambda c: True,
        "account_kept": lambda a: True,
        "bucket_kept": lambda b: True,
        "active_customer": _undefined("active_customer"),
        "revenue": _undefined("revenue"),
        "tech_symbol": _undefined("tech_symbol"),
        "present": lambda x: x,
    }


# --- materialize transforms -------------------------------------------------------------------------


@materialize("assign_codes")
def assign_codes(data: Data, params: dict[str, Any], seed: int) -> Data:
    """Q1: every doc of `collection` gets `field` ∈ codes, hash-assigned by `key` at `shares`."""
    coll, field, key = params["collection"], params["field"], params["key"]
    out = []
    for doc in data[coll]:
        u = stable_unit(f"{field}:{doc[key]}", seed)
        out.append({**doc, field: pick_share(u, params["codes"], params["shares"])})
    return {**data, coll: out}


@materialize("mark_removed")
def mark_removed(data: Data, params: dict[str, Any], seed: int) -> Data:
    """Q3: a `removed_share` of docs carry `field: removed` (the real marker); a `decoy_share` carry a non-null
    `decoy_field` (legacy; those still count); every other doc carries `field` ∈ other_codes and a null decoy.

    Marked and decoy docs keep only items whose `kind_field` equals `keep_kind`. That places Q3's population
    where no other quirk's template reads (revenue and the sell controls read only the other kind), so a
    proposer that honours the decoy, or ignores the marker, changes only Q3's templates (gold isolation)."""
    coll, field, key = params["collection"], params["field"], params["key"]
    items, kind_field, keep = params["items"], params["kind_field"], params["keep_kind"]
    removed_share, decoy_share = params["removed_share"], params["decoy_share"]
    out = []
    for doc in data[coll]:
        u = stable_unit(f"{field}:{doc[key]}", seed)
        d = dict(doc)
        if u < removed_share + decoy_share:
            d[items] = [t for t in doc[items] if t[kind_field] == keep]
            d[params["count_field"]] = len(d[items])
        if u < removed_share:
            d[field], d[params["decoy_field"]] = params["removed"], None
        else:
            v = stable_unit(f"{field}:code:{doc[key]}", seed)
            d[field] = pick_share(v, params["other_codes"], params["other_shares"])
            d[params["decoy_field"]] = doc[params["decoy_from"]] if u < removed_share + decoy_share else None
        out.append(d)
    return {**data, coll: out}


# --- gold transforms (definitions as slot overrides) ------------------------------------------------


@gold("in_set")
def in_set(params: dict[str, Any]) -> Slots:
    """A doc is in the concept iff `field` ∈ values (Q1: active ⇔ st ∈ {2, 7}; D1 adds 4)."""
    field, values = params["field"], frozenset(params["values"])
    return {params["slot"]: lambda d: d.get(field) in values}


@gold("exclude_value")
def exclude_value(params: dict[str, Any]) -> Slots:
    """A floor: docs with `field == value` are excluded from every count and sum (Q3: rs == 3)."""
    field, value = params["field"], params["value"]
    return {params["slot"]: lambda d: d.get(field) != value}


@gold("net_of_fee")
def net_of_fee(params: dict[str, Any]) -> Slots:
    """Q5: revenue = Σ `amount_field` (stored as a string) over items of `kind` × factor."""
    kind_field, kind, amount, factor = params["kind_field"], params["kind"], params["amount_field"], params["factor"]

    def revenue(trades: Iterable[Doc]) -> float:
        return sum(float(t[amount]) for t in trades if t[kind_field] == kind) * factor
    return {"revenue": revenue}


@gold("round_to")
def round_to(params: dict[str, Any]) -> Slots:
    """P1: the figure is presented rounded to the nearest `unit` (half away from zero)."""
    unit = params["unit"]

    def present(x: Any) -> Any:
        if not isinstance(x, (int, float)):
            return x
        q = abs(x) / unit
        r = int(q) + (1 if q - int(q) >= 0.5 else 0)
        return (r if x >= 0 else -r) * unit
    return {"present": present}


def compose(*overrides: Slots) -> Slots:
    out = base_slots()
    for o in overrides:
        out.update(o)
    return out


# --- measures (what a template asks) ----------------------------------------------------------------


def _year(d: Any) -> int:
    return d.year if isinstance(d, datetime) else int(str(d)[:4])


def _month(d: Any) -> int:
    return d.month if isinstance(d, datetime) else int(str(d)[5:7])


def _accounts_by_id(data: Data, slots: Slots) -> dict[Any, Doc]:
    return {a["account_id"]: a for a in data["accounts"] if slots["account_kept"](a)}


def _customers(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> list[Doc]:
    accounts = _accounts_by_id(data, slots) if "product" in p else {}
    out = []
    for c in data["customers"]:
        if not slots["customer_kept"](c):
            continue
        if args.get("active") and not slots["active_customer"](c):
            continue
        if "born_from" in p and _year(c["birthdate"]) < p["born_from"]:
            continue
        if "born_before" in p and _year(c["birthdate"]) >= p["born_before"]:
            continue
        if "product" in p and not any(p["product"] in accounts.get(a, {}).get("products", ())
                                      for a in c.get("accounts", ())):
            continue
        out.append(c)
    return out


@measure("customers_count")
def customers_count(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> int:
    return len(_customers(data, slots, p, args))


@measure("customers_avg_accounts")
def customers_avg_accounts(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> float:
    cs = _customers(data, slots, p, args)
    return sum(len(c.get("accounts", ())) for c in cs) / len(cs) if cs else 0.0


@measure("customers_accounts_limit_sum")
def customers_accounts_limit_sum(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> int:
    """Σ limit over the distinct accounts (present in `accounts`) held by the selected customers."""
    accounts = _accounts_by_id(data, slots)
    ids = {a for c in _customers(data, slots, p, args) for a in c.get("accounts", ()) if a in accounts}
    return sum(accounts[a]["limit"] for a in ids)


def _accounts(data: Data, slots: Slots, p: dict[str, Any]) -> list[Doc]:
    out = []
    for a in data["accounts"]:
        if not slots["account_kept"](a):
            continue
        if "product" in p and p["product"] not in a.get("products", ()):
            continue
        if "limit_at_least" in p and a["limit"] < p["limit_at_least"]:
            continue
        out.append(a)
    return out


@measure("accounts_count")
def accounts_count(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> int:
    return len(_accounts(data, slots, p))


@measure("accounts_avg_limit")
def accounts_avg_limit(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> float:
    xs = _accounts(data, slots, p)
    return sum(a["limit"] for a in xs) / len(xs) if xs else 0.0


def _trades(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> list[Doc]:
    out = []
    for b in data["transactions"]:
        if not slots["bucket_kept"](b):
            continue
        for t in b.get("transactions", ()):
            if "kind" in args and t["transaction_code"] != args["kind"]:
                continue
            if args.get("tech") and not slots["tech_symbol"](t):
                continue
            if "symbol" in p and t["symbol"] != p["symbol"]:
                continue
            if "year" in p and _year(t["date"]) != p["year"]:
                continue
            if "month" in p and _month(t["date"]) != p["month"]:
                continue
            out.append(t)
    return out


@measure("trades_count")
def trades_count(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> int:
    return len(_trades(data, slots, p, args))


@measure("trades_amount_sum")
def trades_amount_sum(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> int:
    return sum(t["amount"] for t in _trades(data, slots, p, args))


@measure("revenue")
def revenue(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> float:
    return float(slots["revenue"](_trades(data, slots, p, args)))


@measure("buckets_with_symbol")
def buckets_with_symbol(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> int:
    return sum(1 for b in data["transactions"]
               if slots["bucket_kept"](b) and any(t["symbol"] == p["symbol"] for t in b.get("transactions", ())))


@measure("trades_share")
def trades_share(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> float:
    """Share of trades (of `args.kind`) in the period that pass the `tech` slot."""
    base = {k: v for k, v in args.items() if k != "tech"}
    every = len(_trades(data, slots, p, base))
    return len(_trades(data, slots, p, args)) / every if every else 0.0


@measure("accounts_trading")
def accounts_trading(data: Data, slots: Slots, p: dict[str, Any], args: dict[str, Any]) -> int:
    """Distinct accounts with at least one matching trade in a kept bucket."""
    return len({b["account_id"] for b in data["transactions"] if slots["bucket_kept"](b)
                and _trades({"transactions": [b]}, slots, p, args)})
