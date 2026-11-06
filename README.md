# Vyapaar Data (`vyapaar-data`)

**Bounded Context**: Point-in-Time Financial Lakehouse & Corporate Actions (Tier 6A)

`vyapaar-data` is the Python + DuckDB + Polars + PyArrow lakehouse that powers
look-ahead-bias-free research and backtests for the Vyapaar Labs ecosystem:

- **Corporate actions** — splits, bonuses, dividends, and rights issues as
  self-validating `Decimal` value objects with exact back-adjustment math.
- **Point-in-time fundamentals** — every `FundamentalRecord` carries both a
  `period_end_date` and a `filing_date`; as-of queries only ever surface facts
  that were publicly filed by the query date (no look-ahead bias).
- **Coverage ledgers** — track data availability across instruments, intervals,
  and date ranges and report uncovered gaps.
- **Parquet catalog** — Hive-partitioned columnar storage with
  `DECIMAL128(18,4)` pricing columns (zero `float` in any financial column).
- **NSE bhavcopy provider** — deterministic CSV parser that ingests official
  `cm` bhavcopy files into the catalog.

## Layout (4-Zone Clean Package)

```
vyapaar-data/
├── vyapaar_data/          # Zone 1: package (domain / ports / adapters / providers / service)
├── tests/                 # Zone 2: offline test suite (parallel to the package)
├── configs/               # Zone 3: catalog / lakehouse configuration templates
└── docs/                  # Zone 4: architecture & migration guides
```

## Zero-Floats Policy

All prices, adjusted payouts, split ratios, and fundamental values are
`decimal.Decimal` end-to-end. Columnar storage uses Arrow `decimal128(18,4)`;
there is no `f32`/`f64` in any financial path.

## Quick Start

```python
from vyapaar_data import (
    DuckDbFundamentalsStore,
    DuckDbCorporateActionsStore,
    ParquetCatalog,
    VyapaarDataService,
)

service = VyapaarDataService(
    fundamentals=DuckDbFundamentalsStore(":memory:"),
    corporate_actions=DuckDbCorporateActionsStore(":memory:"),
    catalog=ParquetCatalog("data/catalog"),
)

history = service.adjusted_history("NSE:RELIANCE-EQ")  # restated to current basis
```

## Development

```bash
make test      # pytest -q
make lint      # ruff check .
make check     # lint + format-check + type-check + tests
```

## Verification Gate

```bash
pytest -q
ruff check .
```
