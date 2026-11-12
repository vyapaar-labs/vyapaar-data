# 0013 — FII/DII daily institutional net-flow ingestion

**Status**: open

## What's stubbed or hardcoded

This repo has no FII (Foreign Institutional Investor) / DII (Domestic Institutional Investor)
daily net-flow data source at all: no repository port, no reader, no Parquet catalog table. A
repo-wide grep for `fii`/`dii` across `vyapaar-data` finds zero matches. NSE and SEBI both
publish daily provisional and final FII/DII cash-market net buy/sell figures (and, separately,
F&O net positioning), and this is one of the most direct, widely-watched "institutional big
money" signals in Indian equity markets — but nothing in this workspace (this repo,
`vyapaar-market`, or `vyapaar-adapters`) ingests it. The chat agent has no tool that could ever
ground an answer to "are FIIs buying or selling today?" in real data.

## Why

`vyapaar-agent/docs/plans/0010-institutional-smart-money-detection-suite.md` scopes an
`institutional_flows` chat tool and a composite smart-money strategy signal in
`vyapaar-strategies` that both need this repo to be the actual data source, per this
workspace's gap-tracking rule (`.agents/rules/gap-tracking.md` §5): a stub's root cause is
filed in the provider repo, not silently stubbed in the consumer.

Like block/bulk deals ([0005](0005-block-bulk-deal-disclosure-ingestion.md)) and unlike the
economic calendar ([0010](0010-economic-calendar-ingestion.md), which needs a paid vendor
decision), FII/DII net-flow figures are public exchange/regulator data published daily with no
vendor licensing involved. The open decision here is narrower: which publisher to ingest from
first (NSE's own daily FII/DII provisional figures vs. SEBI's FPI data), the exact
disclosure/file shape (cash-market net buy/sell in ₹ crore, and separately index/stock futures
and options net OI change for the F&O leg), publish cadence (provisional same-day evening,
final T+1), and how far back to backfill. No source URL or vendor name should be assumed here
— verify the live disclosure shape against the current publisher before implementing.

Target shape (per-day record): trade date, participant category (`FII` | `DII`), segment
(`cash` | `index_futures` | `stock_futures` | `index_options` | `stock_options`), gross buy
value, gross sell value, net value (all `Money`, exact `Decimal`). Cash-segment net value is the
primary signal; F&O segment rows are additive context for the composite strategy's OI-buildup
cross-check.

## How to close it

1. Decide the ingestion source(s) (NSE provisional/final FII-DII bulletins first) and verify the
   live disclosure shape (columns, file/feed format, publish time, historical backfill depth)
   against the exchange's current disclosure feed — do not assume a shape or URL without
   checking it live.
2. Add an `InstitutionalFlowRepository` port under `vyapaar_data/ports/repositories.py`,
   following the same shape as the existing `MacroSeriesRepository`
   (`vyapaar_data/ports/repositories.py`, backing `vyapaar_data/service/macro_reader.py`'s
   `PythonMacroReader`).
3. Add a `PythonInstitutionalFlowReader` (or similarly named) service in
   `vyapaar_data/service/institutional_flow_reader.py`, returning a Polars `DataFrame` with the
   target shape above (exact `Decimal` value columns, per this repo's existing readers'
   convention).
4. Land the ingested data in this repo's existing Parquet catalog pattern (`data/catalog/`), the
   same lakehouse architecture the macro-series, filings, and block/bulk-deal gaps already use.
5. Once this lands, `vyapaar-agent/docs/plans/0010-institutional-smart-money-detection-suite.md`
   Phase 1's `institutional_flows` chat tool can replace its `PortError::unavailable`
   stand-in with a real read.

No code should be written against this gap document until the ingestion-source decision above
is made; it is documentation only, recording the decision point and target shape.
