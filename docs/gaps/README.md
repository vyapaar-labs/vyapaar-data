# Gaps index

Every time something in this repo is stubbed, mocked, or hardcoded because the real
dependency (a data source, a pipeline, a design decision) isn't wired up yet, it gets a
numbered entry here instead of being left silent. Per root `.agents/rules/gap-tracking.md`
§3, this index also carries gaps whose symptom shows up in a *different* repo but whose root
cause lives here.

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

| # | Title | Area |
|---|-------|------|
| 0001 | Economic/earnings/dividends/splits/IPO calendar ingestion | `vyapaar_data` (calendar) |
| 0002 | Company fundamentals / symbol profile ingestion | `vyapaar_data` (reference) |
| 0003 | Calendar data stubbed pending external source decision | `vyapaar_data` (calendar) |
| [0004](0004-catalog-seeded-from-honba-kao-ad-hoc-copy.md) | `data/catalog/` NSE daily bars seeded via ad-hoc copy from honba-kao, not vyapaar-data's own ingestion pipeline | `data/catalog/1D`, `data/catalog/5M` |
| [0005](0005-block-bulk-deal-disclosure-ingestion.md) | Block & bulk deal disclosure ingestion — no data source, port, or reader exists | `vyapaar_data` (reference) |
| [0006](0006-news-ingestion.md) | News article ingestion — no data source, port, or reader exists (blocks chat `news_search` tool) | `vyapaar_data` (reference) |
| [0007](0007-filings-rust-bridge.md) | Filings data is Python-side only — no `vyapaar-data` → Rust consumer bridge (blocks chat `filings_search` tool) | `vyapaar_data` (filings) |

## Closed gaps

| # | Title | Area |
|---|-------|------|
| 0001 | Parquet catalog coverage verified for downstream consumers (`vyapaar-runtime`'s `/bars` endpoint, `vyapaar-ui-web`'s Risk tab/sparklines) | `vyapaar_data` (catalog) |
| 0002 | Macro series ingestion stub (`PythonMacroReader` returns empty) | `vyapaar_data.service.macro_reader` | Closed in `c08710d` (macro series ingestion behind `PythonMacroReader`) |
| 0003 | Filings ingestion & expanded economic series breadth | `vyapaar-data` (macro + filings) | Closed in `c08710d` (filings ingestion behind `FilingsReader`/`LakehouseFilingsReader`) |
