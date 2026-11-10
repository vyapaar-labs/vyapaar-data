# `vyapaar-data` — Inter-Agent Handoff

## Phase / Slice Status
* **Tier 6A (COMPLETE)**: Implemented Point-in-Time Financial Lakehouse bounded context.
* Package `vyapaar_data/` with hexagonal layout:
  * `domain/`: `Split`, `Bonus`, `Dividend`, `Rights` (frozen, self-validating, `Decimal`-exact),
    `FundamentalRecord` (filing/period dates with look-ahead guard), `CoverageLedger` (gap discovery),
    `InstrumentCoverage`, `CoverageReport`.
  * `ports/`: `CorporateActionsRepository`, `FundamentalsRepository`, `CatalogRepository`,
    `DataService` protocols + canonical `BAR_SCHEMA`.
  * `adapters/`: `DuckDbFundamentalsStore`, `DuckDbCorporateActionsStore`,
    `ParquetCatalog` (supporting both Hive layout and runtime `{root}/catalog/{TF}/{EXCHANGE}/{SYMBOL}/*.parquet`
    layouts with exact `DECIMAL128(18,4)` prices).
  * `providers/`: NSE `cm` bhavcopy parser + `rows_to_bars` mapper.
  * `service/`: `VyapaarDataService.adjusted_history()`, `coverage()`, `report_coverage()`.
  * `cli/`: `python -m vyapaar_data.cli` coverage reporting tool (`vyapaar-coverage`).
* Zone 3 configs: `configs/catalog.toml`. CI: `.github/workflows/ci.yml`.
- `docs/migration-guide.md` decimated: historical migration map moved to
  `docs/design/code-migration-map.md`; verification commands moved to
  `docs/roadmap/migration-verification.md`; original `migration-guide.md` removed.
* **Gap 0001 (CLOSED)**: Ran coverage-ledger reporting for `vyapaar-ui-web` instruments. Confirmed
  equity coverage (2014–2026, >3,150 bars each) in the deployed lakehouse catalog (`RELIANCE`,
  `TCS`, `HDFCBANK`, `INFY`, `ICICIBANK`), unblocking gap 0011 sparklines. Identified that benchmark
  indices (`NIFTY50`) are missing from cash bhavcopies, requiring index ingestion before plan 0007
  option (a) can use real benchmark bars.

## Decisions & Discoveries
* `pyproject.toml`: Made `vyapaar>=0.1.0` optional under `[project.optional-dependencies].native`
  (consistent with `_compat.py` runtime fallback); added console script `vyapaar-coverage`.
* `ParquetCatalog`: Seamlessly reads both Hive layout (`{root}/<instrument>/year=YYYY/*.parquet`) and
  the runtime catalog layout (`{root}/catalog/{TF}/{EXCHANGE}/{SYMBOL}/*.parquet`), normalizing
  both nanosecond `int64` and temporal timestamps into microsecond UTC datetimes, and float/double
  prices into canonical `DECIMAL(18, 4)`.
* NSE cash equity bhavcopies (`sec_bhavdata_full_*.csv`) do not contain benchmark index levels
  (`NIFTY 50`), which live in separate index bhavcopies (`ind_close_all_*.csv`).
* **Gap 0001 (calendar) implemented with stubbed data** — `CalendarEvent` domain,
  `CalendarRepository`/`CalendarReader` ports, `DuckDbCalendarStore` adapter,
  `LakehouseCalendarReader` service, stubbed CSV provider (`stubbed_calendar_rows`).
  Stubbed data is a stopgap pending an external vendor decision — tracked by
  `docs/gaps/0003-calendar-stubbed-data.md`. Tests in `tests/test_calendar.py`.
* **Gap 0002 (symbol profile) implemented with yfinance** — `SymbolProfile` domain,
  `ProfileRepository`/`ProfileReader` ports, `DuckDbProfileStore` adapter,
  `LakehouseProfileReader` service, yfinance provider (`fetch_symbol_profiles`,
  degrades gracefully when yfinance is absent). Tests in `tests/test_profile.py`.

