# Plans Index — `vyapaar-data`

Per workspace rule `.agents/rules/gap-tracking.md`:
- Gaps are individual features (`docs/gaps/XXXX-*.md`).
- Plans are collections of gaps (`docs/plans/XXXX-*.md`).
- When implemented, plan documents are cleaned up from `docs/plans/` and recorded in this index.

## Active Plans

## Implemented Plans

| # | Title | Target Scope | Implemented In |
|---|-------|--------------|----------------|
| 0001 | Lakehouse & Port Architecture for MCP Quantitative Tools and Screening | `vyapaar-data` | `MarketReader`, `ScreenerReader`, `MacroReader`, `ReferenceExporter` read ports in `vyapaar_data/ports/data_feeds.py`; `LakehouseMarketReader`, `VectorizedScreener`, `InMemoryReferenceExporter`, `PythonMacroReader` in `vyapaar_data/service/`; screener domain types (`ScreenQuery`, `ScreenCondition`, `ComparisonOp`); 16 tests in `tests/test_data_feeds.py`. |
| 0002 | Filings Ingestion, Economic Series Breadth | `vyapaar-data` | Macro series ingestion: `MacroObservation` domain, `DuckDbMacroStore`, `MacroSeriesRepository` port, `PythonMacroReader.get_series` (`tests/test_macro.py`); filings ingestion: `Filing`/`FilingType` domain, `DuckDbFilingsStore`, `FilingsRepository`/`FilingsReader` ports, `LakehouseFilingsReader` (`tests/test_filings.py`). Both gaps 0002 and 0003 closed. 18 new tests total. |
