# `vyapaar-data` — Subagent Migration & DDD Refactoring Guide

> **Tier**: Tier 6A
> **Source**: `/home/pmallapp/Devel/Finance/honba-workspace/honba-data`
> **Target**: `/home/pmallapp/Devel/Finance/vyapaar-labs/vyapaar-data`

---

## 1. Migration & DDD Refactoring Steps
1. **Fix `pyproject.toml`**:
   - Replace invalid `"rust_decimal>=1.0.0"` in `vyapaar-data/pyproject.toml` with standard Python dependencies (`duckdb>=1.0.0`, `polars>=1.0.0`, `pyarrow>=15.0.0`, `pydantic>=2.0.0`).
2. **Port Source Tree**:
   - Copy `honba-workspace/honba-data/src/honba_data/*` into `vyapaar-labs/vyapaar-data/vyapaar_data/`.
   - Replace `honba_data` → `vyapaar_data` and `honba` → `vyapaar` across all `.py` files.
3. **Port Tests & Scripts**:
   - Copy `honba-workspace/honba-data/tests/*` into `vyapaar-labs/vyapaar-data/tests/` and `scripts/` into `vyapaar-data/scripts/`.
   - Ensure zero test files sit at the repository root.

## 2. Verification Commands
```bash
cd /home/pmallapp/Devel/Finance/vyapaar-labs/vyapaar-data
pytest -q
ruff check .
```
