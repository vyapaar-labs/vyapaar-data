# 0001 — Economic/earnings/dividends/splits/IPO calendar ingestion

**Status**: open

## What's stubbed or hardcoded

This repo currently has no economic/earnings/dividends/splits/IPO calendar data
source at all. There is no scheduled-events feed, no reader port, and no
Parquet catalog entry for this category.

This is distinct from the already-closed gaps 0002 (`PythonMacroReader` /
macro series ingestion) and 0003 (filings ingestion / expanded economic series
breadth, see `docs/gaps/README.md`'s Closed gaps table). Those two closed gaps
cover point-in-time macro time series (e.g. CPI, GDP prints as historical
series) and SEC-style filings — backward-looking reference data. This gap is
a forward-looking, multi-category *scheduled events calendar*: a board of
upcoming (and recently-released) economic releases, earnings reports,
dividend/split corporate actions, and IPOs, each with its own release
datetime, impact level, and actual/forecast/prior values. No existing reader
or ingestion path in this repo produces that shape.

## Why

`vyapaar-ui-web` is planning a Calendar workspace tab plus a right-dock
calendar panel (its own `docs/plans/0011-vela-journal-calendar-reports-domain-model.md`),
and `vyapaar-runtime` is planning a `/market-data/calendar` REST endpoint to
serve it (its own `docs/plans/0003-trade-journal-and-market-reference-rest-endpoints.md`).
Both consumers need this repo to be the actual data source for calendar
events, per this workspace's gap-tracking rule (`.agents/rules/gap-tracking.md`
§5) that a stub's root cause gets filed in the provider repo — not stubbed
silently in the consuming repo.

The shapes below were reverse-engineered live from vela.luxalgo.com's own
`GET /api/markets/calendar?from=...&to=...` endpoint and its rendered
Calendar tab (observed 2026-11-09), to document the target shape concretely:

- A 5-weekday board of time-stamped events, each with: time, country
  flag/code, event name (e.g. "Westpac Consumer Confidence Change", "Retail
  Sales MoM", "GDP Growth Rate QoQ", "Fed [Name] Speech"), impact level
  (observed value: "High", shown as a colored badge and a color-coded
  left-edge row bar), Actual/Forecast/Prior numeric values (color-coded green
  when actual beats forecast, red when it misses), a period label (e.g.
  "Oct", "Q3", "Nov/06"), and category — the UI's own filter pills are
  `Economic` / `Earnings` / `Dividends` / `Splits` / `IPO`, i.e. this is a
  multi-category calendar despite this gap's title saying "economic
  calendar".
- A per-event detail view additionally shows: a countdown ("In 6h 04m"),
  currency code (e.g. "AUD"), a "LAST 13 RELEASES" historical actual-vs-forecast
  bar chart, and a "MARKETS IT MOVES" list of 2-3 affected symbol/currency
  tickers with a one-line note.

## How to close it

Ingest a multi-category scheduled-events feed (economic releases, earnings,
dividends, splits, IPOs) with per-event fields: scheduled datetime,
country/currency, category, event name, impact level, actual/forecast/prior
values once released, period label, and (for earnings specifically) the
affected instrument/symbol.

This needs an external data source/vendor decision that has **not** been made
yet — flagged here as open, no vendor name should be invented or assumed.

Once a source is chosen, this should land in this repo's existing
lakehouse/catalog pattern (the same "Parquet catalog" architecture already
established for the macro-series and filings gaps this repo closed — see the
Closed gaps table in `docs/gaps/README.md`), so `vyapaar-runtime` can read it
via the same kind of reader port those closed gaps used. `MacroReader` and
`FilingsReader` (from this repo's own closed gaps 0002/0003) are the
precedent pattern — a new `CalendarReader` port in the same shape is the
natural next port. No code should be written against this gap document; it
is documentation only, recording the decision point and target shape.