## What was implemented (gaps 0001 & 0002)
- **Calendar ingestion** (gap 0001): `CalendarEvent` domain value object
  (`vyapaar_data/domain/calendar.py`); `CalendarRow`/`parse_calendar` CSV provider
  (`vyapaar_data/providers/calendar.py`); `CalendarRepository` port +
  `DuckDbCalendarStore` adapter (`vyapaar_data/adapters/duckdb_store.py`);
  `CalendarReader` port + `LakehouseCalendarReader` service
  (`vyapaar_data/service/calendar_reader.py`). Data is stubbed/hardcoded pending
  an external vendor decision (see docs/gaps/0003-calendar-stubbed-data.md).
- **Symbol profile ingestion** (gap 0002): `SymbolProfile` domain value object
  (`vyapaar_data/domain/profile.py`); `ProfileRow`/`fetch_symbol_profiles` yfinance
  provider (`vyapaar_data/providers/profile.py`); `ProfileRepository` port +
  `DuckDbProfileStore` adapter (`vyapaar_data/adapters/duckdb_store.py`);
  `ProfileReader` port + `LakehouseProfileReader` service
  (`vyapaar_data/service/profile_reader.py`). yfinance is optional; degrades
  gracefully when absent.
- **Tests**: 18 new tests (`tests/test_calendar.py` 10, `tests/test_profile.py` 8).
- Full suite `pytest -q`: **100 passed, 0 failed**; `ruff check` + `ruff format --check`
  clean; `mypy` clean on new files.

## What was implemented (plan 0001)
- **Analytical data-feed ports** (`vyapaar_data/ports/data_feeds.py`): `MarketReader`
  (`get_quote`, `get_candles`, `get_returns`, `get_indicators`), `ScreenerReader`
  (`execute_screen`), `MacroReader` (`get_series`), `ReferenceExporter` (`export`/`resolve`
  emitting `$vyapaar/ref/<uuid>` URIs), plus screener domain types
  (`ScreenQuery`, `ScreenCondition`, `ComparisonOp`).
- **Implementations** (`vyapaar_data/service/`): `LakehouseMarketReader` backed by the
  Parquet catalog + `VyapaarDataService`; `VectorizedScreener` (gt/lt/gte/lte/eq and
  crosses_above/crosses_below vs literal or field, order_by + limit);
  `InMemoryReferenceExporter`; `PythonMacroReader` (empty canonical frame — stub,
  see open gap 0002).
- **Tests**: 16 new tests in `tests/test_data_feeds.py`; full suite `pytest -q`: 45 passed,
  0 failed; `ruff check` + `ruff format --check` clean.

## What was implemented (plan 0002 / gaps 0002 & 0003)
- **Macro series ingestion** (gap 0002 closed): `MacroObservation` domain value object
  (`vyapaar_data/domain/macro.py`); `MacroRow`/`parse_macro` CSV provider
  (`vyapaar_data/providers/macro.py`); `MacroSeriesRepository` port +
  `DuckDbMacroStore` adapter (`vyapaar_data/adapters/macro_store.py`);
  `PythonMacroReader.get_series` now reads from the repository with as-of semantics and
  returns exact `Decimal(18,4)` Polars frames (`vyapaar_data/service/macro_reader.py`).
- **Filings ingestion** (gap 0003 closed): `Filing`/`FilingType` domain value objects
  (`vyapaar_data/domain/filings.py`); `FilingRow`/`parse_filings` CSV provider
  (`vyapaar_data/providers/filings.py`); `FilingsRepository` port +
  `DuckDbFilingsStore` adapter (`vyapaar_data/adapters/filings_store.py`);
  `FilingsReader` port + `LakehouseFilingsReader` service
  (`vyapaar_data/service/filings_reader.py`).
- **Tests**: 18 new tests (`tests/test_macro.py` 9, `tests/test_filings.py` 9).
- Full suite `pytest -q`: **63 passed, 0 failed**; `ruff check` + `ruff format --check`
  clean. Both gap docs moved to Closed Gaps; plan 0002 moved to Implemented Plans.

## Immediate Next Step
* `vyapaar-ui-web`: Proceed with gap 0011 (wire sparklines to `GET /bars/{id}`) against verified
  catalog data; for plan 0007 / gap 0024 (Risk tab), either use option (b) local equity curve or
  schedule index ingestion in `vyapaar-data`.
* Tier 6B: `vyapaar-adapters` (broker ACL SDK with entry points and paper/mock harness).

## Operating Invariants
* Zero floats: `decimal.Decimal` + `DECIMAL128(18,4)` everywhere in financial columns.
* Tests live in `tests/` only (parallel test directory rule).
