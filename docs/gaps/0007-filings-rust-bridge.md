# 0007 — Filings data has no Rust-consumer bridge

**Status**: open

## What's stubbed or hardcoded

Filings ingestion exists in this repo's Python service — closed gap 0003
landed `vyapaar_data.domain.filings.Filing`/`FilingType`, the
`FilingsRepository` port (`vyapaar_data/ports/repositories.py`), and
`LakehouseFilingsReader` (`vyapaar_data/service/filings_reader.py`). But no
Rust consumer can reach that data: there is no FFI/Arrow bridge, no REST
projection served to Rust, and no Rust-side reader for filings anywhere in
`vyapaar-runtime`/`vyapaar-ffi`.

The consumer blocked today is the chat agent: `vyapaar-agent` plan 0006 Phase
3 adds a `filings_search` chat tool (`FilingsSearchTool` over a new
`ContentReader` port, mirroring this repo's `Filing` shape — instrument,
filing date, `FilingType` value, title, source URL). Until the bridge exists,
`vyapaar-runtime`'s content adapter
(`crates/vyapaar-runtime-api-rest/src/chat_content.rs::FeedContentReader`)
answers every filings query with an explicit `PortError::unavailable` citing
this gap.

## Why

`vyapaar-agent/docs/plans/0006-mcp-tool-catalog-expansion-guide.md` Phase 3
needs filings readable from Rust, and this workspace's gap-tracking rule
(`.agents/rules/gap-tracking.md` §5) requires the provider repo to own the
gap. This is the same shape as the standing `vyapaar-data` → Rust FFI bridge
item that `vyapaar-runtime`'s market-reference endpoints already stub against
(`vyapaar-runtime/crates/vyapaar-runtime-api-rest/src/market.rs` sample
stores pending the bridge, sourced from gaps 0001/0002 data): filings are the
next lakehouse dataset behind the same missing bridge.

## How to close it

1. Land the `vyapaar-data` → Rust FFI bridge (Arrow zero-copy record batches
   over the existing DuckDB/Parquet lakehouse — the same mechanism
   `vyapaar-ffi` uses for the `vyapaar` Python wheel in the other direction)
   or expose a machine-readable projection the runtime can ingest.
2. Surface the filings dataset (`Filing`/`FilingType`) through it, keeping
   the exact-`Decimal`/zero-float record shape and point-in-time visibility
   semantics (`filing_date <= as-of date`) the Python reader guarantees.
3. Once bridged, replace `FeedContentReader::filings`'s explicit-error
   stand-in (`vyapaar-runtime`) with a real read.
