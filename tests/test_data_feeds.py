"""Analytical data-feed ports: MarketReader, ScreenerReader, MacroReader,
ReferenceExporter and the VectorizedScreener engine."""

from __future__ import annotations

from decimal import Decimal

import polars as pl
import pytest

from vyapaar_data import (
    ComparisonOp,
    DuckDbMacroStore,
    InMemoryReferenceExporter,
    LakehouseMarketReader,
    PythonMacroReader,
    ScreenCondition,
    ScreenQuery,
    ScreenValue,
    VectorizedScreener,
)
from vyapaar_data.ports.repositories import BAR_SCHEMA


def build_reader(catalog, data_service=None) -> LakehouseMarketReader:
    return LakehouseMarketReader(catalog=catalog, data_service=data_service)


# --------------------------------------------------------------------------- #
# MarketReader
# --------------------------------------------------------------------------- #


def test_market_reader_get_quote_returns_latest_price(catalog, sample_bars):
    reader = build_reader(catalog)
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    quote = reader.get_quote("NSE:RELIANCE-EQ")
    assert quote["instrument"] == "NSE:RELIANCE-EQ"
    assert quote["price"] == Decimal("1280.0000")
    assert quote["ts"] is not None


def test_market_reader_get_quote_missing_instrument(catalog):
    reader = build_reader(catalog)
    assert reader.get_quote("NSE:NOPE-EQ") == {
        "instrument": "NSE:NOPE-EQ",
        "price": None,
        "ts": None,
    }


def test_market_reader_get_candles_decimal_schema(catalog, sample_bars):
    reader = build_reader(catalog)
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    candles = reader.get_candles("NSE:RELIANCE-EQ")
    assert not candles.is_empty()
    assert candles.columns == list(BAR_SCHEMA)
    assert candles["close"].dtype == pl.Decimal(18, 4)
    assert candles["volume"].dtype == pl.Int64()


def test_market_reader_get_returns(catalog, sample_bars):
    reader = build_reader(catalog)
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    returns = reader.get_returns("NSE:RELIANCE-EQ")
    assert returns.columns == ["ts", "return"]
    assert len(returns) == len(sample_bars)
    # first return is NaN (no previous close); remaining are simple pct changes.
    assert returns["return"][0] is None or returns["return"][0] != returns["return"][0]


def test_market_reader_get_indicators_sma_and_ema(catalog, sample_bars):
    reader = build_reader(catalog)
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    sma = reader.get_indicators("NSE:RELIANCE-EQ", "sma", params={"window": 2})
    assert sma.columns == ["ts", "sma"]
    assert sma["sma"].to_list()[2] == Decimal("1265.0000")  # (1260+1270)/2

    ema = reader.get_indicators("NSE:RELIANCE-EQ", "ema", params={"window": 2})
    assert ema.columns == ["ts", "ema"]

    with pytest.raises(ValueError):
        reader.get_indicators("NSE:RELIANCE-EQ", "macd")


# --------------------------------------------------------------------------- #
# ScreenerReader / VectorizedScreener
# --------------------------------------------------------------------------- #


def test_screener_execute_screen_filters_by_gt(catalog, sample_bars):
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    reader = build_reader(catalog)
    screener = VectorizedScreener(reader=reader)
    query = ScreenQuery(
        universe=["NSE:RELIANCE-EQ"],
        conditions=[
            ScreenCondition(
                field="close",
                operator=ComparisonOp.GT,
                value=ScreenValue(literal=Decimal("1200")),
            )
        ],
    )
    result = screener.execute_screen(query)
    assert result.instruments == ["NSE:RELIANCE-EQ"]
    assert result.rows == 1


def test_screener_execute_screen_rejects(catalog, sample_bars):
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    reader = build_reader(catalog)
    screener = VectorizedScreener(reader=reader)
    query = ScreenQuery(
        universe=["NSE:RELIANCE-EQ"],
        conditions=[
            ScreenCondition(
                field="close",
                operator=ComparisonOp.GT,
                value=ScreenValue(literal=Decimal("1300")),
            )
        ],
    )
    result = screener.execute_screen(query)
    assert result.instruments == []
    assert result.rows == 0


def test_screener_crosses_above_literal(catalog, sample_bars):
    # closes: 1250, 1260, 1270, 1280 -> last step 1270->1280 crosses above 1275
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    reader = build_reader(catalog)
    screener = VectorizedScreener(reader=reader)
    query = ScreenQuery(
        universe=["NSE:RELIANCE-EQ"],
        conditions=[
            ScreenCondition(
                field="close",
                operator=ComparisonOp.CROSSES_ABOVE,
                value=ScreenValue(literal=Decimal("1275")),
            )
        ],
    )
    result = screener.execute_screen(query)
    assert result.instruments == ["NSE:RELIANCE-EQ"]


def test_screener_crosses_below_literal(catalog, sample_bars):
    # last two closes 1270->1280 do NOT cross below 1275 (already rising past it)
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    reader = build_reader(catalog)
    screener = VectorizedScreener(reader=reader)
    query = ScreenQuery(
        universe=["NSE:RELIANCE-EQ"],
        conditions=[
            ScreenCondition(
                field="close",
                operator=ComparisonOp.CROSSES_BELOW,
                value=ScreenValue(literal=Decimal("1275")),
            )
        ],
    )
    result = screener.execute_screen(query)
    assert result.instruments == []


