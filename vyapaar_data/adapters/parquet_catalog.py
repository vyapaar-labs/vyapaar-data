"""Hive-partitioned and runtime-compatible Parquet catalog with ``DECIMAL128(18,4)`` prices.

Bars are stored either as:
1. Hive layout: ``<root>/<encoded-instrument>/year=<YYYY>/part-*.parquet``
2. Runtime layout: ``<root>/catalog/<TF>/<EXCHANGE>/<SYMBOL>/*.parquet`` or
   ``<root>/<TF>/<EXCHANGE>/<SYMBOL>/*.parquet``

Every financial column returned is an exact fixed-point decimal; no ``float`` ever
touches the returned catalog bars (enforced by explicit schema casting on read and write).
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


def _parse_instrument(instrument: str) -> tuple[str, str, str]:
    """Parse an instrument string into (exchange, raw_symbol, clean_symbol).

    Examples:
        'NSE:RELIANCE-EQ' -> ('NSE', 'RELIANCE-EQ', 'RELIANCE')
        'RELIANCE.NSE'    -> ('NSE', 'RELIANCE', 'RELIANCE')
        'RELIANCE'        -> ('NSE', 'RELIANCE', 'RELIANCE')
    """
    exchange = "NSE"
    if ":" in instrument:
        exchange, raw_sym = instrument.split(":", 1)
    elif "." in instrument:
        raw_sym, exchange = instrument.split(".", 1)
    else:
        raw_sym = instrument

    clean_sym = raw_sym
    for suffix in ("-EQ", "-BE", "-BZ", "-SM"):
        if clean_sym.endswith(suffix):
            clean_sym = clean_sym[: -len(suffix)]
            break
    return exchange, raw_sym, clean_sym


def _find_parquet_files(root: Path, instrument: str, interval: str = "1d") -> list[Path]:
    """Locate Parquet partition files for an instrument across supported layouts."""
    exchange, raw_sym, clean_sym = _parse_instrument(instrument)

    # 1. Hive layout: {root}/<encoded-instrument>/year=*/*.parquet
    for inst_name in (instrument, f"{exchange}:{raw_sym}", f"{exchange}:{clean_sym}"):
        encoded = _encode(inst_name)
        pattern_dir = root / encoded
        if pattern_dir.exists():
            files = list(pattern_dir.glob("year=*/*.parquet"))
            if files:
                return sorted(files)
            files = list(pattern_dir.glob("*.parquet"))
            if files:
                return sorted(files)

    # 2. Runtime layout: {root}/catalog/{TF}/{EXCHANGE}/{SYMBOL}/*.parquet
    # or {root}/{TF}/{EXCHANGE}/{SYMBOL}/*.parquet
    tf_candidates = [interval.upper(), interval.lower()]
    if interval.lower() in ("1d", "d", "day", "1day"):
        tf_candidates.extend(["1D", "1d", "D"])
    elif interval.lower() in ("5m", "5min"):
        tf_candidates.extend(["5M", "5m"])
    elif interval.lower() in ("1h", "1hour"):
        tf_candidates.extend(["1H", "1h"])

    root_candidates = [root]
    if (root / "catalog").exists():
        root_candidates.append(root / "catalog")

    for r in root_candidates:
        for tf in tf_candidates:
            for ex in (exchange, exchange.upper(), exchange.lower()):
                for sym in (raw_sym, clean_sym, raw_sym.upper(), clean_sym.upper()):
                    sym_dir = r / tf / ex / sym
                    if sym_dir.is_dir():
                        files = [p for p in sym_dir.glob("*.parquet") if p.is_file()]
                        if files:
                            return sorted(files)

    return []


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
        interval: str = "1d",
    ) -> pl.DataFrame:
        files = _find_parquet_files(self.root, instrument, interval=interval)
        if not files:
            return pl.DataFrame(schema=BAR_SCHEMA)

        try:
            lf = pl.scan_parquet([str(f) for f in files])
            schema = lf.collect_schema()
            missing = [c for c in BAR_SCHEMA if c not in schema.names()]
            if missing:
                return pl.DataFrame(schema=BAR_SCHEMA)

            # Normalize timestamp to microsecond resolution
            ts_type = schema["ts"]
            if ts_type == pl.Int64:
                lf = lf.with_columns(
                    pl.when(pl.col("ts") > 1_000_000_000_000_000_000)
                    .then(pl.col("ts").cast(pl.Datetime("ns")).dt.cast_time_unit("us"))
                    .when(pl.col("ts") > 1_000_000_000_000_000)
                    .then(pl.col("ts").cast(pl.Datetime("us")))
                    .otherwise(pl.col("ts") * 1_000_000)
                    .cast(pl.Datetime("us"))
                    .alias("ts")
                )
            elif ts_type.is_temporal():
                lf = lf.with_columns(pl.col("ts").dt.cast_time_unit("us"))

            # Normalize price fields to canonical DECIMAL(18, 4)
            for field in _PRICE_FIELDS:
                if schema[field] != _DECIMAL:
                    lf = lf.with_columns(pl.col(field).round(4).cast(pl.String).cast(_DECIMAL))

            # Normalize volume to Int64
            if schema["volume"] != pl.Int64:
                lf = lf.with_columns(pl.col("volume").cast(pl.Int64))

            if start is not None:
                lf = lf.filter(pl.col("ts") >= datetime.combine(start, time.min))
            if end is not None:
                lf = lf.filter(pl.col("ts") <= datetime.combine(end, time.max))

            df = lf.select(list(BAR_SCHEMA)).collect()
            if df.is_empty():
                return df
            return df.sort("ts")
        except Exception:
            return pl.DataFrame(schema=BAR_SCHEMA)

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
