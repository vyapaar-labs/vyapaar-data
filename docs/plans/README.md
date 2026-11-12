# Plans Index — `vyapaar-data`

Per workspace rule `.agents/rules/gap-tracking.md`:
- Gaps are individual features (`docs/gaps/XXXX-*.md`).
- Plans are collections of gaps (`docs/plans/XXXX-*.md`).
- When implemented, plan documents are cleaned up from `docs/plans/` and recorded in this index.
- Numbering is per-repo, sequential, never reused.

## Active Plans

| # | Title | Target Scope | Status |
|---|-------|--------------|--------|
| [0003](0003-calendar-and-reference-data.md) | Calendar & Reference Data | `vyapaar_data` (calendar) | Open — tracks gaps 0010, 0012 (real calendar source + stub replacement) |
| [0004](0004-content-and-disclosure-ingestion.md) | Content & Disclosure Ingestion | `vyapaar_data` (block deals, news) | Open — tracks gaps 0005, 0006 |
| [0005](0005-rust-data-bridge.md) | vyapaar-data → Rust Data Bridge | `vyapaar_data` (filings, corporate actions) + `vyapaar-runtime`/`vyapaar-ffi` | Open — tracks gaps 0007, 0008 |
| [0006](0006-lakehouse-ingestion-completeness.md) | Lakehouse Ingestion Completeness | `vyapaar_data` (catalog, corporate actions) | Open — tracks gaps 0004, 0009 |

## Implemented Plans

| # | Title | Target Scope | Implemented In |
|---|-------|--------------|----------------|
| 0001 | Lakehouse & Port Architecture for MCP Quantitative Tools and Screening | `vyapaar-data` | `MarketReader`, `ScreenerReader`, `MacroReader`, `ReferenceExporter` read ports in `vyapaar_data/ports/data_feeds.py`; `LakehouseMarketReader`, `VectorizedScreener`, `InMemoryReferenceExporter`, `PythonMacroReader` in `vyapaar_data/service/`; screener domain types (`ScreenQuery`, `ScreenCondition`, `ComparisonOp`); 16 tests in `tests/test_data_feeds.py`. |
| 0002 | Filings Ingestion, Economic Series Breadth | `vyapaar-data` | Macro series ingestion: `MacroObservation` domain, `DuckDbMacroStore`, `MacroSeriesRepository` port, `PythonMacroReader.get_series` (`tests/test_macro.py`); filings ingestion: `Filing`/`FilingType` domain, `DuckDbFilingsStore`, `FilingsRepository`/`FilingsReader` ports, `LakehouseFilingsReader` (`tests/test_filings.py`). Both gaps 0002 and 0003 closed. 18 new tests total. |

## Roadmap Dismantling Note

The historical roadmap (`docs/roadmap/roadmap.md`, `docs/roadmap/migration-verification.md`)
has been dismantled:
- Its two milestones (clean package layout & domain models; point-in-time corporate actions
  & quality suite) are complete and captured in `docs/design/code-migration-map.md` and
  `docs/design/architecture.md`.
- All remaining open work lives here as plans 0003–0006, tracking the open gaps in
  `docs/gaps/README.md`.
