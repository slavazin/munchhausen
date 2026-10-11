"""Pipeline text → stages (domain/pipeline_json.py; pilot gate): Extended JSON dates decode to dates, and a
non-JSON pipeline is repaired leniently, with the repairs recorded by name."""

from __future__ import annotations

from datetime import UTC, datetime

from munchhausen.domain.pipeline_json import parse_pipeline
from munchhausen.impl.parties import proposer as proposer_party

D2010 = datetime(2010, 1, 1, tzinfo=UTC)


def test_extended_json_dates_decode_to_dates_without_a_repair() -> None:
    stages, repairs = parse_pipeline('[{"$match": {"d": {"$gte": {"$date": "2010-01-01T00:00:00Z"}, '
                                     '"$lt": {"$date": {"$numberLong": "1262304000000"}}}}}]')
    assert stages == [{"$match": {"d": {"$gte": D2010, "$lt": D2010}}}] and repairs == ()
    assert parse_pipeline('[{"$match": {"d": {"$date": "2010-01-01"}}}]')[0] == [{"$match": {"d": D2010}}]


def test_shell_constructors_and_trailing_commas_are_repaired_and_recorded() -> None:
    stages, repairs = parse_pipeline('[{"$match": {"d": {"$lt": new Date("2010-01-01"), '
                                     '"e": ISODate("2010-01-01T00:00:00Z"), "n": NumberInt(3),}}},]')
    assert stages == [{"$match": {"d": {"$lt": D2010, "e": D2010, "n": 3}}}]
    assert repairs == ("js_date", "js_number", "trailing_comma")


def test_text_that_is_not_a_pipeline_stays_unparsed() -> None:
    assert parse_pipeline("not json") == (None, ())
    assert parse_pipeline("[1, 2]") == (None, ())
    assert parse_pipeline('{"$count": "n"}') == ([{"$count": "n"}], ())


def test_the_proposal_records_repairs() -> None:
    wire = proposer_party.ProposalWire(collection="c", pipeline_json='[{"$match": {"d": ISODate("2010-01-01")}}]',
                                       answer_path="0.n", terms_used=[], consulted=[], anomalies=[],
                                       confidence=0.5, rationale="")
    p = wire.to_domain([])
    assert p.pipeline == [{"$match": {"d": D2010}}] and p.repairs == ("js_date",)
