# 0008 — Corporate-actions data is Python-side only — no `vyapaar-data` → Rust consumer bridge

**Status**: open

## What's stubbed or hardcoded

`vyapaar-agent`'s plan 0006 Phase 4 adds a `corporate_actions` chat tool
(`vyapaar-agent-chat-tools`'s `MarketReader::corporate_actions` port method), and
`vyapaar-runtime`'s chat adapter answers it with an honest `PortError::unavailable`
stand-in because no Rust consumer can reach this repo's corporate-actions data.

Verified 2026-11-12 (point-in-time re-check, per the plan's §4 Phase 4 requirement):
a **historical corporate-actions reader does exist Python-side** — this gap is
therefore a *bridge* gap in the exact shape of
[0007](0007-filings-rust-bridge.md) (filings), not a "no data source exists" gap:

- Protocol: `vyapaar_data/ports/repositories.py` — `CorporateActionsRepository`
  (line ~35), `list(instrument, as_of)` with an ex-date window.
- Store: `vyapaar_data/adapters/duckdb_store.py` —
  `DuckDbCorporateActionsStore` (line ~343) over a persisted `corporate_actions`
  DuckDB table (DDL lines ~36–37; INSERT/SELECT ~350–382).
- Domain: `vyapaar_data/domain/corporate_actions.py` — `Split`/`Bonus`/`Dividend`/
  `Rights` value objects with `ex_date`, ratios, and per-share amounts.
- Facade: `vyapaar_data/service/data_service.py` —
  `VyapaarDataService.corporate_actions` (line ~59, `.list()` at line ~73).

Nothing bridges that store into Rust: there is no FFI/Arrow path a Rust consumer
(e.g. `vyapaar-runtime`'s `AppState`, `vyapaar-agent-chat-tools`'s ports) can call.

## Why

Per this workspace's gap-tracking rule (`.agents/rules/gap-tracking.md` §5), the
stub's root cause is filed in the provider repo. The chat tool is blocked on the
same standing limitation as `filings_search` (gap 0007): this repo's lakehouse is
Python-only, and the `vyapaar-data` → Rust bridge that would let any Rust service
read it does not exist yet.

## How to close it

1. Extend the same `vyapaar-data` → Rust FFI/Arrow bridge mechanism planned for
   gap 0007 (filings) to corporate actions — one bridge, multiple datasets, is the
   shape both consumers need; do not build a corporate-actions-only second bridge.
2. Once the bridge lands, `vyapaar-runtime`'s `FeedMarketReader::corporate_actions`
   (currently a stand-in) reads through it instead of returning
   `PortError::unavailable`.
3. Note the companion limitation: whatever the bridge exposes is only as complete
   as the table's population — real-world historical coverage depends on
   [0009](0009-corporate-actions-ingestion.md) (no provider ingests historical
   actions automatically today).

No code should be written against this gap document until the bridge design
(shared with gap 0007) is decided; it is documentation only, recording the
decision point and target shape.
