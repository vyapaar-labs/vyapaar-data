# `vyapaar-data` — Migration Verification Milestone

Verification commands for the `honba-data → vyapaar-data` migration:

```bash
cd /home/pmallapp/Devel/Finance/vyapaar-labs/vyapaar-data
pytest -q
ruff check .
```

## Migration Milestone Status

| Milestone | Status |
|-----------|--------|
| `pyproject.toml` fixed | Complete |
| Source tree ported | Complete |
| Tests & scripts ported | Complete |
| `pytest -q` | Passing |
| `ruff check .` | Clean |
