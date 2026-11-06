# 0001 — Lakehouse & Port Architecture for MCP Quantitative Tools and Screening

> **Status**: Ready for implementation.
> **Target Crates**: `vyapaar-data`, `vyapaar-data-lakehouse`, `vyapaar-data-screener`.
> **Depends on reading**:
> - `vyapaar-agent/docs/plans/0001-mcp-gateway-discovery-and-quantitative-engines.md`
> - `vyapaar-data/docs/migration-guide.md`

---

## 0. Executive Summary & Objective

The Fincept MCP architectural model relies heavily on instant, high-throughput access to market history, fundamental metrics, option chains, and universe screening without crashing agent memory or exceeding LLM context limits.

To support the 15 quantitative engines in `vyapaar-agent` and the `$vyapaar/ref/...` data reference store, `vyapaar-data` must provide:
1. **Zero-Copy Analytical Data Feeds**: Exposing fast read ports (`MarketReader`, `ScreenerReader`, `MacroReader`) backed by Apache Arrow and Parquet lakehouse partitions.
2. **Multi-Field Screener Query Engine**: Enabling fast screening across 4,000 fundamental, technical, and liquidity dimensions for Indian equities and derivatives.
3. **Reference-Backed Query Serialization**: Emitting lightweight reference URIs that can be passed directly to downstream analytics crates (`vyapaar-agent-analytics`, `vyapaar-risk`) without serializing huge JSON arrays.
4. **Exact Decimal Preservation**: Enforcing exact `Decimal` precision in schemas (storing prices and quantities as `FixedSizeBinary` or integer scales) to uphold the Zero Floats Rule.

---

## 1. Data Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        vyapaar-data Lakehouse                          │
├───────────────────────────────────┬────────────────────────────────────┤
│         Time-Series Stores        │         Universe & Screener        │
│                                   │                                    │
│  • Parquet Daily & 1-Min Bars     │  • Fundamental Metrics Matrix      │
│  • NSE/BSE Equity & F&O Ticks     │  • Liquidity & Turnover Metrics    │
│  • Corporate Actions & Splits     │  • Macro Series (RBI, WPI, Yields) │
└─────────────────┬─────────────────┴──────────────────┬─────────────────┘
                  │                                    │
┌─────────────────▼────────────────────────────────────▼─────────────────┐
│                  Port Layer for vyapaar-agent-chat-tools               │
│                                                                        │
│   • MarketReader: get_quote, get_candles, get_returns, get_indicators  │
│   • ScreenerReader: execute_screen(universe, conditions, rank_by)      │
│   • MacroReader: get_series(series_id, start_date, end_date)           │
│   • ReferenceExporter: registers query results in DataReferenceStore   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Emits
┌───────────────────────────────────▼────────────────────────────────────┐
│         In-Memory Reference Handle ($vyapaar/ref/ohlcv/<uuid>)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Specifications

### 2.1 Screener Query Engine (`vyapaar-data-screener`)
Fincept allows screening across 4,000 fields using nested logical operators (`and`, `or`, `gt`, `crosses_above`). `vyapaar-data` implements this via a vectorized evaluation engine:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenQuery {
    pub universe: UniverseFilter, // e.g. "NIFTY50", "NIFTY_MIDCAP100", "NSE_FO"
    pub conditions: Vec<ScreenCondition>,
    pub order_by: String, // e.g. "pe_ratio ASC", "momentum_12m DESC"
    pub limit: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenCondition {
    pub field: String, // e.g. "market_cap", "rsi_14", "debt_to_equity"
    pub operator: ComparisonOp, // Gt, Lt, Gte, Lte, Eq, CrossesAbove, CrossesBelow
    pub value: ScreenValue, // Literal(Decimal) | Field(String)
}
```

### 2.2 Integration with `$vyapaar/ref/...`
When a query matches 200 instruments with 50 fields each:
- `execute_screen` writes the resulting Apache Arrow RecordBatch to the shared ephemeral reference cache.
- Returns a compact table block (Top 10 rows) and a reference handle:
  `$vyapaar/ref/screen_momentum_20261106`.
- Subsequent calls to `vyapaar_portfolio_optimize` or `vyapaar_backtest_run` can take this reference directly.

---

## 3. Implementation Phases

### Phase 1: Port Implementation
- Implement `MarketReader` and `SnapshotSource` traits backed by `vyapaar-data` lakehouse queries.
- Validate zero floating-point conversions.

### Phase 2: Vectorized Screener Engine
- Implement condition parser and filter evaluation over Parquet metadata and Arrow record batches.

### Phase 3: Reference Cache Exporter
- Connect `vyapaar-data` queries to `DataReferenceStore` in `vyapaar-agent-core`.
