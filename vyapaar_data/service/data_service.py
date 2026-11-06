"""VyapaarDataService: the unified lakehouse facade.

``adjusted_history`` restates raw prices and volumes to the *current*
corporate-action basis: for every bar at date ``d``, all actions whose
ex-date is strictly after ``d`` are chained in chronological order. This is the
standard total-return back-adjustment used by Indian backtests.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal

import polars as pl

from vyapaar_data.domain.corporate_actions import CorporateAction
from vyapaar_data.domain.coverage import (
    CoverageEntry,
    CoverageLedger,
    CoverageReport,
    InstrumentCoverage,
)
from vyapaar_data.domain.fundamentals import FundamentalRecord
from vyapaar_data.ports.repositories import (
    CatalogRepository,
    CorporateActionsRepository,
    FundamentalsRepository,
)

_PRICE_FIELDS = ("open", "high", "low", "close")


def _restate_price(price: Decimal, actions_after: Iterable[CorporateAction]) -> Decimal:
    adjusted = price
    for action in actions_after:
        adjusted = action.apply(adjusted)
    return adjusted


def _restate_volume(volume: int, actions_after: Iterable[CorporateAction]) -> Decimal:
    quantity: Decimal = Decimal(volume)
    for action in actions_after:
        multiplier = getattr(action, "quantity_multiplier", None)
        if multiplier is not None:
            quantity *= multiplier
    return quantity


class VyapaarDataService:
    """Facade composing corporate actions, fundamentals, and catalog storage."""

    def __init__(
        self,
        corporate_actions: CorporateActionsRepository,
        fundamentals: FundamentalsRepository,
        catalog: CatalogRepository,
    ) -> None:
        self.corporate_actions = corporate_actions
        self.fundamentals = fundamentals
        self.catalog = catalog

    def adjusted_history(
        self,
        instrument: str,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        """Raw history restated to the current basis (splits, bonuses, dividends, rights)."""
        bars = self.catalog.read_bars(instrument, start, end)
        if bars.is_empty():
            return bars
        actions = sorted(self.corporate_actions.list(instrument), key=lambda action: action.ex_date)
        dates = [ts.date() for ts in bars["ts"].to_list()]
        for field in _PRICE_FIELDS:
            adjusted: list[Decimal] = []
            for ts, price in zip(dates, bars[field].to_list(), strict=True):
                actions_after = [action for action in actions if action.ex_date > ts]
                adjusted.append(_restate_price(Decimal(price), actions_after))
            bars = bars.with_columns(pl.Series(field, adjusted, dtype=pl.Decimal(18, 4)))
        quantities = [
            _restate_volume(int(v), [a for a in actions if a.ex_date > ts])
            for ts, v in zip(dates, bars["volume"].to_list(), strict=True)
        ]
        bars = bars.with_columns(pl.Series("volume", quantities, dtype=pl.Decimal(18, 4)))
        return bars

    def as_of_fundamentals(self, instrument: str, as_of: date) -> list[FundamentalRecord]:
        """Fundamentals filed on or before ``as_of`` (no look-ahead)."""
        return self.fundamentals.query(instrument, as_of)

    def coverage(self, instrument: str, interval: str = "1d") -> CoverageEntry | None:
        """Compute the catalog coverage window for an instrument."""
        try:
            bars = self.catalog.read_bars(instrument, interval=interval)
        except TypeError:
            bars = self.catalog.read_bars(instrument)
        if bars.is_empty():
            return None
        ts = bars["ts"]
        min_ts = ts.min()
        max_ts = ts.max()
        assert isinstance(min_ts, datetime) and isinstance(max_ts, datetime)
        return CoverageEntry(
            instrument=instrument,
            interval=interval,
            start=min_ts.date(),
            end=max_ts.date(),
            row_count=len(bars),
        )

    def report_coverage(
        self,
        instruments: Iterable[str],
        interval: str = "1d",
        start: date | None = None,
        end: date | None = None,
    ) -> CoverageReport:
        """Evaluate coverage across a target list of instruments."""
        items: list[InstrumentCoverage] = []
        for inst in instruments:
            entry = self.coverage(inst, interval=interval)
            gaps: list[tuple[date, date]] = []
            if entry is not None:
                if start is not None and end is not None:
                    ledger = CoverageLedger((entry,))
                    gaps = ledger.gaps(inst, interval, start, end)
                items.append(
                    InstrumentCoverage(
                        instrument=inst,
                        interval=interval,
                        entry=entry,
                        gaps=tuple(gaps),
                    )
                )
            else:
                if start is not None and end is not None:
                    gaps = [(start, end)]
                items.append(
                    InstrumentCoverage(
                        instrument=inst,
                        interval=interval,
                        entry=None,
                        gaps=tuple(gaps),
                    )
                )
        root_path = str(getattr(self.catalog, "root", "unknown"))
        return CoverageReport(
            catalog_root=root_path,
            interval=interval,
            target_start=start,
            target_end=end,
            instruments=tuple(items),
        )


__all__ = ["VyapaarDataService"]
