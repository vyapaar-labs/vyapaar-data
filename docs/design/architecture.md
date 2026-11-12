# `vyapaar-data` — DDD Architecture & Financial Lakehouse Bounded Context

## 1. Bounded Context & Responsibility

`vyapaar-data` (Tier 6A, ported from `honba-data`) is the **Point-in-Time Financial
Lakehouse & Corporate Actions Bounded Context** powered by Python 3.11+, DuckDB, Polars,
and PyArrow. It is the canonical source of historical and reference data for the Vyapaar
Labs ecosystem:

* **Corporate actions** — splits, bonuses, dividends, and rights issues as frozen,
  self-validating `Decimal` value objects with exact back-adjustment math.
* **Point-in-time fundamentals** — every `FundamentalRecord` carries both a
  `period_end_date` and a `filing_date`; as-of queries only surface facts that were
  publicly filed by the query date (no look-ahead bias).
* **Coverage ledgers** — track data availability across instruments, intervals, and date
  ranges and report uncovered gaps.
* **Parquet catalog** — Hive-partitioned columnar storage with `DECIMAL128(18,4)` pricing
  columns (zero `float` in any financial column).
* **Macro series, filings, calendar events, and symbol profiles** — point-in-time
  reference datasets behind reader ports.

## 2. Hexagonal Architecture (`vyapaar_data/`)

### 2.1 `domain/` — pure value objects (zero I/O)

| Module | Types |
|--------|-------|
| `corporate_actions.py` | `CorporateActionType`, `Split`, `Bonus`, `Dividend`, `Rights`, `CorporateActionRecord`, `to_record`/`from_record` |
| `fundamentals.py` | `FundamentalRecord` (filing-date vs period-end-date look-ahead guard) |
| `coverage.py` | `CoverageEntry`, `CoverageLedger`, `InstrumentCoverage`, `CoverageReport` |
| `filings.py` | `Filing`, `FilingType` |
| `macro.py` | `MacroObservation` |
| `calendar.py` | `CalendarEvent` (scheduled datetime, country/currency, category, impact, actual/forecast/prior) |
| `profile.py` | `SymbolProfile` (mirrors the vela.luxalgo.com symbol-profile contract; `Decimal` monetary fields) |

### 2.2 `ports/` — protocols (service layer depends on these, never on concrete storage)

| Module | Ports |
|--------|-------|
| `repositories.py` | `CorporateActionsRepository`, `FundamentalsRepository`, `CatalogRepository`, `MacroSeriesRepository`, `FilingsRepository`, `CalendarRepository`, `ProfileRepository`, `DataService`, plus canonical `BAR_SCHEMA` (all financial columns `Decimal(18,4)`) |
| `data_feeds.py` | Read ports `MarketReader`, `ScreenerReader`, `MacroReader`, `FilingsReader`, `ReferenceExporter`, `CalendarReader`, `ProfileReader`, plus screener domain types (`ScreenQuery`, `ScreenCondition`, `ComparisonOp`, `ScreenValue`, `ScreenResult`) |

### 2.3 `adapters/` — storage implementations

| Module | Adapters |
|--------|----------|
| `duckdb_store.py` | `DuckDbFundamentalsStore`, `DuckDbCalendarStore`, `DuckDbProfileStore`, `DuckDbCorporateActionsStore` |
| `filings_store.py` | `DuckDbFilingsStore` |
| `macro_store.py` | `DuckDbMacroStore` |
| `parquet_catalog.py` | `ParquetCatalog` (Hive layout + runtime `{root}/catalog/{TF}/{EXCHANGE}/{SYMBOL}` layout; `arrow_schema()`) |

### 2.4 `providers/` — ingestion

| Module | Provider |
|--------|----------|
| `bhavcopy.py` | NSE `cm` bhavcopy CSV parser (`parse_bhavcopy`, `read_bhavcopy`, `rows_to_bars`) |
| `calendar.py` | Calendar CSV parser + `stubbed_calendar_rows()` (placeholder data — gap 0012) |
| `filings.py` | Filings CSV parser (`parse_filings`, `read_filings`, `rows_to_filings`) |
| `macro.py` | Macro CSV parser (`parse_macro`, `read_macro`, `rows_to_observations`) |
| `profile.py` | yfinance-backed `fetch_symbol_profiles` (optional dependency; degrades gracefully) |

### 2.5 `service/` — read services & facade

| Module | Service |
|--------|---------|
| `data_service.py` | `VyapaarDataService` — `adjusted_history()`, `as_of_fundamentals()`, `coverage()`, `report_coverage()` |
| `market_reader.py` | `LakehouseMarketReader` — `get_quote`, `get_candles`, `get_returns`, `get_indicators` |
| `screener.py` | `VectorizedScreener` — gt/lt/gte/lte/eq and crosses_above/crosses_below |
| `macro_reader.py` | `PythonMacroReader` — `get_series` (as-of semantics, exact `Decimal` frames) |
| `filings_reader.py` | `LakehouseFilingsReader` — `list_filings` |
| `calendar_reader.py` | `LakehouseCalendarReader` — `get_calendar` |
| `profile_reader.py` | `LakehouseProfileReader` — `get_profile`/`get_profiles` |
| `reference_exporter.py` | `InMemoryReferenceExporter` — `$vyapaar/ref/<uuid>` URIs |

### 2.6 `cli/`

`python -m vyapaar_data.cli` / console script `vyapaar-coverage` — coverage-ledger
reporting against a catalog directory (`vyapaar_data/cli/coverage.py`).

## 3. Point-in-Time & Back-Adjustment Semantics

`VyapaarDataService.adjusted_history()` restates raw prices and volumes to the *current*
basis: for every bar at date `d`, all actions whose ex-date is strictly after `d` are
chained in chronological order. `as_of_fundamentals()` returns only records filed on or
before the query date. This is the standard total-return back-adjustment used by Indian
backtests and keeps research free of look-ahead bias.

## 4. Zero-Floats Policy

All prices, adjusted payouts, split ratios, fundamental values, macro observations,
calendar actual/forecast/prior values, and profile monetary fields are `decimal.Decimal`
end-to-end. Columnar storage uses Arrow `decimal128(18,4)`; there is no `f32`/`f64` in any
financial path.

## 5. Dependency Rules & Consumers

* `vyapaar_data` depends only on standard Python libraries, DuckDB, Polars, PyArrow, and
  Pydantic. The `vyapaar` wheel is optional (`[project.optional-dependencies].native`).
* Downstream Rust consumers (`vyapaar-runtime`) read through `data_feeds.py` ports where a
  Rust bridge exists; datasets that are Python-only today (filings, corporate actions) are
  tracked by gaps 0007 and 0008.

## 6. Related

* `docs/design/code-migration-map.md` — historical `honba-data → vyapaar-data` migration.
* `docs/gaps/README.md` / `docs/plans/README.md` — open ingestion/bridge work and plans.
* `README.md` — package overview, quick start, and development commands.
