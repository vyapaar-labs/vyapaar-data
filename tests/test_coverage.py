"""Coverage ledger gap discovery."""

from __future__ import annotations

from datetime import date

from vyapaar_data.domain.coverage import CoverageEntry, CoverageLedger


def test_gaps_reports_uncovered_ranges() -> None:
    ledger = CoverageLedger(
        (
            CoverageEntry(
                "NSE:RELIANCE-EQ", "1d", date(2024, 1, 2), date(2024, 1, 10), row_count=7
            ),
            CoverageEntry(
                "NSE:RELIANCE-EQ", "1d", date(2024, 1, 15), date(2024, 1, 17), row_count=3
            ),
        )
    )
    assert ledger.gaps("NSE:RELIANCE-EQ", "1d", date(2024, 1, 1), date(2024, 1, 20)) == [
        (date(2024, 1, 1), date(2024, 1, 1)),
        (date(2024, 1, 11), date(2024, 1, 14)),
        (date(2024, 1, 18), date(2024, 1, 20)),
    ]


def test_gaps_empty_when_fully_covered() -> None:
    ledger = CoverageLedger(
        (CoverageEntry("NSE:RELIANCE-EQ", "1d", date(2024, 1, 1), date(2024, 1, 31)),)
    )
    assert ledger.gaps("NSE:RELIANCE-EQ", "1d", date(2024, 1, 5), date(2024, 1, 20)) == []


def test_covered_point_query() -> None:
    ledger = CoverageLedger(
        (CoverageEntry("NSE:RELIANCE-EQ", "1d", date(2024, 1, 1), date(2024, 1, 10)),)
    )
    assert ledger.covered("NSE:RELIANCE-EQ", "1d", date(2024, 1, 5)) is True
    assert ledger.covered("NSE:RELIANCE-EQ", "1d", date(2024, 1, 11)) is False


def test_entry_validates_window() -> None:
    try:
        CoverageEntry("NSE:A", "1d", date(2024, 1, 10), date(2024, 1, 1))
    except ValueError:
        return
    raise AssertionError("expected end < start to be rejected")
