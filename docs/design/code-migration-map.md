# `vyapaar-data` — Historical Migration Map (honba-data → vyapaar-data)

> **Tier**: Tier 6A
> **Source**: `honba-workspace/honba-data`
> **Target**: `vyapaar-data`
> **Status**: Migration complete & expanded. The historical roadmap
> (`docs/roadmap/`) has been dismantled into `docs/design/`, `docs/gaps/`, and
> `docs/plans/`.

## Migration & DDD Refactoring Steps

### 1. Fix `pyproject.toml`

- Replace invalid `"rust_decimal>=1.0.0"` in `vyapaar-data/pyproject.toml` with standard Python dependencies (`duckdb>=1.0.0`, `polars>=1.0.0`, `pyarrow>=15.0.0`, `pydantic>=2.0.0`).
- `vyapaar>=0.1.0` is optional under `[project.optional-dependencies].native` (runtime fallback in `_compat.py`); dev extras `pytest`, `ruff`, `mypy`.

### 2. Port Source Tree

- Copy `honba-workspace/honba-data/src/honba_data/*` into `vyapaar-labs/vyapaar-data/vyapaar_data/`.
- Replace `honba_data` → `vyapaar_data` and `honba` → `vyapaar` across all `.py` files.

### 3. Port Tests & Scripts

- Copy `honba-workspace/honba-data/tests/*` into `vyapaar-labs/vyapaar-data/tests/`; ensure zero test files sit at the repository root.

## Post-Migration Expansion

Since the port, `vyapaar_data/` has grown well beyond the ported core via gap/plan work
(see `docs/plans/README.md`):

| Area | Added | Landed Via |
|------|-------|------------|
| Read ports & screener | `MarketReader`, `ScreenerReader`, `MacroReader`, `ReferenceExporter` + `ScreenQuery`/`ScreenCondition`/`ComparisonOp`; `LakehouseMarketReader`, `VectorizedScreener`, `InMemoryReferenceExporter` | plan 0001 |
| Macro series | `MacroObservation`, `MacroSeriesRepository`, `DuckDbMacroStore`, `PythonMacroReader.get_series`, macro CSV provider | gap 0002 (closed) |
| Filings | `Filing`/`FilingType`, `FilingsRepository`, `DuckDbFilingsStore`, `LakehouseFilingsReader`, filings CSV provider | gap 0003 (closed) |
| Calendar | `CalendarEvent`, `CalendarRepository`/`CalendarReader`, `DuckDbCalendarStore`, `LakehouseCalendarReader`, calendar CSV provider (currently stubbed — gap 0012) | gap 0010 (real ingestion open) |
| Symbol profile | `SymbolProfile`, `ProfileRepository`/`ProfileReader`, `DuckDbProfileStore`, `LakehouseProfileReader`, yfinance provider | gap 0011 (closed) |
| Coverage reporting | `CoverageLedger`/`CoverageReport`, `vyapaar-coverage` CLI | gap 0001 (closed) |

## Verification Commands

```bash
# Run from the repository root
pytest -q
ruff check .
ruff format --check .
mypy vyapaar_data
```

## Migration Milestone Status

| Milestone | Status |
|-----------|--------|
| `pyproject.toml` fixed (`rust_decimal` replaced with standard Python deps) | Complete |
| Source tree ported (`vyapaar_data/` package) | Complete |
| Tests & scripts ported | Complete |
| Zero test files at repo root | Complete |
| `pytest -q` | Passing |
| `ruff check .` | Clean |
