# 0004 — `data/catalog/` seeded via ad-hoc copy from honba-kao, not vyapaar-data's own pipeline

**Status**: open

## What's stubbed or hardcoded

`data/catalog/1D/NSE/` and `data/catalog/5M/NSE/` (120 NSE symbols, per-year `.parquet` daily
bars under `1D`, plus a thin `5M` tree) were populated by directly copying files from the
sibling `honba-kao` project's own data directory
(`/home/pmallapp/Devel/Finance/honba-workspace/honba-data/data/catalog`), not through any
adapter, provider, or ingestion command in `vyapaar_data/`. Before this copy, `data/catalog/`
was empty — `vyapaar-runtime-api-rest`'s `GET /instruments`/`/quotes`/`/bars/{id}` had no data to
serve at all when pointed at this repo's own `data/` directory.

## Why

`vyapaar-ui-web`'s Symbol Search dialog and watchlist price/change% columns needed *some* real
data to verify against during development (`docs/gaps/0064` in `vyapaar-ui-web`, closed), and
honba-kao happened to have a compatible catalog layout (`catalog/<tf>/<EXCHANGE>/<SYMBOL>/<year>.parquet`)
with real historical NSE daily bars already on disk. Copying it was the fastest way to unblock
that work; it was not produced by any of `vyapaar_data`'s adapters (`vyapaar_data/adapters/`),
so its provenance, licensing, point-in-time correctness, and corporate-actions adjustment are
all unverified — treat it as throwaway dev-fixture data, not a trustworthy source for anything
beyond local UI development.

## How to close it

- Replace this ad-hoc copy with real ingestion through `vyapaar_data`'s own adapters/providers
  (whichever upstream feed this repo is meant to source NSE daily bars from), or, if honba-kao's
  pipeline itself is meant to be ported into `vyapaar_data` per the ecosystem's stated direction
  (root `AGENTS.md`: `vyapaar-data` is the canonical Data Lakehouse), port that ingestion logic
  here properly instead of just its output files.
- Once real ingestion exists, delete the copied `data/catalog/1D` and `data/catalog/5M` trees
  this gap introduced and reseed from the real pipeline.
