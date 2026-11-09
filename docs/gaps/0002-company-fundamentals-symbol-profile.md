# 0002 — Company fundamentals / symbol profile ingestion

**Status**: open

## What's stubbed or hardcoded

No company-fundamentals/profile lookup exists in this repo today: no bio,
sector/industry classification, CEO, employee count, market cap, beta,
dividend, 52-week range, or active-trading flag per symbol. There is no
reader port and no Parquet catalog entry for this kind of point-in-time
company reference data.

## Why

Both `vyapaar-ui-web` (its own
`docs/plans/0011-vela-journal-calendar-reports-domain-model.md`) and
`vyapaar-runtime` (its own
`docs/plans/0003-trade-journal-and-market-reference-rest-endpoints.md`, which
would add a symbol-profile REST endpoint backed by this repo) need a company
fundamentals/profile lookup. Per this workspace's gap-tracking rule
(`.agents/rules/gap-tracking.md` §5), the root cause — no data source for this
category — is filed here, in the repo responsible for point-in-time reference
data, rather than stubbed in either consumer.

The target shape was reverse-engineered live from vela.luxalgo.com's own
`GET /api/markets/public-get-symbol-profile?symbols=AAPL,NVDA` endpoint
(observed 2026-11-09), quoted verbatim below:

```json
{"data":{"profiles":[{"symbol":"AAPL","profile":{
  "symbol":"AAPL","name":"Apple Inc.","description":"<long text bio>","ceo":"...","employees":"...",
  "website":"...","headquarters":"...","industry":"...","sector":"...","ipoDate":"...",
  "exchange":"...","country":"...","image":"<logo URL>","marketCap":"...","beta":"...",
  "lastDividend":"...","range":"<52-week range>","averageVolume":"...","isEtf":false,"isActivelyTrading":true
}}]}}}
```

This is point-in-time reference/fundamental data (company bio, sector/industry
classification, market cap, beta, dividend, 52-week range, active-trading
flag) — not real-time market data — so it fits this repo's "Data Lakehouse" /
"Point-in-time corporate actions" responsibility, not `vyapaar-market`'s
real-time tick/WebSocket responsibility.

## How to close it

Ingest point-in-time company reference data per the exact field list in the
JSON shape quoted above: `symbol`, `name`, `description`, `ceo`, `employees`,
`website`, `headquarters`, `industry`, `sector`, `ipoDate`, `exchange`,
`country`, `image` (logo URL), `marketCap`, `beta`, `lastDividend`, `range`
(52-week range), `averageVolume`, `isEtf`, `isActivelyTrading`.

This needs an external data source/vendor decision that has **not** been made
yet — flagged here as open, no vendor name should be invented or assumed.

Once a source is chosen, this should extend this repo's existing
catalog/reader-port pattern — the same shape as the `MacroReader` and
`FilingsReader` ports from this repo's own closed gaps 0002/0003 (see the
Closed gaps table in `docs/gaps/README.md`) — e.g. a new `ProfileReader` (or
`FundamentalsReader`) port, so `vyapaar-runtime` can read it the same way.
No code should be written against this gap document; it is documentation
only, recording the decision point and target shape.
