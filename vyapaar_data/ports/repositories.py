"""Repository and service protocols (ports).

The service layer depends on these protocols, never on concrete storage
classes, so DuckDB, Parquet, or future providers are swappable without touching
domain or service code.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

import polars as pl

from vyapaar_data.domain.corporate_actions import CorporateAction
from vyapaar_data.domain.fundamentals import FundamentalRecord

# Canonical bar schema for the Parquet catalog. All financial columns are
# fixed-point decimals; ``ts`` is microsecond-resolution UTC.
BAR_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Datetime("us"),
    "open": pl.Decimal(18, 4),
    "high": pl.Decimal(18, 4),
    "low": pl.Decimal(18, 4),
    "close": pl.Decimal(18, 4),
    "volume": pl.Int64(),
}


@runtime_checkable
class CorporateActionsRepository(Protocol):
    """Storage for corporate action records."""

    def list(
        self, instrument: str | None = None, as_of: date | None = None
    ) -> list[CorporateAction]:
        """Return actions, optionally filtered by instrument and ex-date window."""
        ...

    def add(self, action: CorporateAction) -> None:
        """Persist an action idempotently (same instrument+ex_date+type)."""
        ...


@runtime_checkable
class FundamentalsRepository(Protocol):
    """Storage for point-in-time fundamental records."""

    def upsert(self, record: FundamentalRecord) -> None:
        """Insert or replace a fundamental record (idempotent on full key)."""
        ...

    def query(
        self,
        instrument: str,
        as_of: date,
        metric: str | None = None,
    ) -> list[FundamentalRecord]:
        """Return records with ``filing_date <= as_of`` (no look-ahead)."""
        ...


@runtime_checkable
class CatalogRepository(Protocol):
    """Parquet catalog of OHLCV bars keyed by instrument."""

    def write_bars(self, instrument: str, bars: pl.DataFrame) -> None:
        """Persist bars, validating the canonical decimal schema."""
        ...

    def read_bars(
        self,
        instrument: str,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        """Read bars sorted by timestamp, optionally filtered to a window."""
        ...


@runtime_checkable
class DataService(Protocol):
    """Unified, look-ahead-bias-free data facade."""

    def adjusted_history(
        self,
        instrument: str,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        """Raw history restated to the current corporate-action basis."""
        ...
