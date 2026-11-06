"""Deterministic NSE bhavcopy parser.

Parses the official NSE ``cm`` bhavcopy CSV layout into ``Decimal``-based rows
and maps them onto the canonical catalog bar schema.

Columns (official NSE header)::

    SYMBOL,SERIES,DATE,PREV_CLOSE,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,LAST_PRICE,
    CLOSE_PRICE,AVERAGE_PRICE,TOTAL_TRADED_QUANTITY,TURNOVER_LACS,NO_OF_TRADES,
    DELIVERABLE_QTY,% DLVY TO QTY
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path

import polars as pl

from vyapaar_data.adapters.parquet_catalog import _DECIMAL  # canonical fixed-point dtype
from vyapaar_data.ports.repositories import BAR_SCHEMA

_NSE_HEADER = (
    "SYMBOL",
    "SERIES",
    "DATE",
    "PREV_CLOSE",
    "OPEN_PRICE",
    "HIGH_PRICE",
    "LOW_PRICE",
    "LAST_PRICE",
    "CLOSE_PRICE",
    "AVERAGE_PRICE",
    "TOTAL_TRADED_QUANTITY",
    "TURNOVER_LACS",
    "NO_OF_TRADES",
    "DELIVERABLE_QTY",
    "% DLVY TO QTY",
)


@dataclass(frozen=True, slots=True)
class BhavcopyRow:
    """One NSE bhavcopy line with exact ``Decimal`` prices."""

    symbol: str
    series: str
    trade_date: date
    prev_close: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    last: Decimal
    close: Decimal
    average_price: Decimal
    total_traded_quantity: int
    turnover_lacs: Decimal
    no_of_trades: int
    deliverable_qty: int
    deliverable_pct: Decimal | None = None


def _decimal(text: str, field: str) -> Decimal:
    try:
        return Decimal(text.strip())
    except Exception as exc:
        raise ValueError(f"invalid {field!r} value in bhavcopy: {text!r}") from exc


def _date(text: str, field: str) -> date:
    try:
        return datetime.strptime(text.strip(), "%d-%b-%Y").date()
    except Exception as exc:
        raise ValueError(f"invalid {field!r} date in bhavcopy: {text!r}") from exc


def parse_bhavcopy(text: str) -> list[BhavcopyRow]:
    """Parse raw bhavcopy text into typed rows (header is mandatory)."""
    reader = csv.DictReader(line for line in text.splitlines() if line.strip())
    if reader.fieldnames is None or not reader.fieldnames:
        raise ValueError("bhavcopy is empty or missing a header")
    rows: list[BhavcopyRow] = []
    for raw in reader:
        if not any(raw.values()):
            continue
        rows.append(
            BhavcopyRow(
                symbol=raw["SYMBOL"].strip(),
                series=raw["SERIES"].strip(),
                trade_date=_date(raw["DATE"], "DATE"),
                prev_close=_decimal(raw["PREV_CLOSE"], "PREV_CLOSE"),
                open=_decimal(raw["OPEN_PRICE"], "OPEN_PRICE"),
                high=_decimal(raw["HIGH_PRICE"], "HIGH_PRICE"),
                low=_decimal(raw["LOW_PRICE"], "LOW_PRICE"),
                last=_decimal(raw["LAST_PRICE"], "LAST_PRICE"),
                close=_decimal(raw["CLOSE_PRICE"], "CLOSE_PRICE"),
                average_price=_decimal(raw["AVERAGE_PRICE"], "AVERAGE_PRICE"),
                total_traded_quantity=int(raw["TOTAL_TRADED_QUANTITY"]),
                turnover_lacs=_decimal(raw["TURNOVER_LACS"], "TURNOVER_LACS"),
                no_of_trades=int(raw["NO_OF_TRADES"]),
                deliverable_qty=int(raw["DELIVERABLE_QTY"]),
                deliverable_pct=_decimal(raw["% DLVY TO QTY"], "% DLVY TO QTY")
                if raw.get("% DLVY TO QTY", "").strip()
                else None,
            )
        )
    return rows


def read_bhavcopy(path: str | Path) -> list[BhavcopyRow]:
    """Read and parse a bhavcopy CSV file from disk."""
    with open(path, encoding="utf-8") as handle:
        return parse_bhavcopy(handle.read())


def rows_to_bars(rows: list[BhavcopyRow], instrument_prefix: str = "NSE:") -> pl.DataFrame:
    """Map bhavcopy rows onto the canonical catalog bar schema.

    Prices are stored as fixed-point ``DECIMAL128(18,4)``; the trade date is
    anchored at ``00:00:00 UTC`` in the ``ts`` column.
    """
    if not rows:
        return pl.DataFrame(schema=BAR_SCHEMA)
    data: dict[str, list[object]] = {
        "ts": [datetime.combine(r.trade_date, time.min, tzinfo=UTC) for r in rows],
        "open": [r.open for r in rows],
        "high": [r.high for r in rows],
        "low": [r.low for r in rows],
        "close": [r.close for r in rows],
        "volume": [r.total_traded_quantity for r in rows],
    }
    df = pl.DataFrame(data)
    df = df.with_columns(
        pl.col("ts").cast(pl.Datetime("us")),
        pl.col("open").cast(_DECIMAL),
        pl.col("high").cast(_DECIMAL),
        pl.col("low").cast(_DECIMAL),
        pl.col("close").cast(_DECIMAL),
        pl.col("volume").cast(pl.Int64()),
    )
    return df.sort("ts")
