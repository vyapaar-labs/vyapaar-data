# 0012 — Calendar data stubbed pending external source decision

**Status**: open (implementation uses stubbed/hardcoded data)

## What's stubbed or hardcoded

The calendar reader (`gap 0010`) is implemented using a bundled, hardcoded set of calendar
events rather than a live external source:

- `vyapaar_data/providers/calendar.py::stubbed_calendar_rows()` returns 7 illustrative
  `CalendarRow`s (earnings, dividends, splits, IPO, and macroeconomic events)
  reverse-engineered from the shape described in
  `docs/gaps/0010-economic-calendar-ingestion.md`.
- The stubbed events are loaded through the real pipeline (`parse_calendar`,
  `rows_to_events`, `CalendarRepository`, `DuckDbCalendarStore`,
  `LakehouseCalendarReader`), so only the provider is placeholder.

This is placeholder data: no real vendor data is asserted, and the stubbed events must be
replaced once a concrete calendar data source is selected.

## Why

Per `docs/gaps/0010-economic-calendar-ingestion.md`, an external data source/vendor
decision had **not** been made, and no vendor name was to be invented or assumed. This gap
records that stubbed/hardcoded data is being used as a stopgap so the `CalendarReader` port
has data to serve while the upstream decision remains pending, per
`.agents/rules/gap-tracking.md` §2 (file a gap doc whenever stubbed/hardcoded data is used).

## How to close it

1. Select a concrete external calendar data source/vendor (replace the
   `stubbed_calendar_rows()` provider with a live ingestion path).
2. Remove `docs/gaps/0012-calendar-stubbed-data.md` and update `docs/gaps/README.md` once
   real ingestion lands.

This gap is a prerequisite for `vyapaar-runtime` plan 0003 Phase 3
(`/market-data/calendar` REST endpoint).
