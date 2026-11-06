# 0002 — Filings Ingestion, Economic Series Breadth (Deferred Items)

> **Status**: Proposed — not yet implemented.
> **Target**: `vyapaar-data`.
> **Depends on reading**:
> - `vyapaar-data/docs/plans/0001-mcp-market-and-screener-data-feed-ports.md`

---

## 0. Executive Summary & Objective

Two Fincept toolset gaps touch `vyapaar-data` that `0001` doesn't cover: `filings`
(SEC-EDGAR-style regulatory filings/insiders/funds — India's equivalent would be BSE/NSE/SEBI
corporate filings) and broader cross-provider economic series, beyond `0001`'s current
point-in-time corporate-actions/splits/dividends scope. This is a deferred-items note, not a new
active engine — neither gap has a concrete consumer yet.

---

## 1. Context

`0001` scoped `vyapaar-data`'s lakehouse read-ports (`MarketReader`, `ScreenerReader`,
`MacroReader`) for the 15 quantitative engines in `vyapaar-agent`. Fincept's toolset additionally
exposes `filings` (regulatory filings, insider transactions, fund holdings) and a wider set of
cross-provider economic series than `0001` scoped. Both are real gaps relative to Fincept's
surface, but neither has a concrete consumer inside Vyapaar today.

Fincept's `deals` toolset (M&A, comps, private raises) is recorded here as a deliberate
**non-goal** — out of scope for a trading platform's data layer unless someone later decides
otherwise.

---

## 2. Component Specifications

None proposed. This doc intentionally stops short of specifying `FilingsReader` or an expanded
`MacroReader` surface — see Phase 1 below.

---

## 3. Implementation Phases

### Phase 1 (deferred)
Revisit filings ingestion once a concrete consumer (e.g. a fundamentals-driven screener field, or
a research-loop hypothesis needing filing data) actually needs it — do not build a generic filings
pipeline speculatively.
