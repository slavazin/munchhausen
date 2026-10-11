"""Offline stand-ins for the world side: a `sample_analytics`-shaped source generator and an in-memory
DocumentReader/WorldWriter. Tests and dry runs use them; nothing on a live run does.

The generator mirrors the source's shapes (customers{username,name,email,birthdate,accounts[],
tier_and_details}, accounts{account_id,limit,products[]}, transactions{account_id,transaction_count,
bucket_start_date,bucket_end_date,transactions[{date,amount,transaction_code,symbol,price,total}]}),
with `price` and `total` stored as strings, as the source stores them.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

Doc = dict[str, Any]


def synthetic_source(seed: int, *, customers: int, products: Sequence[str], symbols: Sequence[str],
                     years: tuple[int, int], birth_years: tuple[int, int], limits: Sequence[int],
                     max_trades: int) -> dict[str, list[Doc]]:
    rng = random.Random(f"synthetic:{seed}")
    out: dict[str, list[Doc]] = {"customers": [], "accounts": [], "transactions": []}
    next_account = 100_000
    for i in range(customers):
        ids = []
        for _ in range(rng.randint(1, 4)):
            next_account += rng.randint(1, 50)
            aid = next_account
            ids.append(aid)
            out["accounts"].append({"_id": f"a{aid:08d}", "account_id": aid, "limit": rng.choice(list(limits)),
                                    "products": rng.sample(list(products), rng.randint(1, 3))})
            start = datetime(rng.randint(*years), rng.randint(1, 12), rng.randint(1, 28))
            trades = []
            for _ in range(rng.randint(1, max_trades)):
                date = start + timedelta(days=rng.randint(0, 3 * 365))
                amount = rng.randint(1, 9999)
                price = rng.uniform(5, 500)
                trades.append({"date": date, "amount": amount, "transaction_code": rng.choice(["buy", "sell"]),
                               "symbol": rng.choice(list(symbols)), "price": repr(price),
                               "total": repr(amount * price)})
            trades.sort(key=lambda t: t["date"])
            out["transactions"].append({"_id": f"t{aid:08d}", "account_id": aid, "transaction_count": len(trades),
                                        "bucket_start_date": trades[0]["date"], "bucket_end_date": trades[-1]["date"],
                                        "transactions": trades})
        tier = f"{rng.getrandbits(128):032x}"
        out["customers"].append({
            "_id": f"c{i:06d}", "username": f"user{i}", "name": f"Customer {i}", "email": f"user{i}@example.com",
            "birthdate": datetime(rng.randint(*birth_years), rng.randint(1, 12), rng.randint(1, 28)),
            "accounts": ids,
            "tier_and_details": {tier: {"tier": rng.choice(["Bronze", "Silver", "Gold", "Platinum"]),
                                        "id": tier, "active": True, "benefits": []}},
        })
    return out


class MemoryDB:
    """In-memory DocumentReader + WorldWriter. `aggregate` supports only `[{$count: <field>}]`."""

    def __init__(self, data: dict[str, list[Doc]] | None = None) -> None:
        self.data: dict[str, list[Doc]] = {k: list(v) for k, v in (data or {}).items()}

    async def find(self, collection: str, filter: Doc | None = None, projection: Doc | None = None,
                   limit: int = 0) -> list[Doc]:
        docs = [d for d in self.data.get(collection, []) if all(d.get(k) == v for k, v in (filter or {}).items())]
        return docs[:limit] if limit else docs

    async def aggregate(self, collection: str, pipeline: list[Doc], *, max_time_ms: int) -> list[Doc]:
        if len(pipeline) == 1 and "$count" in pipeline[0]:
            n = len(self.data.get(collection, []))
            return [{pipeline[0]["$count"]: n}] if n else []
        raise NotImplementedError("MemoryDB supports only a lone $count stage")

    async def collection_names(self) -> list[str]:
        return sorted(self.data)

    async def replace_collection(self, collection: str, docs: Sequence[Doc]) -> int:
        self.data[collection] = list(docs)
        return len(docs)

    async def create_view(self, name: str, source: str, pipeline: list[Doc]) -> None:
        raise NotImplementedError("MemoryDB has no views")

    async def drop_view(self, name: str) -> None:
        self.data.pop(name, None)
