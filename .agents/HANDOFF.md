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

## Immediate Next Step
* `vyapaar-ui-web`: Proceed with gap 0011 (wire sparklines to `GET /bars/{id}`) against verified
  catalog data; for plan 0007 / gap 0024 (Risk tab), either use option (b) local equity curve or
  schedule index ingestion in `vyapaar-data`.
* Tier 6B: `vyapaar-adapters` (broker ACL SDK with entry points and paper/mock harness).

## Operating Invariants
* Zero floats: `decimal.Decimal` + `DECIMAL128(18,4)` everywhere in financial columns.
* Tests live in `tests/` only (parallel test directory rule).
