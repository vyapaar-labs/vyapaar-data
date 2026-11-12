# 0010 — Economic/earnings/dividends/splits/IPO calendar ingestion (real source)

**Status**: open

## What's stubbed or hardcoded

The calendar **reader, port, and storage are implemented**, but they are backed by
bundled, hardcoded placeholder events rather than a live external source:

- `vyapaar_data/domain/calendar.py::CalendarEvent` — the calendar domain value object
  (scheduled datetime, country/currency, category, event name, impact level,
  actual/forecast/prior, period label, affected instrument).
- `vyapaar_data/ports/repositories.py::CalendarRepository` and
  `vyapaar_data/ports/data_feeds.py::CalendarReader` — storage and read ports.
- `vyapaar_data/adapters/duckdb_store.py::DuckDbCalendarStore` — DuckDB storage adapter.
- `vyapaar_data/service/calendar_reader.py::LakehouseCalendarReader` — read service
  returning exact-`Decimal` Polars frames.
- `vyapaar_data/providers/calendar.py::stubbed_calendar_rows()` — 7 illustrative
  `CalendarRow`s reverse-engineered from the vela.luxalgo.com calendar shape.
- Tests in `tests/test_calendar.py`.

What remains open is the **real vendor data source**: no scheduled-events feed has been
selected, so no live ingestion path populates the store. The placeholder data is tracked
separately by [0012](0012-calendar-stubbed-data.md).

This is distinct from the already-closed gaps 0002 (`PythonMacroReader` / macro series
ingestion) and 0003 (filings ingestion / expanded economic series breadth, see
`docs/gaps/README.md`'s Closed gaps table). Those two closed gaps cover point-in-time macro
time series (e.g. CPI, GDP prints as historical series) and SEC-style filings —
backward-looking reference data. This gap is a forward-looking, multi-category *scheduled
events calendar*: a board of upcoming (and recently-released) economic releases, earnings
reports, dividend/split corporate actions, and IPOs, each with its own release datetime,
impact level, and actual/forecast/prior values.

## Why

`vyapaar-ui-web` is planning a Calendar workspace tab plus a right-dock calendar panel (its
own `docs/plans/0011-vela-journal-calendar-reports-domain-model.md`), and `vyapaar-runtime`
is planning a `/market-data/calendar` REST endpoint to serve it (its own
`docs/plans/0003-trade-journal-and-market-reference-rest-endpoints.md`). Both consumers
need this repo to be the actual data source for calendar events, per this workspace's
gap-tracking rule (`.agents/rules/gap-tracking.md` §5) that a stub's root cause gets filed
in the provider repo — not stubbed silently in the consuming repo.

## How to close it

1. Select a concrete external calendar data source/vendor (economic releases, earnings,
   dividends, splits, IPOs) — **no vendor name should be invented or assumed**.
2. Replace `stubbed_calendar_rows()` with a live ingestion path through the existing
   `CalendarRepository`/`DuckDbCalendarStore` (the store side needs no change).
3. Close [0012](0012-calendar-stubbed-data.md) once the placeholder events are removed.

This gap is a prerequisite for `vyapaar-runtime` plan 0003 Phase 3
(`/market-data/calendar` REST endpoint).
