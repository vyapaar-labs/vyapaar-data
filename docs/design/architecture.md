# `vyapaar-data` — DDD Architecture & Financial Lakehouse Bounded Context

## 1. Bounded Context & Responsibility
`vyapaar-data` (Tier 6A, ported from `honba-data`) is the **Point-in-Time Financial Lakehouse & Corporate Actions Bounded Context** powered by Python 3.11+, DuckDB, Polars, and PyArrow.

## 2. Hexagonal Architecture (`vyapaar_data/`)
* `domain/`: Pure value objects for corporate actions (`Split`, `Bonus`, `Dividend`, `Rights`), point-in-time `FundamentalRecord` (`filing_date` vs `period_end_date` to prevent look-ahead bias), and `CoverageLedger`.
* `ports/`: `FundamentalsRepository`, `CorporateActionsRepository`, `CatalogRepository`, `DataService` protocol.
* `adapters/`: `DuckDbFundamentalsStore`, Hive-partitioned Parquet `Decimal128(18,4)` catalog reader/writer.
* `providers/`: NSE Bhavcopy, Screener/fundamental ingestion sidecars.
* `service/`: Unified `VyapaarDataService` facade.
