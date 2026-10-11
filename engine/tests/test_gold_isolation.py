"""Gold isolation (SPEC § 4.2): for every template, applying any other quirk's gold transform leaves its gold
unchanged, at every world version, on a materialized synthetic world shaped like `sample_analytics`.
`munchhausen build-world` runs the same check over the live `world`."""

from __future__ import annotations

from collections import Counter

from munchhausen.config import Settings
from munchhausen.truth.gold import PackGold
from munchhausen.world.adapters.sample_analytics import materialize_pack
from munchhausen.world.checks import isolation_violations, quirk_effects
from munchhausen.world.pack import load_pack
from munchhausen.world.questions import bank_from_pack
from munchhausen.world.synthetic import MemoryDB, synthetic_source

S = Settings(_env_file=None)
PACK = load_pack(S.pack_path())
BANK = bank_from_pack(PACK, S.quirk_share)
SYMBOLS = ["amzn", "msft", "aapl", "goog", "nvda", "intc", "csco", "ibm", "adbe", "crm", "ebay", "nflx",
           "sap", "amd", "team", "znga"]
PRODUCTS = ["Derivatives", "InvestmentStock", "CurrencyService", "Commodity", "Brokerage", "InvestmentFund"]
SOURCE = synthetic_source(3, customers=80, products=PRODUCTS, symbols=SYMBOLS, years=(2004, 2016),
                          birth_years=(1960, 1999), limits=[3000, 5000, 8000, 9000, 10000, 10000], max_trades=40)
WORLD = materialize_pack(SOURCE, PACK, S.world_seed)
GOLD = PackGold(PACK, BANK, MemoryDB(WORLD), None, S.execute_max_time_ms)


def test_gold_isolation_every_template_every_version() -> None:
    assert isolation_violations(GOLD, BANK, PACK, WORLD, limit=8) == []


def test_isolation_check_catches_a_misplaced_population() -> None:
    """Sanity of the check itself: if removed batches also held sells, revenue would read Q3's floor."""
    leaky = {**WORLD, "transactions": [{**b, "transactions": SOURCE["transactions"][i]["transactions"]}
                                       for i, b in enumerate(WORLD["transactions"])]}
    gold = PackGold(PACK, BANK, MemoryDB(leaky), None, S.execute_max_time_ms)
    bad = isolation_violations(gold, BANK, PACK, leaky, limit=8)
    assert any(v.startswith("revenue") and "Q3_soft_delete" in v for v in bad)


def test_each_quirk_template_is_not_vacuous() -> None:
    """Most combinations of each quirk template have a gold the poison (conventional) variant misses."""
    effects = quirk_effects(GOLD, BANK, PACK, WORLD, limit=8)
    assert set(effects) >= {t for q in PACK.quirks if q.persona is None and q.gold for t in q.templates}
    weak = {t: share for t, share in effects.items() if share < 0.5}
    assert not weak, weak


def test_materialize_shares_and_placement() -> None:
    n = len(WORLD["customers"])
    st = Counter(c["st"] for c in WORLD["customers"])
    assert set(st) <= {1, 2, 4, 7} and abs(st[1] / n - 0.5) < 0.15
    buckets = WORLD["transactions"]
    assert all("rs" in b and "deleted_at" in b for b in buckets)
    removed = [b for b in buckets if b["rs"] == 3]
    decoy = [b for b in buckets if b["deleted_at"] is not None]
    assert removed and decoy and not any(b["rs"] == 3 for b in decoy)
    for b in removed + decoy:
        assert all(t["transaction_code"] == "buy" for t in b["transactions"])
        assert b["transaction_count"] == len(b["transactions"])
    assert materialize_pack(SOURCE, PACK, S.world_seed) == WORLD                     # deterministic
    assert materialize_pack(SOURCE, PACK, S.world_seed + 1) != WORLD                 # and seed-dependent
