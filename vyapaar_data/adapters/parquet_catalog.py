"""Hive-partitioned Parquet catalog with fixed-point ``DECIMAL128(18,4)`` prices.

Bars are stored as ``<root>/<encoded-instrument>/year=<YYYY>/part-*.parquet``.
Every financial column is an exact fixed-point decimal; no ``float`` ever
touches the catalog (enforced by an explicit PyArrow schema at write time).
"""

from __future__ import annotations

import re
from datetime import date, datetime, time
from pathlib import Path

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from vyapaar_data.ports.repositories import BAR_SCHEMA

_PRICE_FIELDS = ("open", "high", "low", "close")

_ARROW_SCHEMA = pa.schema(
    [
        pa.field("ts", pa.timestamp("us")),
        pa.field("open", pa.decimal128(18, 4)),
        pa.field("high", pa.decimal128(18, 4)),
        pa.field("low", pa.decimal128(18, 4)),
        pa.field("close", pa.decimal128(18, 4)),
        pa.field("volume", pa.int64()),
    ]
)

_DECIMAL = pl.Decimal(18, 4)


def _encode(instrument: str) -> str:
    """Safe filesystem encoding of an ``InstrumentId`` (e.g. ``NSE:RELIANCE-EQ``)."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", instrument)


class ParquetCatalog:
    """Parquet lakehouse catalog implementing :class:`CatalogRepository`."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write_bars(self, instrument: str, bars: pl.DataFrame) -> None:
        df = self._normalize(bars)
        df = df.with_columns(pl.col("ts").dt.year().alias("_year"))
        instrument_dir = self.root / _encode(instrument)
        for year in df.get_column("_year").unique().sort().to_list():
            chunk = df.filter(pl.col("_year") == year).drop("_year")
            partition_dir = instrument_dir / f"year={year}"
            partition_dir.mkdir(parents=True, exist_ok=True)
            path = partition_dir / "part-0.parquet"
            pq.write_table(self._to_arrow_table(chunk), path, version="2.6")

    def read_bars(
        self,
        instrument: str,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        instrument_dir = self.root / _encode(instrument)
        if not instrument_dir.exists():
            return pl.DataFrame(schema=BAR_SCHEMA)
        pattern = str(instrument_dir / "year=*" / "*.parquet")
        try:
            lf = pl.scan_parquet(pattern)
        except Exception:
            return pl.DataFrame(schema=BAR_SCHEMA)
        if start is not None:
            lf = lf.filter(pl.col("ts") >= datetime.combine(start, time.min))
        if end is not None:
            lf = lf.filter(pl.col("ts") <= datetime.combine(end, time.max))
        df = lf.select(list(BAR_SCHEMA)).collect()
        if df.is_empty():
            return df
        return df.sort("ts")

    def _normalize(self, bars: pl.DataFrame) -> pl.DataFrame:
        missing = [c for c in BAR_SCHEMA if c not in bars.columns]
        if missing:
            raise ValueError(f"bars missing required columns: {missing}")
        for field in _PRICE_FIELDS:
            bars = bars.with_columns(pl.col(field).cast(_DECIMAL))
        bars = bars.with_columns(
            pl.col("ts").cast(pl.Datetime("us")),
            pl.col("volume").cast(pl.Int64()),
        )
        return bars.select(list(BAR_SCHEMA)).sort("ts")

    @staticmethod
    def _to_arrow_table(chunk: pl.DataFrame) -> pa.Table:
        """Build an Arrow table with the canonical ``DECIMAL128(18,4)`` schema."""
        data = {name: chunk[name].to_list() for name in _ARROW_SCHEMA.names}
        return pa.Table.from_pydict(data, schema=_ARROW_SCHEMA)


def arrow_schema() -> pa.Schema:
    """Expose the canonical Arrow schema (used by tests and providers)."""
    return _ARROW_SCHEMA
