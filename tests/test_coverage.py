"""Coverage ledger gap discovery and coverage reporting."""

from __future__ import annotations

from datetime import date

from vyapaar_data.adapters.duckdb_store import (
    DuckDbCorporateActionsStore,
    DuckDbFundamentalsStore,
)
from vyapaar_data.cli.coverage import run_report
from vyapaar_data.domain.coverage import (
    CoverageEntry,
    CoverageLedger,
    CoverageReport,
)
from vyapaar_data.service.data_service import VyapaarDataService


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


def test_coverage_report_metrics(catalog, sample_bars) -> None:
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    service = VyapaarDataService(
        corporate_actions=DuckDbCorporateActionsStore(":memory:"),
        fundamentals=DuckDbFundamentalsStore(":memory:"),
        catalog=catalog,
    )

    report = service.report_coverage(
        ["NSE:RELIANCE-EQ", "NSE:NIFTY50"],
        interval="1d",
        start=date(2023, 1, 1),
        end=date(2024, 12, 31),
    )

    assert report.total_count == 2
    assert report.covered_count == 1
    assert report.missing_count == 1
    assert report.covered_symbols == ("NSE:RELIANCE-EQ",)
    assert report.missing_symbols == ("NSE:NIFTY50",)

    table = report.summary_table()
    assert "NSE:RELIANCE-EQ" in table
    assert "NSE:NIFTY50" in table
    assert "MISSING" in table


def test_run_report_cli(catalog, sample_bars) -> None:
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    report = run_report(catalog.root, ["NSE:RELIANCE-EQ", "NSE:MISSING"], interval="1d")
    assert isinstance(report, CoverageReport)
    assert report.total_count == 2
    assert report.covered_count == 1
    assert report.missing_count == 1
