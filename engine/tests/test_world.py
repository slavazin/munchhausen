"""World: pack coverage, the question stream, the authority, the adapter, PackWorld, and the schema summary
as the vocabulary's seed source (SPEC § 4, § 22.4)."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

import pytest

from munchhausen.config import Settings
from munchhausen.domain.common import AuthorityLevel
from munchhausen.ports.world import World
from munchhausen.truth.gold import PackGold
from munchhausen.world.adapters.sample_analytics import materialize_pack
from munchhausen.world.authority import Authority
from munchhausen.world.pack import load_pack
from munchhausen.world.pack_world import PackWorld
from munchhausen.world.questions import bank_from_pack
from munchhausen.world.synthetic import MemoryDB, synthetic_source

S = Settings(_env_file=None)
PACK = load_pack(S.pack_path())
SYMBOLS = ["amzn", "msft", "aapl", "goog", "nvda", "intc", "csco", "ibm", "adbe", "crm", "ebay", "nflx",
           "sap", "amd", "team", "znga"]
PRODUCTS = ["Derivatives", "InvestmentStock", "CurrencyService", "Commodity", "Brokerage", "InvestmentFund"]


def _source() -> dict[str, list[dict[str, Any]]]:
    return synthetic_source(5, customers=60, products=PRODUCTS, symbols=SYMBOLS, years=(2004, 2016),
                            birth_years=(1960, 1999), limits=[3000, 5000, 9000, 10000], max_trades=30)


class FakeStore:
    def __init__(self) -> None:
        self.src, self.wdb = MemoryDB(_source()), MemoryDB()

    def source(self) -> MemoryDB:
        return self.src

    def world(self) -> MemoryDB:
        return self.wdb

    def world_writer(self) -> MemoryDB:
        return self.wdb


# --- pack ---------------------------------------------------------------------------------------------


def test_pack_coverage_and_minimum_set() -> None:
    assert PACK.validate_coverage() == []
    kinds = {q.id: q.kind for q in PACK.quirks}
    assert {"Q1_active_customer", "Q3_soft_delete", "Q5_revenue", "P1_dana_rounding", "N1_stale_report"} <= set(kinds)
    assert len([t for t in PACK.templates if not any(t.id in q.templates and q.persona is None
                                                     for q in PACK.quirks)]) >= 4    # controls for the pilot
    assert PACK.drift_schedule["D1"]["quirk"] == "Q1_active_customer"


def test_q1_has_four_templates_with_distinct_wording_and_collections() -> None:
    """The story needs Q1 learned on some templates and applied on one absent from its sources."""
    q1 = PACK.quirk("Q1_active_customer")
    specs = [t for t in PACK.templates if t.id in q1.templates]
    assert len(specs) >= 4
    assert len({t.text.split("{")[0] for t in specs}) == len(specs)
    assert len({t.collections for t in specs}) >= 2
    assert all("active customer" in t.text for t in specs)          # every one presents the concept


def test_phrasings_name_the_concept_not_the_definition() -> None:
    for q in PACK.quirks:
        for p in q.authority_phrasings:
            assert not re.search(r"\bst\b|\brs\b|0\.995|\b[0-9]+\b", p), (q.id, p)


def test_pack_hash_is_stable() -> None:
    assert PACK.content_hash() == load_pack(S.pack_path()).content_hash()
    assert len(PACK.content_hash()) == 64


# --- questions ----------------------------------------------------------------------------------------


BANK = bank_from_pack(PACK, S.quirk_share, sealed=(S.v_seed, S.v_size))


def test_stream_is_deterministic_and_ids_stable() -> None:
    a = [BANK.question_at(S.stream_seed, i) for i in range(50)]
    fresh = bank_from_pack(PACK, S.quirk_share, sealed=(S.v_seed, S.v_size))
    it = fresh.stream(S.stream_seed)
    b = [next(it) for _ in range(50)]
    assert a == b
    assert len({q.id for q in a}) == 50
    other = bank_from_pack(PACK, S.quirk_share, sealed=(S.v_seed, S.v_size))
    assert other.hidden(a[17].id) == BANK.hidden(a[17].id)            # regenerated, not remembered


def test_stream_mix_honours_quirk_share() -> None:
    qs = [BANK.question_at(S.stream_seed, i) for i in range(2000)]
    share = sum(bool(BANK.hidden(q.id).quirks) for q in qs) / len(qs)
    assert abs(share - S.quirk_share) < 0.04
    per_quirk = Counter(BANK.hidden(q.id).quirks[0] for q in qs if BANK.hidden(q.id).quirks)
    assert set(per_quirk) == {"Q1_active_customer", "Q3_soft_delete", "Q5_revenue", "Q6_tech_names",
                              "P1_dana_rounding"}
    assert per_quirk["Q1_active_customer"] > 1.5 * per_quirk["Q5_revenue"]          # pack weight 2


def test_one_quirk_per_question_and_dana_on_controls_only() -> None:
    p1 = PACK.quirk("P1_dana_rounding")
    for i in range(1000):
        q = BANK.question_at(S.stream_seed, i)
        h = BANK.hidden(q.id)
        assert len(h.quirks) <= 1
        if q.persona == "dana":
            assert h.quirks == ("P1_dana_rounding",) and q.template in p1.templates
            assert not BANK.template(q.template).quirks
        elif h.quirks:
            assert BANK.template(q.template).quirks == h.quirks


def test_v_set_is_sealed_from_the_stream() -> None:
    v = BANK.v_set(S.v_seed, S.v_size)
    assert len(v) == S.v_size and all(q.id.startswith("v") for q in v)
    key = lambda q: (q.template, q.persona, tuple(sorted(BANK.hidden(q.id).params.items())))  # noqa: E731
    v_keys = {key(q) for q in v}
    assert not v_keys & {key(BANK.question_at(S.stream_seed, i)) for i in range(3000)}


def test_instances_by_template() -> None:
    qs = BANK.instances("active_limit_total", seed=1, n=5)
    assert len(qs) == 5 and {q.template for q in qs} == {"active_limit_total"}
    assert all(BANK.hidden(q.id).quirks == ("Q1_active_customer",) for q in qs)
    other = bank_from_pack(PACK, S.quirk_share)
    assert other.hidden(qs[3].id) == BANK.hidden(qs[3].id)


def test_question_text_carries_no_hidden_tag() -> None:
    for i in range(300):
        q = BANK.question_at(S.stream_seed, i)
        assert not any(qid.lower() in q.text.lower() for qid in (x.id for x in PACK.quirks))


# --- authority ----------------------------------------------------------------------------------------


@pytest.fixture
def world_data() -> dict[str, list[dict[str, Any]]]:
    return materialize_pack(_source(), PACK, S.world_seed)


def _authority(data: dict, level: AuthorityLevel = AuthorityLevel.TERM, rate: float = 0.05) -> Authority:
    gold = PackGold(PACK, BANK, MemoryDB(data), None, S.execute_max_time_ms)
    return Authority(gold, PACK, BANK, level, rate, S.score_rel_tol, S.score_abs_tol_rounded, S.world_seed)


async def test_authority_phrasing_per_level(world_data: dict) -> None:
    q = BANK.pose("revenue_year", "priya", {"year": 2010})
    ctl = BANK.pose("sell_trades_year", "priya", {"year": 2010})
    term = await _authority(world_data, rate=0.0).judge(q, -1.0, "v0", 3, with_authority=True)
    assert not term.correct and term.phrasing in PACK.quirk("Q5_revenue").authority_phrasings
    terse = await _authority(world_data, AuthorityLevel.TERSE, 0.0).judge(q, -1.0, "v0", 3, with_authority=True)
    assert terse.phrasing is None and terse.figure == term.figure
    rule = await _authority(world_data, AuthorityLevel.RULE, 0.0).judge(q, -1.0, "v0", 3, with_authority=True)
    assert PACK.quirk("Q5_revenue").definition in (rule.phrasing or "")
    c = await _authority(world_data, rate=0.0).judge(ctl, -1.0, "v0", 3, with_authority=True)
    assert c.phrasing is None and c.figure is not None
    hidden = await _authority(world_data, rate=0.0).judge(q, -1.0, "v0", 3, with_authority=False)
    assert hidden.figure is None and hidden.phrasing is None


async def test_authority_scores_gold_and_dana_tolerance(world_data: dict) -> None:
    a = _authority(world_data, rate=0.0)
    q = BANK.pose("avg_limit_product", "dana", {"product": "Commodity"})
    g = await a._truth.gold(q, "v0")
    assert g % 1000 == 0
    assert (await a.judge(q, g + 0.4, "v0", 0, with_authority=False)).correct
    assert not (await a.judge(q, g + 1.0, "v0", 0, with_authority=False)).correct
    plain = BANK.pose("avg_limit_product", "priya", {"product": "Commodity"})
    exact = await a._truth.gold(plain, "v0")
    assert (await a.judge(plain, exact, "v0", 0, with_authority=False)).correct
    assert a._abs_tol_for(plain) == 0.0 and a._abs_tol_for(q) == S.score_abs_tol_rounded


async def test_poison_is_deterministic_per_seed_and_index(world_data: dict) -> None:
    q = BANK.pose("revenue_year", "priya", {"year": 2010})
    a, b = _authority(world_data, rate=0.3), _authority(world_data, rate=0.3)
    gold = await a._truth.gold(q, "v0")
    poisoned = []
    for idx in range(60):
        ja = await a.judge(q, -1.0, "v0", idx, with_authority=True)
        jb = await b.judge(q, -1.0, "v0", idx, with_authority=True)
        assert ja == jb
        if ja.figure != gold:
            poisoned.append(idx)
            assert ja.figure == pytest.approx(gold / 0.995)            # revenue without the fee
            assert ja.phrasing in PACK.quirk("Q5_revenue").authority_phrasings   # labelled like genuine
    assert 5 <= len(poisoned) <= 35
    none = _authority(world_data, rate=0.0)
    for i in range(60):
        assert (await none.judge(q, -1.0, "v0", i, with_authority=True)).figure == gold


async def test_d1_drift_is_gold_only(world_data: dict) -> None:
    a = _authority(world_data, rate=0.0)
    q = BANK.pose("active_born_from", "priya", {"born_from": 1960})
    v0, v1 = await a._truth.gold(q, "v0"), await a._truth.gold(q, "v0+D1")
    st = Counter(c["st"] for c in world_data["customers"])
    assert (v0, v1) == (st[2] + st[7], st[2] + st[4] + st[7])


# --- PackWorld + adapter ------------------------------------------------------------------------------


async def test_pack_world_builds_and_judges() -> None:
    store = FakeStore()
    w = PackWorld.create("pack", S, store)  # type: ignore[arg-type]
    assert isinstance(w, World)
    counts = await w.build(S.world_seed)
    assert counts == {c: len(store.src.data[c]) for c in ("customers", "accounts", "transactions")}
    assert await w.counts() == counts
    snapshot = {c: list(d) for c, d in store.wdb.data.items()}
    await w.build(S.world_seed)
    assert store.wdb.data == snapshot                                   # deterministic rebuild
    assert w.world_version(S.d1_at - 1) == "v0" and w.world_version(S.d1_at) == "v0+D1"
    q = next(w.questions(S.stream_seed))
    gold = await w.truth.gold(q, "v0")
    assert (await w.judge(q, gold, 0, with_authority=True)).correct
    assert len(w.v_set()) == S.v_size
    inv = w.inventory()
    assert inv["pack_hash"] == w.pack_hash and inv["drift_at"] == {"D1": S.d1_at}
    assert "definition" not in str(inv) and "0.995" not in str(inv)
    assert w.instances("revenue_symbol", 0, 2)[0].template == "revenue_symbol"


async def test_schema_summary_is_names_and_types_only() -> None:
    """The vocabulary's seed source (SPEC § 22.4): no pack id, template id, definition, phrasing, prior trap
    or definitional transform parameter appears in the schema summary. Field-name params (`st`, `rs`) must."""
    store = FakeStore()
    w = PackWorld.create("pack", S, store)  # type: ignore[arg-type]
    await w.build(S.world_seed)
    summary = w.schema_summary()
    tokens = set(summary.collections)
    for fields in summary.collections.values():
        for path, typ in fields.items():
            tokens |= set(path.lower().split(".")) | {typ.lower()}
    assert {"st", "rs", "deleted_at"} <= tokens
    field_keys = {"field", "kind_field", "amount_field", "collection", "key", "items", "decoy_field",
                  "decoy_from", "count_field"}
    forbidden: set[str] = {PACK.id.lower(), *(q.id.lower() for q in PACK.quirks),
                           *(t.id.lower() for t in PACK.templates)}
    text = " ".join(sorted(tokens))
    for q in PACK.quirks:
        for sentence in (q.definition, q.prior_trap, *q.authority_phrasings):
            assert not sentence or sentence.lower() not in text, sentence
        for ref in (q.materialize, q.gold):
            for k, v in (ref.params.items() if ref else ()):
                if k in field_keys:
                    continue
                forbidden |= {str(x).lower() for x in (v if isinstance(v, list) else [v])}
        for d in q.drift:
            forbidden |= {str(x).lower() for v in d.gold_params.values() for x in (v if isinstance(v, list) else [v])}
    for p in PACK.poison_bank:
        forbidden |= {str(x).lower() for v in p.params.values() for x in (v if isinstance(v, list) else [v])}
    leaked = forbidden & tokens
    assert not leaked, leaked


async def test_schema_notes_are_storage_facts_never_quirk_fields_or_definitions() -> None:
    """Schema-summary notes (pilot gate): listed values only for allowlisted non-quirk fields, and never a
    value a quirk's params, drift or the poison bank carry unless the question texts themselves state it
    (`buy`/`sell` in "How many sell trades…"); no note on any field a quirk writes or defines; no definition,
    prior trap or phrasing in any note."""
    store = FakeStore()
    w = PackWorld.create("pack", S, store)  # type: ignore[arg-type]
    await w.build(S.world_seed)
    notes = w.schema_summary().notes
    assert notes["transactions"]["transactions.transaction_code"] == "values: buy, sell"
    assert notes["transactions"]["transactions.price"] == "numbers stored as text"
    # Fields a quirk writes carry no note at all; fields a quirk's gold reads (e.g. Q6's `symbol`) may carry a
    # storage note such as `lowercase`, never listed values.
    written = {str(v) for q in PACK.quirks if q.materialize
               for k, v in q.materialize.params.items() if k in {"field", "decoy_field"}}
    read = {str(v) for q in PACK.quirks if q.gold for k, v in q.gold.params.items() if k == "field"}
    assert {"st", "rs", "deleted_at"} <= written and "symbol" in read
    noted = {path.rsplit(".", 1)[-1] for fields in notes.values() for path in fields}
    assert not written & noted, written & noted
    valued = {path.rsplit(".", 1)[-1] for fields in notes.values() for path, n in fields.items()
              if n.startswith("values: ")}
    assert not (written | read) & valued, (written | read) & valued
    assert not {f.rsplit(".", 1)[-1] for f in S.schema_value_fields} & (written | read)
    text = " ".join(n for fields in notes.values() for n in fields.values()).lower()
    for q in PACK.quirks:
        for sentence in (q.definition, q.prior_trap, *q.authority_phrasings):
            assert not sentence or sentence.lower() not in text, sentence
    values = {v.strip().lower() for fields in notes.values() for n in fields.values() if n.startswith("values: ")
              for v in n.removeprefix("values: ").split(",")}
    carried: set[str] = set()
    for q in PACK.quirks:
        for ref in (q.materialize, q.gold):
            carried |= {str(x).lower() for v in (ref.params.values() if ref else ())
                        for x in (v if isinstance(v, list) else [v])}
        carried |= {str(x).lower() for d in q.drift for v in d.gold_params.values()
                    for x in (v if isinstance(v, list) else [v])}
    for p in PACK.poison_bank:
        carried |= {str(x).lower() for v in p.params.values() for x in (v if isinstance(v, list) else [v])}
    stated = set(re.findall(r"[a-z0-9_]+", " ".join(t.text.lower() for t in PACK.templates)))
    assert not (values & carried) - stated, (values & carried) - stated
