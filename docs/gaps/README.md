# Gaps index

Every time something in this repo is stubbed, mocked, or hardcoded because the real
dependency (a data source, a pipeline, a design decision) isn't wired up yet, it gets a
numbered entry here instead of being left silent. Per root `.agents/rules/gap-tracking.md`
§3, this index also carries gaps whose symptom shows up in a *different* repo but whose root
cause lives here.

Numbering is per-repo, sequential, never reused: closed gaps 0001–0003 (and 0011) keep
their numbers, so new gaps continue from 0004. The original open gaps 0001–0003 collided
with the closed 0001–0003 and were renumbered to 0010–0012 during the 2026-11-12 docs
overhaul.

## Entry template

```markdown
# XXXX — Short title

**Status**: open | closed (link the closing commit/PR)

## What's stubbed or hardcoded
...

## Why
...

## How to close it
...
```

## Open gaps

| # | Title | Area | Plan |
|---|-------|------|------|
| [0004](0004-catalog-seeded-from-honba-kao-ad-hoc-copy.md) | `data/catalog/` NSE daily bars seeded via ad-hoc copy from honba-kao, not vyapaar-data's own ingestion pipeline | `data/catalog/1D`, `data/catalog/5M` | [0006](../plans/0006-lakehouse-ingestion-completeness.md) |
| [0005](0005-block-bulk-deal-disclosure-ingestion.md) | Block & bulk deal disclosure ingestion — no data source, port, or reader exists | `vyapaar_data` (reference) | [0004](../plans/0004-content-and-disclosure-ingestion.md) |
| [0006](0006-news-ingestion.md) | News article ingestion — no data source, port, or reader exists (blocks chat `news_search` tool) | `vyapaar_data` (reference) | [0004](../plans/0004-content-and-disclosure-ingestion.md) |
| [0007](0007-filings-rust-bridge.md) | Filings data is Python-side only — no `vyapaar-data` → Rust consumer bridge (blocks chat `filings_search` tool) | `vyapaar_data` (filings) | [0005](../plans/0005-rust-data-bridge.md) |
| [0008](0008-corporate-actions-rust-bridge.md) | Corporate-actions data is Python-side only — no `vyapaar-data` → Rust consumer bridge (blocks chat `corporate_actions` tool) | `vyapaar_data` (corporate actions) | [0005](../plans/0005-rust-data-bridge.md) |
| [0009](0009-corporate-actions-ingestion.md) | Corporate-actions DuckDB store has no automatic ingestion — population is manual/test-seeded today | `vyapaar_data` (corporate actions) | [0006](../plans/0006-lakehouse-ingestion-completeness.md) |
| [0010](0010-economic-calendar-ingestion.md) | Economic/earnings/dividends/splits/IPO calendar ingestion — reader/port/store implemented, real vendor source not selected | `vyapaar_data` (calendar) | [0003](../plans/0003-calendar-and-reference-data.md) |
| [0012](0012-calendar-stubbed-data.md) | Calendar data stubbed pending external source decision | `vyapaar_data` (calendar) | [0003](../plans/0003-calendar-and-reference-data.md) |

## Closed gaps

| # | Title | Area |
|---|-------|------|
| 0001 | Parquet catalog coverage verified for downstream consumers (`vyapaar-runtime`'s `/bars` endpoint, `vyapaar-ui-web`'s Risk tab/sparklines) | `vyapaar_data` (catalog) |
| 0002 | Macro series ingestion stub (`PythonMacroReader` returns empty) | `vyapaar_data.service.macro_reader` | Closed in `c08710d` (macro series ingestion behind `PythonMacroReader`) |
| 0003 | Filings ingestion & expanded economic series breadth | `vyapaar-data` (macro + filings) | Closed in `c08710d` (filings ingestion behind `FilingsReader`/`LakehouseFilingsReader`) |
| 0011 | Company fundamentals / symbol profile ingestion (was `0002-company-fundamentals-symbol-profile.md`; renumbered to fix the 0001–0003 collision) | `vyapaar_data` (profile) | Closed in `261d646` (`SymbolProfile` domain, `ProfileRepository`/`ProfileReader` ports, `DuckDbProfileStore`, `LakehouseProfileReader`, yfinance provider `fetch_symbol_profiles`, tests in `tests/test_profile.py`) |
