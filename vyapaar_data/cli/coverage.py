"""Coverage ledger reporting CLI for vyapaar-data.

Scans the Parquet catalog for target instruments and reports coverage status,
date spans, row counts, and uncovered gaps.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from vyapaar_data.adapters.duckdb_store import (
    DuckDbCorporateActionsStore,
    DuckDbFundamentalsStore,
)
from vyapaar_data.adapters.parquet_catalog import ParquetCatalog
from vyapaar_data.domain.coverage import CoverageReport
from vyapaar_data.service.data_service import VyapaarDataService


def run_report(
    catalog_root: str | Path,
    instruments: Sequence[str],
    interval: str = "1d",
    start: date | None = None,
    end: date | None = None,
) -> CoverageReport:
    """Run coverage-ledger reporting against a catalog directory."""
    service = VyapaarDataService(
        corporate_actions=DuckDbCorporateActionsStore(":memory:"),
        fundamentals=DuckDbFundamentalsStore(":memory:"),
        catalog=ParquetCatalog(catalog_root),
    )
    report = service.report_coverage(instruments, interval=interval, start=start, end=end)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vyapaar Data Catalog Coverage-Ledger Report")
    parser.add_argument(
        "--catalog",
        default="data/catalog",
        help="Path to Parquet catalog root directory (default: data/catalog)",
    )
    parser.add_argument(
        "--instruments",
        required=True,
        help="Comma-separated instrument symbols (e.g. NSE:RELIANCE-EQ,NSE:TCS-EQ,NSE:NIFTY50)",
    )
    parser.add_argument(
        "--interval",
        default="1d",
        help="Timeframe interval (default: 1d)",
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Target start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Target end date (YYYY-MM-DD)",
    )

    args = parser.parse_args(argv)
    instruments = [s.strip() for s in args.instruments.split(",") if s.strip()]
    start_d = date.fromisoformat(args.start) if args.start else None
    end_d = date.fromisoformat(args.end) if args.end else None

    report = run_report(
        args.catalog,
        instruments,
        interval=args.interval,
        start=start_d,
        end=end_d,
    )
    print(report.summary_table())
    return 0 if report.missing_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
