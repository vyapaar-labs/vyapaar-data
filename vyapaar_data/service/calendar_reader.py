"""Scheduled calendar events reader (economic / earnings / dividends / splits /
IPO)."""

from __future__ import annotations

from datetime import date

import polars as pl

from vyapaar_data.ports.repositories import CalendarRepository


class LakehouseCalendarReader:
    """Calendar reader backed by a calendar repository."""

    def __init__(self, repository: CalendarRepository) -> None:
        self.repository = repository

    def get_calendar(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
        category: str | None = None,
    ) -> pl.DataFrame:
        """Calendar events over ``[from_date, to_date]``, optionally
        category-filtered (``Economic`` / ``Earnings`` / ``Dividends`` /
        ``Splits`` / ``IPO``).

        Returns an exact-``Decimal`` Polars frame (empty canonical frame when
        no events match).
        """
        events = self.repository.query(category=category, start_date=from_date, end_date=to_date)
        if not events:
            return pl.DataFrame(
                {
                    "instrument": [],
                    "scheduled_at": [],
                    "country": [],
                    "currency": [],
                    "category": [],
                    "event_name": [],
                    "impact_level": [],
                    "actual": [],
                    "forecast": [],
                    "prior": [],
                    "period_label": [],
                },
                schema={
                    "instrument": pl.String,
                    "scheduled_at": pl.Datetime("us", time_zone="UTC"),
                    "country": pl.String,
                    "currency": pl.String,
                    "category": pl.String,
                    "event_name": pl.String,
                    "impact_level": pl.String,
                    "actual": pl.Decimal(18, 4),
                    "forecast": pl.Decimal(18, 4),
                    "prior": pl.Decimal(18, 4),
                    "period_label": pl.String,
                },
            )
        return pl.DataFrame(
            {
                "instrument": [e.instrument for e in events],
                "scheduled_at": [e.scheduled_at for e in events],
                "country": [e.country for e in events],
                "currency": [e.currency for e in events],
                "category": [e.category for e in events],
                "event_name": [e.event_name for e in events],
                "impact_level": [e.impact_level for e in events],
                "actual": [e.actual for e in events],
                "forecast": [e.forecast for e in events],
                "prior": [e.prior for e in events],
                "period_label": [e.period_label for e in events],
            },
            schema={
                "instrument": pl.String,
                "scheduled_at": pl.Datetime("us", time_zone="UTC"),
                "country": pl.String,
                "currency": pl.String,
                "category": pl.String,
                "event_name": pl.String,
                "impact_level": pl.String,
                "actual": pl.Decimal(18, 4),
                "forecast": pl.Decimal(18, 4),
                "prior": pl.Decimal(18, 4),
                "period_label": pl.String,
            },
        )


__all__ = ["LakehouseCalendarReader"]
