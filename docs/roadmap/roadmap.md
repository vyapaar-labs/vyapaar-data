# `vyapaar-data` — TDD & Engineering Roadmap

## Milestone 1: Clean Package Layout & Domain Models (P0)
- [ ] Fix `pyproject.toml` (remove invalid `rust_decimal` PyPI dependency; declare `duckdb`, `polars`, `pyarrow`, `pydantic`).
- [ ] Port `domain/`, `ports/`, `adapters/`, `providers/`, `coverage/`, `service/`, and `cli/` into `vyapaar_data/`.

## Milestone 2: Point-in-Time Corporate Actions & Quality Suite (P0)
- [ ] Port all unit, property, and integration tests into `tests/`.
- [ ] Verify `pytest -q` and `ruff check .` pass with 0 warnings.
