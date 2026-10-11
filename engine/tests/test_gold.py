"""Gold per transform on a hand-computed fixture (SPEC § 4.3 Do). A gold bug is indistinguishable from poison.

Fixture (already materialized: `st` on customers, `rs`/`deleted_at` on buckets):
  customers  c1 st2 b.1970 accts[1,2] · c2 st1 b.1985 [3] · c3 st4 b.1990 [2,4] · c4 st7 b.1960 [5]
  accounts   1: 10000 {Brokerage,Commodity} · 2: 5000 {Derivatives} · 3: 9000 {Brokerage}
             4: 3000 {Commodity} · 5: 10000 {InvestmentStock}
  buckets    b1 acct1 rs1 start 2010-01-02: sell msft 100 "1000.0" 2010-01-05; buy msft 50 "500.0" 2010-02-01;
                                            sell aapl 10 "200.5" 2011-03-01
             b2 acct2 rs3 (removed) start 2010-06-01: buy msft 30 "300.0" 2010-06-01
             b3 acct3 rs2 deleted_at set (decoy; counts) start 2011-01-01: buy aapl 20 "400.0" 2011-05-01
             b4 acct4 rs1 start 2010-03-01: sell msft 5 "99.5" 2010-03-03
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from munchhausen.config import Settings
from munchhausen.truth.gold import PackGold
from munchhausen.world.pack import load_pack
from munchhausen.world.questions import bank_from_pack
from munchhausen.world.synthetic import MemoryDB
from munchhausen.world.transforms import GOLD, round_to

D = datetime


def _t(date: datetime, amount: int, code: str, symbol: str, total: str) -> dict[str, Any]:
    return {"date": date, "amount": amount, "transaction_code": code, "symbol": symbol,
            "price": str(float(total) / amount), "total": total}


def _bucket(i: int, acct: int, rs: int, deleted: datetime | None, start: datetime, trades: list) -> dict:
    return {"_id": f"b{i}", "account_id": acct, "rs": rs, "deleted_at": deleted, "bucket_start_date": start,
            "bucket_end_date": trades[-1]["date"], "transaction_count": len(trades), "transactions": trades}


FIXTURE: dict[str, list[dict[str, Any]]] = {
    "customers": [
        {"_id": "c1", "username": "u1", "birthdate": D(1970, 5, 1), "accounts": [1, 2], "st": 2},
        {"_id": "c2", "username": "u2", "birthdate": D(1985, 1, 1), "accounts": [3], "st": 1},
        {"_id": "c3", "username": "u3", "birthdate": D(1990, 7, 1), "accounts": [2, 4], "st": 4},
        {"_id": "c4", "username": "u4", "birthdate": D(1960, 1, 1), "accounts": [5], "st": 7},
    ],
    "accounts": [
        {"_id": "a1", "account_id": 1, "limit": 10000, "products": ["Brokerage", "Commodity"]},
        {"_id": "a2", "account_id": 2, "limit": 5000, "products": ["Derivatives"]},
        {"_id": "a3", "account_id": 3, "limit": 9000, "products": ["Brokerage"]},
        {"_id": "a4", "account_id": 4, "limit": 3000, "products": ["Commodity"]},
        {"_id": "a5", "account_id": 5, "limit": 10000, "products": ["InvestmentStock"]},
    ],
    "transactions": [
        _bucket(1, 1, 1, None, D(2010, 1, 2), [_t(D(2010, 1, 5), 100, "sell", "msft", "1000.0"),
                                                 _t(D(2010, 2, 1), 50, "buy", "msft", "500.0"),
                                                 _t(D(2011, 3, 1), 10, "sell", "aapl", "200.5")]),
        _bucket(2, 2, 3, None, D(2010, 6, 1), [_t(D(2010, 6, 1), 30, "buy", "msft", "300.0")]),
        _bucket(3, 3, 2, D(2012, 1, 1), D(2011, 1, 1), [_t(D(2011, 5, 1), 20, "buy", "aapl", "400.0")]),
        _bucket(4, 4, 1, None, D(2010, 3, 1), [_t(D(2010, 3, 3), 5, "sell", "msft", "99.5")]),
    ],
}

PACK = load_pack(Settings(_env_file=None).pack_path())
BANK = bank_from_pack(PACK, 0.65)
GOLDS = PackGold(PACK, BANK, MemoryDB(FIXTURE), None, 3000)
V0, V1 = "v0", "v0+D1"

CASES = [  # (template, persona, params, gold at v0, gold at v0+D1)
    # controls
    ("customers_born_before", "priya", {"born_before": 1980}, 2, 2),
    ("accounts_with_product", "priya", {"product": "Brokerage"}, 2, 2),
    ("accounts_limit_at_least", "marco", {"limit_at_least": 9000}, 3, 3),
    ("avg_limit_product", "priya", {"product": "Commodity"}, 6500.0, 6500.0),
    ("sell_trades_year", "priya", {"year": 2010}, 2, 2),
    ("shares_sold_symbol_year", "priya", {"symbol": "msft", "year": 2010}, 105, 105),
    # P1: Dana on controls, rounded to the nearest thousand
    ("avg_limit_product", "dana", {"product": "Commodity"}, 7000, 7000),
    ("accounts_limit_at_least", "dana", {"limit_at_least": 9000}, 0, 0),
    # Q1: active ⇔ st ∈ {2, 7}; D1 adds 4
    ("active_born_from", "priya", {"born_from": 1965}, 1, 2),
    ("active_with_product", "priya", {"product": "Commodity"}, 1, 2),
    ("active_with_product", "priya", {"product": "Brokerage"}, 1, 1),
    ("active_avg_accounts", "priya", {"born_before": 2000}, 1.5, 5 / 3),
    ("active_limit_total", "priya", {"product": "Commodity"}, 15000, 18000),
    # Q3: rs == 3 excluded; deleted_at is a decoy and those batches count
    ("buy_trades_year", "priya", {"year": 2010}, 1, 1),
    ("trades_symbol_year", "priya", {"symbol": "msft", "year": 2010}, 3, 3),
    ("shares_bought_symbol", "priya", {"symbol": "aapl"}, 20, 20),
    ("batches_with_symbol", "priya", {"symbol": "msft"}, 2, 2),
    ("batches_with_symbol", "priya", {"symbol": "aapl"}, 2, 2),
    # Q5: Σ total of sells × 0.995 (totals stored as strings)
    ("revenue_year", "priya", {"year": 2010}, 1099.5 * 0.995, 1099.5 * 0.995),
    ("revenue_symbol", "priya", {"symbol": "aapl"}, 200.5 * 0.995, 200.5 * 0.995),
    ("revenue_symbol_year", "priya", {"symbol": "msft", "year": 2010}, 1099.5 * 0.995, 1099.5 * 0.995),
    ("revenue_month", "priya", {"month": 1, "year": 2010}, 995.0, 995.0),
]


@pytest.mark.parametrize(("template", "persona", "params", "v0", "v1"), CASES,
                         ids=[f"{c[0]}-{c[1]}-{i}" for i, c in enumerate(CASES)])
async def test_gold_on_hand_fixture(template: str, persona: str, params: dict, v0: Any, v1: Any) -> None:
    q = BANK.pose(template, persona, params)
    assert await GOLDS.gold(q, V0) == pytest.approx(v0)
    assert await GOLDS.gold(q, V1) == pytest.approx(v1)


def test_every_template_has_a_hand_case() -> None:
    assert {t.id for t in PACK.templates} <= {c[0] for c in CASES}


def test_round_to_half_away_from_zero() -> None:
    present = round_to({"unit": 1000})["present"]
    assert [present(x) for x in (1499, 1500, 6500, 91234.5, -1500, 0)] == [1000, 2000, 7000, 91000, -2000, 0]
    assert present([1, 2]) == [1, 2]


def test_quirk_transforms_are_registered() -> None:
    for q in PACK.quirks:
        if q.gold is not None:
            assert q.gold.transform in GOLD, q.id


async def test_poison_variants_differ_from_gold() -> None:
    q1 = BANK.pose("active_born_from", "priya", {"born_from": 1960})
    assert await GOLDS.variant(q1, V0, "Q1_active_customer", {"values": [1, 2, 7]}) == 3
    q5 = BANK.pose("revenue_year", "priya", {"year": 2010})
    assert await GOLDS.variant(q5, V0, "Q5_revenue", {"factor": 1.0}) == pytest.approx(1099.5)
    q3 = BANK.pose("buy_trades_year", "priya", {"year": 2010})
    assert await GOLDS.variant(q3, V0, "Q3_soft_delete", {"value": None}) == 2
