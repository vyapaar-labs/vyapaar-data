"""Parquet catalog: exact decimal round-trip and year partitioning."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from vyapaar_data.adapters.parquet_catalog import arrow_schema


def test_write_and_read_preserves_exact_decimals(catalog, sample_bars) -> None:
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    bars = catalog.read_bars("NSE:RELIANCE-EQ")

    assert bars.height == 4
    assert bars.sort("ts")["close"].to_list() == [
        Decimal("1250.0000"),
        Decimal("1260.0000"),
        Decimal("1270.0000"),
        Decimal("1280.0000"),
    ]
    assert bars["volume"].dtype == pl.Int64


def test_catalog_schema_is_decimal128_18_4(catalog, sample_bars) -> None:
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    part_file = next((catalog.root / "NSE_RELIANCE-EQ").rglob("*.parquet"))
    metadata = pq.ParquetFile(part_file).schema_arrow
    for field_name in ("open", "high", "low", "close"):
        field_type = metadata.field(field_name).type
        assert str(field_type) == "decimal128(18, 4)"


def test_catalog_partitions_by_year(catalog, sample_bars) -> None:
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    root = catalog.root / "NSE_RELIANCE-EQ"
    assert (root / "year=2023").exists()
    assert (root / "year=2024").exists()


def test_read_bars_filters_by_date_window(catalog, sample_bars) -> None:
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    window = catalog.read_bars("NSE:RELIANCE-EQ", start=date(2024, 1, 1))
    assert window.height == 2
    assert window["close"].to_list() == [Decimal("1270.0000"), Decimal("1280.0000")]


def test_read_bars_unknown_instrument_returns_empty(catalog) -> None:
    bars = catalog.read_bars("NSE:MISSING-EQ")
    assert bars.is_empty()
    assert bars.columns == ["ts", "open", "high", "low", "close", "volume"]


def test_write_rejects_missing_columns(catalog) -> None:
    import polars as pl

    with pytest.raises(ValueError):
        catalog.write_bars("NSE:BAD", pl.DataFrame({"close": [1, 2]}))


def test_arrow_schema_exposed() -> None:
    schema = arrow_schema()
    assert schema.field("close").type == pa.decimal128(18, 4)
    assert schema.field("ts").type == pa.timestamp("us")


def test_timestamps_are_utc_microsecond(catalog, sample_bars) -> None:
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    bars = catalog.read_bars("NSE:RELIANCE-EQ")
    first = bars.sort("ts")["ts"][0]
    assert isinstance(first, datetime)
    assert first == datetime(2023, 12, 28)
