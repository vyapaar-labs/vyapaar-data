# `vyapaar-data` — Inter-Agent Handoff

## Phase / Slice Status
* **Tier 6A (COMPLETE)**: Implemented the Point-in-Time Financial Lakehouse
  bounded context from the sub-guide contracts (source `honba-data` unavailable
  in this environment; implemented fresh).
* Package `vyapaar_data/` with hexagonal layout:
  * `domain/`: `Split`, `Bonus`, `Dividend`, `Rights` (frozen, self-validating,
    `Decimal`-exact corporate actions), `FundamentalRecord` (filing/period
    dates with look-ahead guard), `CoverageLedger` (gap discovery).
  * `ports/`: `CorporateActionsRepository`, `FundamentalsRepository`,
    `CatalogRepository`, `DataService` protocols + canonical `BAR_SCHEMA`.
  * `adapters/`: `DuckDbFundamentalsStore`, `DuckDbCorporateActionsStore`,
    `ParquetCatalog` (Hive-partitioned, `DECIMAL128(18,4)` via explicit PyArrow
    schema).
  * `providers/`: NSE `cm` bhavcopy parser + `rows_to_bars` mapper.
  * `service/`: `VyapaarDataService.adjusted_history()` restates prices/volumes
    to the current corporate-action basis (no look-ahead: actions strictly
    after each bar's date are chained in ex-date order).
* Zone 3 configs: `configs/catalog.toml`. CI: `.github/workflows/ci.yml`.

## Decisions & Discoveries
* pyproject declares proper PEP 621 deps (`vyapaar`, `duckdb`, `polars`,
  `pyarrow`, `pydantic`) — the invalid `rust_decimal>=1.0.0` dependency is gone.
* `pl.DataFrame.to_arrow(schema=...)` is **not** supported in polars 2.1.0;
  the catalog builds Arrow tables via `pa.Table.from_pydict(..., schema=...)`.
* `datetime.UTC` (py3.11+) preferred over `timezone.utc` per ruff UP017.
* Split/bonus encoding: `old_shares` held -> `new_shares` after action;
  `price_multiplier = old/new`, `quantity_multiplier = new/old`.

## Immediate Next Step
* Tier 6B: `vyapaar-adapters` (broker ACL SDK with entry points and
  paper/mock harness).

## Operating Invariants
* Zero floats: `decimal.Decimal` + `DECIMAL128(18,4)` everywhere in financial
  columns; mypy/ruff/pytest gates are the CI contract.
* Tests live in `tests/` only (parallel test directory rule).
