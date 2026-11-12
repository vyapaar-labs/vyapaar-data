# Plan 0004 — Content & Disclosure Ingestion

## Objective

Close gaps 0005 and 0006: add block/bulk deal disclosure ingestion and news article
ingestion so the chat agent's `block_deals`, `news_search`, and related content tools can be
grounded on real data.

## Gaps Tracked by This Plan

| Gap | Title | Severity |
|-----|-------|----------|
| [0005](../gaps/0005-block-bulk-deal-disclosure-ingestion.md) | Block & bulk deal disclosure ingestion | Medium |
| [0006](../gaps/0006-news-ingestion.md) | News article ingestion | Medium |

## Implementation Phases

### Phase A — Block & bulk deals (gap 0005)

1. Decide the ingestion source(s) (NSE first, BSE second, or both) and verify the live
   disclosure shape against the exchange feed — do not assume a shape or URL.
2. Add a `BlockDealsRepository` port under `vyapaar_data/ports/repositories.py` and a
   `BlockDealsReader` port in `vyapaar_data/ports/data_feeds.py`, following the
   `MacroSeriesRepository` / `FilingsRepository` precedent.
3. Add a reader service in `vyapaar_data/service/` returning exact-`Decimal` Polars frames.
4. Land the data in the Parquet catalog pattern (`data/catalog/`).
5. Unblocks `vyapaar-runtime` plan 0004 Phase 3 (replace `PortError::unavailable` stand-in).

### Phase B — News ingestion (gap 0006)

1. Decide the ingestion source (RSS / aggregator / exchange announcements) and verify the
   live feed shape.
2. Add a `NewsRepository` port and a reader service returning article records (id, title,
   source, url, published_at, summary, instrument mentions).
3. Land the data in the Parquet catalog pattern.
4. Unblocks `FeedContentReader::news_search` in `vyapaar-runtime` (replace the explicit-error
   stand-in).

## Exit Criteria

- Both readers exist behind ports, return exact-`Decimal` frames, and are tested.
- `pytest -q`, `ruff check .`, `ruff format --check .`, `mypy vyapaar_data` pass.
- `docs/gaps/README.md` marks 0005 and 0006 closed with closing commits.

## Related

- `vyapaar_data/ports/repositories.py` — repository port precedent.
- `vyapaar_data/service/macro_reader.py`, `vyapaar_data/service/filings_reader.py` — reader
  service precedent.
- `vyapaar-runtime` plan 0004 — block/bulk deal chat tool & REST endpoint.
- `vyapaar-agent` plan 0006 — `news_search`/`filings_search` chat tools.
