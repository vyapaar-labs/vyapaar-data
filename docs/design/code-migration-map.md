# `vyapaar-data` — Historical Migration Map (honba-data → vyapaar-data)

> **Tier**: Tier 6A
> **Source**: `honba-workspace/honba-data`
> **Target**: `vyapaar-data`
> **Status**: Migration complete.

## Migration & DDD Refactoring Steps

### 1. Fix `pyproject.toml`

- Replace invalid `"rust_decimal>=1.0.0"` in `vyapaar-data/pyproject.toml` with standard Python dependencies (`duckdb>=1.0.0`, `polars>=1.0.0`, `pyarrow>=15.0.0`, `pydantic>=2.0.0`).

### 2. Port Source Tree

- Copy `honba-workspace/honba-data/src/honba_data/*` into `vyapaar-labs/vyapaar-data/vyapaar_data/`.
- Replace `honba_data` → `vyapaar_data` and `honba` → `vyapaar` across all `.py` files.

### 3. Port Tests & Scripts

- Copy `honba-workspace/honba-data/tests/*` into `vyapaar-labs/vyapaar-data/tests/` and `scripts/` into `vyapaar-data/scripts/`.
- Ensure zero test files sit at the repository root.

## Verification Commands

```bash
# Run from the repository root
pytest -q
ruff check .
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
