# 0001 — Catalog coverage unverified for downstream consumers

**Status**: open

## What's stubbed or hardcoded

Nothing in this repo's own code is stubbed. This gap tracks an unverified assumption two
downstream consumers were both making before this audit: that this repo's Parquet bar catalog
(`{root}/catalog/{TF}/{EXCHANGE}/{SYMBOL}/{PART}.parquet`, per
`vyapaar-runtime/crates/vyapaar-runtime-api-rest/src/catalog.rs`'s own doc comment, which this
repo's data is expected to populate) actually contains real historical bars for the instruments
they need:

- `vyapaar-runtime-api-rest`'s `GET /bars/{id}` endpoint (`src/market.rs`) reads through this
  catalog via `CatalogBars`/`load_catalog`, and is itself fully implemented and tested — but only
  against an in-memory/temp-dir fixture (`tests/market_data.rs`), never against a real, deployed
  catalog directory.
- `vyapaar-ui-web`'s Phase C4 Risk-tab scoping (`vyapaar-ui-web/docs/plans/0007-risk-tab-quant-
  analytics.md`) and its dashboard-sparkline gap (`vyapaar-ui-web/docs/gaps/0011`) both need a
  real historical-bars series, and had each independently assumed — until this audit corrected
  both — that no such endpoint existed anywhere upstream at all. It does; it just needs this
  repo's catalog to actually have coverage.

## Why

This repo ships the catalog *format* and one real ingestion path (the NSE bhavcopy CSV provider,
plus `vyapaar-market-store`'s bhavcopy/Parquet-import code) but holds no catalog data in the repo
itself — expected, since a lakehouse's data lives outside version control, but it means no
session so far has confirmed a live deployment's catalog actually has coverage (per this repo's
own "coverage ledgers... report uncovered gaps" feature, README) for arbitrary portfolio-held
instruments or common benchmark indices.

## How to close it

Run this repo's coverage-ledger reporting against whichever instruments `vyapaar-ui-web`'s
portfolios/benchmarks actually need, against the catalog directory a real deployment points
`vyapaar-runtime`'s `load_catalog` at. If coverage is missing, that's an ingestion-scheduling task
in this repo, not a code gap; if coverage exists, close this gap and let `vyapaar-ui-web`'s gap
0011 and its `docs/plans/0007`'s C4a slice proceed on the real-endpoint option without further
blocking.
