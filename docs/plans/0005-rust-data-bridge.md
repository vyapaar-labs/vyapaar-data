# Plan 0005 — vyapaar-data → Rust Data Bridge

## Objective

Close gaps 0007 and 0008: expose the Python-side filings and corporate-actions datasets to
Rust consumers through a single `vyapaar-data` → Rust FFI/Arrow bridge, unblocking the chat
agent's `filings_search` and `corporate_actions` tools.

## Gaps Tracked by This Plan

| Gap | Title | Severity |
|-----|-------|----------|
| [0007](../gaps/0007-filings-rust-bridge.md) | Filings data is Python-side only — no Rust consumer bridge | Medium |
| [0008](../gaps/0008-corporate-actions-rust-bridge.md) | Corporate-actions data is Python-side only — no Rust consumer bridge | Medium |

## Implementation Phases

1. Land the `vyapaar-data` → Rust bridge: Arrow zero-copy record batches over the existing
   DuckDB/Parquet lakehouse (the same mechanism `vyapaar-ffi` uses for the `vyapaar` Python
   wheel in the other direction), or expose a machine-readable projection the runtime can
   ingest.
2. Surface the filings dataset (`Filing`/`FilingType`) through it, keeping the exact-`Decimal`
   record shape and point-in-time visibility semantics (`filing_date <= as-of date`).
3. Surface the corporate-actions dataset (`Split`/`Bonus`/`Dividend`/`Rights`) through it.
4. Replace `FeedContentReader::filings` / `FeedMarketReader::corporate_actions` stand-ins in
   `vyapaar-runtime` with real reads.

> One bridge, multiple datasets — do not build a corporate-actions-only second bridge.

## Exit Criteria

- A Rust consumer can read filings and corporate actions through the bridge.
- `vyapaar-runtime` chat adapters return real data (no `PortError::unavailable`).
- `pytest -q`, `ruff check .`, `ruff format --check .`, `mypy vyapaar_data` pass.
- `docs/gaps/README.md` marks 0007 and 0008 closed with closing commits.

## Related

- `vyapaar_data/service/filings_reader.py` — `LakehouseFilingsReader`.
- `vyapaar_data/adapters/duckdb_store.py` — `DuckDbCorporateActionsStore`.
- `vyapaar-ffi` — Arrow zero-copy memory bridge mechanism.
- `vyapaar-agent` plan 0006 — `filings_search`/`corporate_actions` chat tools.
- [0009](../gaps/0009-corporate-actions-ingestion.md) — companion ingestion gap (a bridge
  over an empty table still answers "no actions recorded").
