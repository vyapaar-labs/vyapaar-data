"""Calendar ingestion (gap 0001): domain, stubbed provider, DuckDB store, and
LakehouseCalendarReader service.

Calendar data is stubbed/hardcoded while an external calendar data
source/vendor decision remains pending (see docs/gaps/0012-calendar-stubbed-data.md).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import polars as pl

from vyapaar_data import (
    CalendarEvent,
    CalendarReader,
    CalendarRepository,
    DuckDbCalendarStore,
    LakehouseCalendarReader,
    rows_to_events,
    stubbed_calendar_rows,
)
from vyapaar_data.providers.calendar import parse_calendar


def test_calendar_event_validation() -> None:
    evt = CalendarEvent(
        instrument="NSE:RELIANCE-EQ",
        scheduled_at=datetime(2026, 11, 10, 6, 30, tzinfo=UTC),
        country="IN",
        currency="INR",
        category="Earnings",
        event_name="Reliance Industries Q3 FY27 Earnings",
        impact_level="High",
        actual=None,
        forecast=Decimal("12400.00"),
        prior=Decimal("11850.00"),
        period_label="Q3 FY27",
    )
    assert evt.instrument == "NSE:RELIANCE-EQ"
    assert evt.category == "Earnings"
    assert evt.impact_level == "High"
    assert evt.actual is None
    assert evt.forecast == Decimal("12400.00")
    assert evt.prior == Decimal("11850.00")


def test_calendar_event_rejects_bad_category() -> None:
    try:
        CalendarEvent(
            instrument=None,
            scheduled_at=datetime(2026, 11, 10, 6, 30, tzinfo=UTC),
            country="IN",
            currency="INR",
            category="NotACategory",
            event_name="X",
            impact_level="High",
            actual=None,
            forecast=None,
            prior=None,
            period_label=None,
        )
    except ValueError as exc:
        assert "category" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError for bad category")


def test_calendar_event_rejects_naive_timestamp() -> None:
    try:
        CalendarEvent(
            instrument=None,
            scheduled_at=datetime(2026, 11, 10, 6, 30),  # naive
            country="IN",
            currency="INR",
            category="Economic",
            event_name="X",
            impact_level="Low",
            actual=None,
            forecast=None,
            prior=None,
            period_label=None,
        )
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError for naive timestamp")


def test_stubbed_calendar_rows_known_events() -> None:
    rows = stubbed_calendar_rows()
    assert len(rows) == 7
    categories = {r.category for r in rows}
    assert categories == {"Economic", "Earnings", "Dividends", "Splits", "IPO"}
    impacts = {r.impact_level for r in rows}
    assert impacts == {"High", "Medium", "Low"}
    # At least one macro event with no instrument.
    macro = [r for r in rows if r.instrument is None]
    assert len(macro) >= 1


def test_rows_to_events_round_trip() -> None:
    rows = stubbed_calendar_rows()
    events = rows_to_events(rows)
    assert len(events) == len(rows)
    for row, evt in zip(rows, events, strict=True):
        assert evt.instrument == row.instrument
        assert evt.scheduled_at == row.scheduled_at
        assert evt.category == row.category
        assert evt.event_name == row.event_name
        assert evt.impact_level == row.impact_level
        assert evt.actual == row.actual
        assert evt.forecast == row.forecast


def test_parse_calendar_csv() -> None:
    text = (
        "instrument,scheduled_at,country,currency,category,event_name,"
        "impact_level,actual,forecast,prior,period_label\n"
        "NSE:RELIANCE-EQ,2026-11-10T06:30:00Z,IN,INR,Earnings,"
        "Reliance Q3,High,,12400.00,11850.00,Q3 FY27\n"
    )
    rows = parse_calendar(text)
    assert len(rows) == 1
    assert rows[0].instrument == "NSE:RELIANCE-EQ"
    assert rows[0].category == "Earnings"
    assert rows[0].forecast == Decimal("12400.00")
    assert rows[0].actual is None


def test_calendar_store_upsert_and_query() -> None:
    store = DuckDbCalendarStore(":memory:")
    events = rows_to_events(stubbed_calendar_rows())
    for evt in events:
        store.upsert(evt)

    all_events = store.query()
    assert len(all_events) == 7

    econ = store.query(category="Economic")
    assert len(econ) == 2
    assert all(e.category == "Economic" for e in econ)

    reli = store.query(instrument="NSE:RELIANCE-EQ")
    assert len(reli) == 1
    assert reli[0].instrument == "NSE:RELIANCE-EQ"

    # Date window filter.
    nov10 = date(2026, 11, 10)
    nov14 = date(2026, 11, 14)
    window = store.query(start_date=nov10, end_date=nov14)
    assert all(nov10 <= e.scheduled_at.date() <= nov14 for e in window)

    store.close()


def test_calendar_store_upsert_is_idempotent() -> None:
    store = DuckDbCalendarStore(":memory:")
    evt = CalendarEvent(
        instrument="NSE:RELIANCE-EQ",
        scheduled_at=datetime(2026, 11, 10, 6, 30, tzinfo=UTC),
        country="IN",
        currency="INR",
        category="Earnings",
        event_name="Reliance Q3",
        impact_level="High",
        actual=None,
        forecast=Decimal("12400.00"),
        prior=Decimal("11850.00"),
        period_label="Q3 FY27",
    )
    store.upsert(evt)
    store.upsert(
        CalendarEvent(
            instrument="NSE:RELIANCE-EQ",
            scheduled_at=datetime(2026, 11, 10, 6, 30, tzinfo=UTC),
            country="IN",
            currency="INR",
            category="Earnings",
            event_name="Reliance Q3",
            impact_level="High",
            actual=Decimal("12500.00"),  # updated actual
            forecast=Decimal("12400.00"),
            prior=Decimal("11850.00"),
            period_label="Q3 FY27",
        )
    )
    rows = store.query(instrument="NSE:RELIANCE-EQ")
    assert len(rows) == 1
    assert rows[0].actual == Decimal("12500.00")
    store.close()


def test_lakehouse_calendar_reader_frame() -> None:
    store = DuckDbCalendarStore(":memory:")
    events = rows_to_events(stubbed_calendar_rows())
    for evt in events:
        store.upsert(evt)
    reader = LakehouseCalendarReader(store)

    frame = reader.get_calendar()
    assert frame.columns == [
        "instrument",
        "scheduled_at",
        "country",
        "currency",
        "category",
        "event_name",
        "impact_level",
        "actual",
        "forecast",
        "prior",
        "period_label",
    ]
    assert len(frame) == 7
    assert frame["actual"].dtype == pl.Decimal(18, 4)
    assert frame["forecast"].dtype == pl.Decimal(18, 4)
    assert frame["prior"].dtype == pl.Decimal(18, 4)

    # Empty when no match.
    empty = reader.get_calendar(category="DoesNotExist")
    assert len(empty) == 0
    assert empty.columns == frame.columns

    store.close()


def test_calendar_reader_implements_protocol() -> None:
    store = DuckDbCalendarStore(":memory:")
    reader = LakehouseCalendarReader(store)
    assert isinstance(reader, CalendarReader)
    assert isinstance(store, CalendarRepository)
    store.close()


def test_calendar_values_are_decimal_never_float() -> None:
    store = DuckDbCalendarStore(":memory:")
    events = rows_to_events(stubbed_calendar_rows())
    for evt in events:
        store.upsert(evt)
    for evt in store.query():
        for field in ("actual", "forecast", "prior"):
            val = getattr(evt, field)
            assert val is None or isinstance(val, Decimal)
    store.close()
