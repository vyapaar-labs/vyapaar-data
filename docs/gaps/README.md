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
| [0001](0001-catalog-coverage-unverified-for-downstream-consumers.md) | Parquet catalog's real-data coverage is unverified for downstream consumers (`vyapaar-runtime`'s `/bars` endpoint, `vyapaar-ui-web`'s Risk tab/sparklines) | `vyapaar_data` (catalog) |

## Closed gaps

| # | Title | Area |
|---|-------|------|
