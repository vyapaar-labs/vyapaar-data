"""Shared pytest fixtures for the vyapaar-data test suite."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import polars as pl
import pytest

from vyapaar_data import DuckDbCorporateActionsStore, DuckDbFundamentalsStore, ParquetCatalog
from vyapaar_data.domain.corporate_actions import Dividend, Split
from vyapaar_data.domain.fundamentals import FundamentalRecord


def utc(y: int, m: int, d: int, hour: int = 0) -> datetime:
    return datetime(y, m, d, hour, tzinfo=UTC)


@pytest.fixture
def fundamentals_store() -> DuckDbFundamentalsStore:
    return DuckDbFundamentalsStore(":memory:")


@pytest.fixture
def corporate_actions_store() -> DuckDbCorporateActionsStore:
    return DuckDbCorporateActionsStore(":memory:")


@pytest.fixture
def catalog(tmp_path) -> ParquetCatalog:
    return ParquetCatalog(tmp_path / "catalog")


@pytest.fixture
def sample_bars() -> pl.DataFrame:
    """Daily bars for NSE:RELIANCE-EQ across two calendar years."""
    rows: list[dict[str, object]] = []
    for day in (date(2023, 12, 28), date(2023, 12, 29), date(2024, 1, 2), date(2024, 1, 3)):
        close = {
            "2023-12-28": "1250.00",
            "2023-12-29": "1260.00",
            "2024-01-02": "1270.00",
            "2024-01-03": "1280.00",
        }[day.isoformat()]
        rows.append(
            {
                "ts": datetime.combine(day, time.min, tzinfo=UTC),
                "open": close,
                "high": close,
                "low": close,
                "close": close,
                "volume": 1_000_000,
            }
        )
    return pl.DataFrame(rows)


@pytest.fixture
def sample_fundamentals() -> list[FundamentalRecord]:
    return [
        FundamentalRecord(
            instrument="NSE:RELIANCE-EQ",
            period_end_date=date(2023, 12, 31),
            filing_date=date(2024, 1, 20),
            metric="net_profit",
            value="68000.00",
        ),
        FundamentalRecord(
            instrument="NSE:RELIANCE-EQ",
            period_end_date=date(2024, 3, 31),
            filing_date=date(2024, 4, 25),
            metric="net_profit",
            value="72100.00",
        ),
    ]


@pytest.fixture
def sample_actions() -> list[object]:
    return [
        Split(instrument="NSE:RELIANCE-EQ", ex_date=date(2024, 1, 2), old_shares=1, new_shares=2),
        Dividend(instrument="NSE:RELIANCE-EQ", ex_date=date(2024, 1, 3), per_share="10.00"),
    ]
