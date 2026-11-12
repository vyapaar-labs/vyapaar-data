# Plan 0006 — Lakehouse Ingestion Completeness

## Objective

Close gaps 0004 and 0009: populate the Parquet catalog and the corporate-actions DuckDB
store through real ingestion pipelines instead of ad-hoc copies and test seeding.

## Gaps Tracked by This Plan

| Gap | Title | Severity |
|-----|-------|----------|
| [0004](../gaps/0004-catalog-seeded-from-honba-kao-ad-hoc-copy.md) | `data/catalog/` seeded via ad-hoc copy from honba-kao, not vyapaar-data's own pipeline | Medium |
| [0009](../gaps/0009-corporate-actions-ingestion.md) | Corporate-actions DuckDB store has no automatic ingestion | Medium |

## Implementation Phases

### Phase A — Corporate-actions ingestion (gap 0009)

1. Decide the ingestion source(s) — NSE and BSE both publish historical corporate-action
   announcements (dividends, splits, bonus, rights); verify the live disclosure shape before
   implementing.
2. Add an ingestion provider in `vyapaar_data/providers/` that constructs the existing
   `Split`/`Bonus`/`Dividend`/`Rights` domain records and writes them through
   `DuckDbCorporateActionsStore` (the store side needs no change).
3. Keep exact `Decimal` for ratios and per-share amounts, per this repo's Zero Floats Policy.

### Phase B — Catalog ingestion (gap 0004)

1. Replace the ad-hoc `data/catalog/1D` and `data/catalog/5M` copies with real ingestion
   through `vyapaar_data`'s own adapters/providers (the NSE bhavcopy provider is the
   existing pipeline; a backfill command over historical bhavcopies is the natural shape).
2. Delete the copied trees this gap introduced and reseed from the real pipeline.
3. Treat the copied data as throwaway dev-fixture data until then (provenance, licensing,
   point-in-time correctness, and corporate-actions adjustment are unverified).

## Exit Criteria

- The catalog and the corporate-actions table are populated by vyapaar-data pipelines.
- `pytest -q`, `ruff check .`, `ruff format --check .`, `mypy vyapaar_data` pass.
- `docs/gaps/README.md` marks 0004 and 0009 closed with closing commits.

## Related

- `vyapaar_data/adapters/parquet_catalog.py` — `ParquetCatalog`.
- `vyapaar_data/adapters/duckdb_store.py` — `DuckDbCorporateActionsStore`.
- `vyapaar_data/providers/bhavcopy.py` — NSE bhavcopy parser (catalog ingestion path).
- [0008](../gaps/0008-corporate-actions-rust-bridge.md) — the Rust bridge is only as
  complete as the table's population.