def test_screener_crosses_below_downward_move(catalog):
    # bars ending ... 1280 -> 1260 cross below 1270 on the final step
    from datetime import UTC, datetime

    down_bars = pl.DataFrame(
        {
            "ts": [
                datetime(2024, 1, 2, tzinfo=UTC),
                datetime(2024, 1, 3, tzinfo=UTC),
            ],
            "open": [Decimal("1270"), Decimal("1260")],
            "high": [Decimal("1280"), Decimal("1270")],
            "low": [Decimal("1260"), Decimal("1250")],
            "close": [Decimal("1280"), Decimal("1260")],
            "volume": [1_000_000, 1_000_000],
        }
    ).with_columns(
        pl.col("open").cast(pl.Decimal(18, 4)),
        pl.col("high").cast(pl.Decimal(18, 4)),
        pl.col("low").cast(pl.Decimal(18, 4)),
        pl.col("close").cast(pl.Decimal(18, 4)),
        pl.col("volume").cast(pl.Int64()),
    )
    catalog.write_bars("NSE:RELIANCE-EQ", down_bars)
    reader = build_reader(catalog)
    screener = VectorizedScreener(reader=reader)
    query = ScreenQuery(
        universe=["NSE:RELIANCE-EQ"],
        conditions=[
            ScreenCondition(
                field="close",
                operator=ComparisonOp.CROSSES_BELOW,
                value=ScreenValue(literal=Decimal("1270")),
            )
        ],
    )
    result = screener.execute_screen(query)
    assert result.instruments == ["NSE:RELIANCE-EQ"]


def test_screener_order_by_and_limit(catalog, sample_bars):
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    reader = build_reader(catalog)
    screener = VectorizedScreener(reader=reader)
    query = ScreenQuery(
        universe=["NSE:RELIANCE-EQ"],
        conditions=[
            ScreenCondition(
                field="close",
                operator=ComparisonOp.GTE,
                value=ScreenValue(literal=Decimal("1250")),
            )
        ],
        order_by="close DESC",
        limit=1,
    )
    result = screener.execute_screen(query)
    assert result.rows <= 1
    assert result.instruments == ["NSE:RELIANCE-EQ"]


def test_screener_unknown_field_passes_none(catalog, sample_bars):
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    reader = build_reader(catalog)
    screener = VectorizedScreener(reader=reader)
    query = ScreenQuery(
        universe=["NSE:RELIANCE-EQ"],
        conditions=[
            ScreenCondition(
                field="nonexistent",
                operator=ComparisonOp.GT,
                value=ScreenValue(literal=Decimal("1")),
            )
        ],
    )
    result = screener.execute_screen(query)
    assert result.instruments == []


# --------------------------------------------------------------------------- #
# ReferenceExporter
# --------------------------------------------------------------------------- #


def test_reference_exporter_export_and_resolve():
    exporter = InMemoryReferenceExporter()
    frame = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    uri = exporter.export("screen_1", frame)
    assert uri == "$vyapaar/ref/screen_1"
    assert uri in exporter
    resolved = exporter.resolve(uri)
    assert resolved.equals(frame)
    with pytest.raises(KeyError):
        exporter.resolve("$vyapaar/ref/does-not-exist")


# --------------------------------------------------------------------------- #
# MacroReader
# --------------------------------------------------------------------------- #


def test_macro_reader_empty_canonical_schema():
    reader = PythonMacroReader(DuckDbMacroStore(":memory:"))
    frame = reader.get_series("RBI_REPO_RATE")
    assert frame.is_empty()
    assert frame.columns == ["ts", "series_id", "value"]
    assert frame["value"].dtype == pl.Decimal(18, 4)


# --------------------------------------------------------------------------- #
# Zero-floats invariants
# --------------------------------------------------------------------------- #


def test_candles_contain_no_float_columns(catalog, sample_bars):
    reader = build_reader(catalog)
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    candles = reader.get_candles("NSE:RELIANCE-EQ")
    float_dtypes = {pl.Float32, pl.Float64}
    for col in candles.columns:
        assert candles[col].dtype not in float_dtypes, f"float column found: {col}"


def test_screener_result_reference_is_export_uri(catalog, sample_bars):
    catalog.write_bars("NSE:RELIANCE-EQ", sample_bars)
    reader = build_reader(catalog)
    exporter = InMemoryReferenceExporter()
    screener = VectorizedScreener(reader=reader, exporter=exporter)
    query = ScreenQuery(
        universe=["NSE:RELIANCE-EQ"],
        conditions=[
            ScreenCondition(
                field="close",
                operator=ComparisonOp.GT,
                value=ScreenValue(literal=Decimal("1200")),
            )
        ],
    )
    result = screener.execute_screen(query)
    assert result.reference is not None
    assert result.reference.startswith("$vyapaar/ref/")
    assert exporter.resolve(result.reference).columns == list(BAR_SCHEMA)
