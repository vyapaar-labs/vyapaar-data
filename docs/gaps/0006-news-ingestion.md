# 0006 — News article ingestion

**Status**: open

## What's stubbed or hardcoded

This repo has no news data source at all: no port, no reader, no Parquet catalog
table, and no ingestion provider. Financial news (headline, source/publisher,
publication timestamp, summary, article URL, and the instruments an article
mentions) is one of the content categories `vyapaar-agent`'s chat tool catalog
covers — `vyapaar-agent/docs/plans/0006-mcp-tool-catalog-expansion-guide.md`
Phase 3 adds a `news_search` chat tool (`NewsSearchTool` over a new
`ContentReader` port), modeled on longbridge's Content/Search (news
list/detail/search) and Fincept's "News and alternative data" toolset.

Until a source exists, the chat agent cannot answer a grounded question like
"what's the latest news on RELIANCE?" — `vyapaar-runtime`'s content adapter
(`crates/vyapaar-runtime-api-rest/src/chat_content.rs::FeedContentReader`)
answers every news query with an explicit `PortError::unavailable` citing this
gap, so the model reports the missing source instead of fabricating headlines.

## Why

`vyapaar-agent/docs/plans/0006-mcp-tool-catalog-expansion-guide.md` Phase 3
needs this repo to be the actual data provider, per this workspace's
gap-tracking rule (`.agents/rules/gap-tracking.md` §5): a stub's root cause
gets filed in the provider repo, not silently stubbed in the consumer. The
plan's §1.3 lists options-chain and corporate-actions readers as the other
genuinely-blocked categories; news is the third.

No vendor or source is decided. News licensing varies widely (free RSS vs
paid API feeds; exchange-curated feeds vs aggregator APIs), and the Indian
market has several disjoint sources (exchange press releases, corporate
announcements are already partially covered by the *filings* reader — closed
gap 0003 — while third-party *news* is a separate feed class). Nothing should
be assumed or invented here.

## How to close it

1. Decide the ingestion source (class: RSS/aggregator/exchange announcements)
   and verify its live feed shape (fields, cadence, retention window, article
   ↔ instrument linkage quality) against the real source — do not assume a
   shape or URL without checking it live.
2. Add a `NewsRepository` port under `vyapaar_data/ports/repositories.py`,
   following the same shape as the existing `FilingsRepository`
   (`vyapaar_data/ports/repositories.py`, backing
   `vyapaar_data/service/filings_reader.py`).
3. Add a reader service (e.g. `vyapaar_data/service/news_reader.py`) returning
   article records (id, title, source, url, published_at, summary, instrument
   mentions).
4. Land the ingested data in this repo's existing Parquet catalog pattern
   (`data/catalog/`).
5. Once real ingestion lands, replace `FeedContentReader::news_search`'s
   explicit-error stand-in (`vyapaar-runtime`) with a real read through the
   runtime's data bridge.
