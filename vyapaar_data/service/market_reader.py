"""Lakehouse-backed ``MarketReader`` implementation.

Reads quotes, candles, returns, and indicators from the Parquet catalog via
``CatalogRepository`` and restates them through ``VyapaarDataService`` so that
corporate actions are back-adjusted. All stored financial columns remain exact
``decimal.Decimal`` (``DECIMAL128(18,4)``); analytical derivatives (returns,
indicators) are computed in Polars for presentation to downstream engines.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from vyapaar_data.ports.repositories import CatalogRepository
from vyapaar_data.service.data_service import VyapaarDataService


class LakehouseMarketReader:
    """Market data reader backed by the Parquet catalog + data service."""

    def __init__(
        self,
        catalog: CatalogRepository,
        data_service: VyapaarDataService | None = None,
    ) -> None:
        self.catalog = catalog
        self.data_service = data_service

    def _frame(
        self,
        instrument: str,
        start: date | None,
        end: date | None,
        interval: str,
    ) -> pl.DataFrame:
        if self.data_service is not None:
            return self.data_service.adjusted_history(instrument, start, end)
        return self.catalog.read_bars(instrument, start, end, interval=interval)

    def get_quote(self, instrument: str) -> dict[str, object]:
        """Latest quote for ``instrument`` (price + ts)."""
        bars = self.catalog.read_bars(instrument)
        if bars.is_empty():
            return {"instrument": instrument, "price": None, "ts": None}
        last = bars.tail(1)
        return {
            "instrument": instrument,
            "price": last["close"][0],
            "ts": last["ts"][0],
        }

    def get_candles(
        self,
        instrument: str,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> pl.DataFrame:
        """OHLCV bars for ``instrument`` over ``[start, end]``."""
        return self._frame(instrument, start, end, interval)

    def get_returns(
        self,
        instrument: str,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> pl.DataFrame:
        """Simple period returns for ``instrument`` over ``[start, end]``."""
        bars = self._frame(instrument, start, end, interval)
        if bars.is_empty() or "close" not in bars.columns:
            return pl.DataFrame(schema={"ts": pl.Datetime("us"), "return": pl.Float64()})
        return bars.select(
            [
                "ts",
                pl.col("close").pct_change().alias("return"),
            ]
        )

    def get_indicators(
        self,
        instrument: str,
        indicator: str,
        params: dict[str, object] | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        """Technical indicator values (SMA / EMA over close) for ``instrument``."""
        params = params or {}
        window = int(params.get("window", 20))
        bars = self._frame(instrument, start, end, interval="1d")
        if bars.is_empty() or "close" not in bars.columns:
            return pl.DataFrame(schema={"ts": pl.Datetime("us"), indicator: pl.Float64()})
        close = pl.col("close")
        name = indicator.lower()
        if name == "sma":
            series = close.rolling_mean(window).alias(name)
        elif name == "ema":
            series = close.ewm_mean(span=window).alias(name)
        else:
            raise ValueError(f"unsupported indicator: {indicator!r}")
        return bars.select(["ts", series])


__all__ = ["LakehouseMarketReader"]
