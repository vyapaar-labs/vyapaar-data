# 0005 — Block & bulk deal disclosure ingestion

**Status**: open

## What's stubbed or hardcoded

This repo has no block-deal or bulk-deal disclosure data source at all: no repository port,
no reader, no Parquet catalog table. A block deal is a single large trade (above an exchange
minimum, negotiated in a separate trading window) and a bulk deal is any single trade on the
regular order book whose quantity exceeds 0.5% of a company's listed shares; NSE and BSE each
publish their own daily disclosure for both categories. Right now this workspace's chat agent
(`vyapaar-runtime`'s `/ws/chat`, backed by `vyapaar-agent-chat-tools`'s market tool catalog) has
no tool that could ever answer a question like "any notable block deals today?" — grounded on
data, because no reader anywhere in this repo (or `vyapaar-market`, or `vyapaar-adapters`)
produces this shape. The LLM currently falls back to answering from its own pretrained knowledge
with a generic, non-grounded disclaimer instead.

## Why

`vyapaar-runtime/docs/plans/0004-block-bulk-deal-chat-tool-and-rest-endpoint.md` adds a
`block_deals` method to the chat agent's `MarketReader` port and a `BlockDealsTool`, but both need
this repo to be the actual data source, per this workspace's gap-tracking rule
(`.agents/rules/gap-tracking.md` §5): a stub's root cause gets filed in the provider repo, not
silently stubbed in the consumer.

Unlike `docs/gaps/0001-economic-calendar-ingestion.md` (which needs a paid vendor decision),
block/bulk deal disclosures are public exchange data — NSE and BSE both publish them as part of
their routine daily surveillance disclosures, with no vendor licensing involved. The open decision
here is narrower: which exchange(s) to ingest from first, the exact disclosure file/feed shape
(columns and refresh cadence can differ slightly between NSE and BSE and are worth verifying
against the live source rather than assumed), and how far back to backfill. No source URL or
vendor name should be assumed here — verify the live disclosure shape before implementing.

Target shape (per-deal record), based on how both exchanges disclose this category generally: a
trade date, exchange, instrument/security identifier, client/counterparty name, buy or sell side,
deal category (`block` or `bulk`), quantity, and trade/weighted-average price. All price and
quantity fields must be exact `Decimal`, per this repo's Zero Floats Policy.

## How to close it

1. Decide the ingestion source(s) (NSE first, BSE second, or both at once) and verify the live
   disclosure shape (columns, file format, publish time, historical backfill availability) against
   the exchange's current disclosure feed — do not assume a shape or URL without checking it live.
2. Add a `BlockDealsRepository` port under `vyapaar_data/ports/repositories.py`, following the
   same shape as the existing `MacroSeriesRepository` (`vyapaar_data/ports/repositories.py`,
   backing `vyapaar_data/service/macro_reader.py`'s `PythonMacroReader`) and
   `FilingsRepository`/`LakehouseFilingsReader` (`vyapaar_data/service/filings_reader.py`).
3. Add a `PythonBlockDealsReader` (or similarly named) service in
   `vyapaar_data/service/block_deals_reader.py`, returning a Polars `DataFrame` with the target
   shape above (exact `Decimal` price/quantity columns, per this repo's existing readers'
   convention).
4. Land the ingested data in this repo's existing Parquet catalog pattern (`data/catalog/`), the
   same lakehouse architecture the macro-series and filings gaps already use.
5. Once this lands, `vyapaar-runtime/docs/plans/0004-block-bulk-deal-chat-tool-and-rest-endpoint.md`
   Phase 3 can replace its `PortError::unavailable` stand-in with a real read.

No code should be written against this gap document until the ingestion-source decision above is
made; it is documentation only, recording the decision point and target shape.
