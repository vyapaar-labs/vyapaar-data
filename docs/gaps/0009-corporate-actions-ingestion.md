# 0009 — Corporate-actions ingestion — the DuckDB store has no automatic data population

**Status**: open

## What's stubbed or hardcoded

This repo has a corporate-actions **store and reader**
(`vyapaar_data/adapters/duckdb_store.py`'s `DuckDbCorporateActionsStore` over the
persisted `corporate_actions` DuckDB table, behind the
`CorporateActionsRepository` protocol — see [0008](0008-corporate-actions-rust-bridge.md))
but **no ingestion path that populates it with real historical disclosure data**:
no provider constructs `Split`/`Dividend`/`Bonus`/`Rights` records anywhere in
`vyapaar_data/providers/` or `vyapaar_data/adapters/` outside the store itself.
Population today is manual/test-seeded, and the coverage CLI instantiates the
store in-memory (`vyapaar_data/cli/coverage.py` line ~33), so real-world
historical coverage is effectively empty.

This is distinct from [0010](0010-economic-calendar-ingestion.md) (the
*scheduled/forward* calendar — upcoming dividends/splits/IPOs as dated events,
blocked on a vendor decision): this gap is about *realized, historical* actions
with ex-dates, ratios, and amounts — public exchange/announcement data, no vendor
licensing involved.

## Why

Chat tool `corporate_actions` (`vyapaar-agent` plan 0006 Phase 4) and any
future point-in-time corporate-action adjustment consumer need this table to hold
real data; a Rust bridge over an empty table (gap 0008) would still answer "no
actions recorded". Per this workspace's gap-tracking rule, the root cause (no
ingestion) is recorded in the provider repo rather than left silent.

## How to close it

1. Decide the ingestion source(s) — NSE and BSE both publish historical
   corporate-action announcements (dividends, splits, bonus, rights) as part of
   their routine disclosures; verify the live disclosure shape (columns, history
   depth, refresh cadence) against the exchange feed before implementing rather
   than assuming a URL or schema.
2. Add an ingestion provider in `vyapaar_data/providers/` that constructs the
   existing `Split`/`Bonus`/`Dividend`/`Rights` domain records and writes them
   through `DuckDbCorporateActionsStore` — the store side needs no change.
3. Keep exact `Decimal` for ratios and per-share amounts, per this repo's Zero
   Floats Policy.

No code should be written against this gap document until the ingestion-source
decision is made; it is documentation only, recording the decision point and
target shape.
