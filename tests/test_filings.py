"""Filings ingestion: provider, DuckDB store, and LakehouseFilingsReader."""

from __future__ import annotations

from datetime import date

from vyapaar_data import Filing, FilingType, LakehouseFilingsReader
from vyapaar_data.providers.filings import FilingRow, parse_filings, rows_to_filings


def test_filings_store_upsert_and_query(filings_store, sample_filings):
    for filing in sample_filings:
        filings_store.upsert(filing)

    rows = filings_store.query(instrument="NSE:RELIANCE-EQ")
    assert len(rows) == 2
    assert all(f.instrument == "NSE:RELIANCE-EQ" for f in rows)
    assert rows[0].filing_date == date(2024, 1, 20)
    assert rows[1].filing_date == date(2024, 2, 10)


def test_filings_store_query_by_type(filings_store, sample_filings):
    for filing in sample_filings:
        filings_store.upsert(filing)

    rows = filings_store.query(filing_type=FilingType.QUARTERLY_RESULT)
    assert len(rows) == 2  # RELIANCE + TCS quarterly results


def test_filings_store_date_window(filings_store, sample_filings):
    for filing in sample_filings:
        filings_store.upsert(filing)

    rows = filings_store.query(
        instrument="NSE:RELIANCE-EQ",
        start_date=date(2024, 2, 1),
        end_date=date(2024, 2, 28),
    )
    assert len(rows) == 1
    assert rows[0].title == "Shareholding Pattern Dec 2023"


def test_filings_store_unknown_instrument_returns_empty(filings_store):
    assert filings_store.query(instrument="NSE:NOPE-EQ") == []


def test_filings_store_upsert_is_idempotent(filings_store):
    filing = Filing(
        "NSE:RELIANCE-EQ",
        date(2024, 1, 20),
        FilingType.QUARTERLY_RESULT,
        "Q3 FY24 Results",
        "https://example.com/reliance-q3",
    )
    filings_store.upsert(filing)
    # Same key (instrument+filing_date+title), updated source_url -> replaces.
    filings_store.upsert(
        Filing(
            "NSE:RELIANCE-EQ",
            date(2024, 1, 20),
            FilingType.QUARTERLY_RESULT,
            "Q3 FY24 Results",
            "https://example.com/reliance-q3-rev",
        )
    )
    rows = filings_store.query(instrument="NSE:RELIANCE-EQ")
    assert len(rows) == 1
    assert rows[0].title == "Q3 FY24 Results"
    assert rows[0].source_url == "https://example.com/reliance-q3-rev"


def test_lakehouse_filings_reader_list_filings(filings_store, sample_filings):
    for filing in sample_filings:
        filings_store.upsert(filing)
    reader = LakehouseFilingsReader(filings_store)

    rows = reader.list_filings(instrument="NSE:TCS-EQ")
    assert len(rows) == 1
    assert rows[0].instrument == "NSE:TCS-EQ"
    assert rows[0].filing_type == FilingType.QUARTERLY_RESULT


def test_lakehouse_filings_reader_point_in_time(filings_store, sample_filings):
    for filing in sample_filings:
        filings_store.upsert(filing)
    reader = LakehouseFilingsReader(filings_store)

    # A filing on 2024-01-15 must not appear when querying end_date=2024-01-14.
    rows = reader.list_filings(instrument="NSE:TCS-EQ", end_date=date(2024, 1, 14))
    assert rows == []

    rows = reader.list_filings(instrument="NSE:TCS-EQ", end_date=date(2024, 1, 15))
    assert len(rows) == 1


def test_parse_filings_csv():
    text = (
        "instrument,filing_date,filing_type,title,source_url\n"
        "NSE:RELIANCE-EQ,20-Jan-2024,quarterly_result,Q3 FY24 Results,https://example.com/r\n"
    )
    rows = parse_filings(text)
    assert len(rows) == 1
    assert rows[0].instrument == "NSE:RELIANCE-EQ"
    assert rows[0].filing_date == date(2024, 1, 20)
    assert rows[0].filing_type == "quarterly_result"
    assert rows[0].title == "Q3 FY24 Results"
    assert rows[0].source_url == "https://example.com/r"


def test_rows_to_filings_round_trip():
    rows = [
        FilingRow(
            "NSE:RELIANCE-EQ",
            date(2024, 1, 20),
            "quarterly_result",
            "Q3 FY24 Results",
            "https://example.com/r",
        )
    ]
    filings = rows_to_filings(rows)
    assert len(filings) == 1
    assert filings[0].filing_type == FilingType.QUARTERLY_RESULT


def test_unknown_filing_type_defaults_to_other(filings_store):
    filing = Filing(
        "NSE:RELIANCE-EQ",
        date(2024, 1, 20),
        FilingType.OTHER,
        "Some other disclosure",
        None,
    )
    filings_store.upsert(filing)
    rows = filings_store.query(instrument="NSE:RELIANCE-EQ")
    assert len(rows) == 1
    assert rows[0].filing_type == FilingType.OTHER
