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

## Closed gaps

| # | Title | Area |
|---|-------|------|
| 0001 | Parquet catalog coverage verified for downstream consumers (`vyapaar-runtime`'s `/bars` endpoint, `vyapaar-ui-web`'s Risk tab/sparklines) | `vyapaar_data` (catalog) |
| 0002 | Macro series ingestion stub (`PythonMacroReader` returns empty) | `vyapaar_data.service.macro_reader` | Closed in `c08710d` (macro series ingestion behind `PythonMacroReader`) |
| 0003 | Filings ingestion & expanded economic series breadth | `vyapaar-data` (macro + filings) | Closed in `c08710d` (filings ingestion behind `FilingsReader`/`LakehouseFilingsReader`) |
