"""Stubbed calendar events provider.

This provider ships a small, hardcoded calendar of scheduled events
(economic releases, earnings, dividends, splits, IPOs) so that the
``CalendarReader`` port has data to serve while an external calendar
data source/vendor decision remains pending.

Zero-floats invariant: every numeric value is an exact ``decimal.Decimal``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

from vyapaar_data.domain.calendar import CalendarEvent

_VALID_CATEGORIES = ("Economic", "Earnings", "Dividends", "Splits", "IPO")
_VALID_IMPACT_LEVELS = ("High", "Medium", "Low")

# Stubbed calendar rows. These are illustrative values reverse-engineered
# from the shape described in docs/gaps/0010-economic-calendar-ingestion.md
# (observed against vela.luxalgo.com's calendar tab on 2026-11-09). No real
# vendor data is asserted here: this is placeholder data to be replaced once a
# concrete calendar data source is selected (see docs/gaps/0012-*.md).
_STUBBED_ROWS: list[dict[str, str | None]] = [
    {
        "instrument": "NSE:RELIANCE-EQ",
        "scheduled_at": "2026-11-10T06:30:00Z",
        "country": "IN",
        "currency": "INR",
        "category": "Earnings",
        "event_name": "Reliance Industries Q3 FY27 Earnings",
        "impact_level": "High",
        "actual": "",
        "forecast": "12400.00",
        "prior": "11850.00",
        "period_label": "Q3 FY27",
    },
    {
        "instrument": "NSE:TCS-EQ",
        "scheduled_at": "2026-11-12T06:30:00Z",
        "country": "IN",
        "currency": "INR",
        "category": "Earnings",
        "event_name": "TCS Q3 FY27 Earnings",
        "impact_level": "High",
        "actual": "",
        "forecast": "13500.00",
        "prior": "12900.00",
        "period_label": "Q3 FY27",
    },
    {
        "instrument": "NSE:HDFCBANK-EQ",
        "scheduled_at": "2026-11-14T06:30:00Z",
        "country": "IN",
        "currency": "INR",
        "category": "Dividends",
        "event_name": "HDFC Bank Interim Dividend",
        "impact_level": "Medium",
        "actual": "",
        "forecast": "15.00",
        "prior": "14.00",
        "period_label": "FY27",
    },
    {
        "instrument": "NSE:INFY-EQ",
        "scheduled_at": "2026-11-15T06:30:00Z",
        "country": "IN",
        "currency": "INR",
        "category": "Splits",
        "event_name": "Infosys Stock Split 1:2",
        "impact_level": "Medium",
        "actual": "",
        "forecast": "",
        "prior": "",
        "period_label": "FY27",
    },
    {
        "instrument": None,
        "scheduled_at": "2026-11-16T06:00:00Z",
        "country": "US",
        "currency": "USD",
        "category": "Economic",
        "event_name": "US Retail Sales MoM",
        "impact_level": "High",
        "actual": "",
        "forecast": "0.40",
        "prior": "0.20",
        "period_label": "Oct",
    },
    {
        "instrument": None,
        "scheduled_at": "2026-11-17T13:30:00Z",
        "country": "US",
        "currency": "USD",
        "category": "Economic",
        "event_name": "Fed [Name] Speech",
        "impact_level": "Low",
        "actual": "",
        "forecast": "",
        "prior": "",
        "period_label": "",
    },
    {
        "instrument": "NSE:IPO-2026-EQ",
        "scheduled_at": "2026-11-20T06:00:00Z",
        "country": "IN",
        "currency": "INR",
        "category": "IPO",
        "event_name": "NewCo IPO Subscription Opening",
        "impact_level": "High",
        "actual": "",
        "forecast": "",
        "prior": "",
        "period_label": "Nov/20",
    },
]


@dataclass(frozen=True, slots=True)
class CalendarRow:
    """One raw calendar row with exact ``Decimal`` values."""

    instrument: str | None
    scheduled_at: datetime
    country: str
    currency: str
    category: str
    event_name: str
    impact_level: str
    actual: Decimal | None
    forecast: Decimal | None
    prior: Decimal | None
    period_label: str | None


def _decimal_or_none(text: str) -> Decimal | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception as exc:
        raise ValueError(f"invalid calendar numeric value: {text!r}") from exc


def _scheduled_at(text: str) -> datetime:
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def parse_calendar(text: str) -> list[CalendarRow]:
    """Parse raw calendar CSV text into typed rows (header is mandatory)."""
    reader = csv.DictReader(line for line in text.splitlines() if line.strip())
    if reader.fieldnames is None or not reader.fieldnames:
        raise ValueError("calendar data is empty or missing a header")
    rows: list[CalendarRow] = []
    for raw in reader:
        if not any(raw.values()):
            continue
        category = raw["category"].strip()
        if category not in _VALID_CATEGORIES:
            raise ValueError(
                f"invalid calendar category {category!r}; must be one of {_VALID_CATEGORIES}"
            )
        impact_level = raw["impact_level"].strip()
        if impact_level not in _VALID_IMPACT_LEVELS:
            raise ValueError(
                f"invalid impact_level {impact_level!r}; must be one of {_VALID_IMPACT_LEVELS}"
            )
        rows.append(
            CalendarRow(
                instrument=raw.get("instrument", "").strip() or None,
                scheduled_at=_scheduled_at(raw["scheduled_at"]),
                country=raw["country"].strip(),
                currency=raw["currency"].strip(),
                category=category,
                event_name=raw["event_name"].strip(),
                impact_level=impact_level,
                actual=_decimal_or_none(raw.get("actual", "")),
                forecast=_decimal_or_none(raw.get("forecast", "")),
                prior=_decimal_or_none(raw.get("prior", "")),
                period_label=raw.get("period_label", "").strip() or None,
            )
        )
    return rows


def stubbed_calendar_rows() -> list[CalendarRow]:
    """Return the bundled stubbed calendar rows (no external source)."""
    return [
        CalendarRow(
            instrument=r["instrument"],
            scheduled_at=_scheduled_at(cast(str, r["scheduled_at"])),
            country=cast(str, r["country"]),
            currency=cast(str, r["currency"]),
            category=cast(str, r["category"]),
            event_name=cast(str, r["event_name"]),
            impact_level=cast(str, r["impact_level"]),
            actual=_decimal_or_none(cast(str, r["actual"])),
            forecast=_decimal_or_none(cast(str, r["forecast"])),
            prior=_decimal_or_none(cast(str, r["prior"])),
            period_label=cast(str, r["period_label"]),
        )
        for r in _STUBBED_ROWS
    ]


def read_calendar(path: str | Path) -> list[CalendarRow]:
    """Read and parse a calendar CSV file from disk."""
    with open(path, encoding="utf-8") as handle:
        return parse_calendar(handle.read())


def rows_to_events(rows: list[CalendarRow]) -> list[CalendarEvent]:
    """Map parsed calendar rows onto domain events."""
    return [
        CalendarEvent(
            instrument=row.instrument,
            scheduled_at=row.scheduled_at,
            country=row.country,
            currency=row.currency,
            category=row.category,
            event_name=row.event_name,
            impact_level=row.impact_level,
            actual=row.actual,
            forecast=row.forecast,
            prior=row.prior,
            period_label=row.period_label,
        )
        for row in rows
    ]


__all__ = [
    "CalendarRow",
    "parse_calendar",
    "read_calendar",
    "rows_to_events",
    "stubbed_calendar_rows",
]
