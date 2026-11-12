# 0014 — Delivery percentage / delivery-adjusted volume ingestion

**Status**: open

## What's stubbed or hardcoded

This repo has no delivery-quantity or delivery-percentage data source at all: no repository
port, no reader, no Parquet catalog table, and no such field on any existing DTO. A repo-wide
grep for `delivery` across `vyapaar-data` finds zero matches; the same is true in
`vyapaar-agent-chat-tools`'s `MarketBar`/`MarketQuote` DTOs
(`vyapaar-agent/crates/vyapaar-agent-chat-tools/src/ports/market.rs`), which carry only
`volume: Quantity` — the raw traded quantity, not the NSE Bhavcopy "Deliverable Quantity /
Traded Quantity" ratio. Delivery percentage is the standard mechanism for distinguishing real
accumulation/distribution (shares actually changing hands into demat, implying intent to hold)
from intraday churn (the same shares bought and sold same-day, netting to zero delivery) — it
is the core signal most "big player"/"elephant" volume-anomaly screens use, and this workspace
has no way to compute it today.

## Why

`vyapaar-agent/docs/plans/0010-institutional-smart-money-detection-suite.md` scopes a
`delivery_analysis` chat tool and uses delivery-adjusted volume as one leg of its composite
smart-money signal; both need this repo to be the actual data source, per this workspace's
gap-tracking rule (`.agents/rules/gap-tracking.md` §5).

Like FII/DII flows ([0013](0013-fii-dii-institutional-flow-ingestion.md)) and block/bulk deals
([0005](0005-block-bulk-deal-disclosure-ingestion.md)), delivery data is public exchange data
— NSE's daily Bhavcopy / "Security-wise Delivery Position" report (and BSE's equivalent)
publish per-symbol traded quantity and deliverable quantity with no vendor licensing involved.
The open decision here is which exchange to ingest from first, the exact file/feed shape
(columns, publish time, historical backfill depth — verify against the live source rather than
assuming), and how it joins to this repo's existing bar/instrument catalog.

Target shape (per-symbol, per-day record): trade date, instrument identifier, traded quantity,
deliverable quantity, delivery percentage (`deliverable_qty / traded_qty * 100`, computed as
exact `Decimal`, never a float ratio). This should be modeled so it can later join cleanly
against this repo's existing daily-bar catalog on `(instrument, date)`.

## How to close it

1. Decide the ingestion source (NSE Bhavcopy delivery report first) and verify the live
   disclosure shape (columns, file format, publish time, historical backfill availability)
   against the exchange's current feed — do not assume a shape or URL without checking it live.
2. Add a `DeliveryRepository` port under `vyapaar_data/ports/repositories.py`, following the
   same shape as the existing `MacroSeriesRepository`
   (`vyapaar_data/ports/repositories.py`).
3. Add a `PythonDeliveryReader` (or similarly named) service in
   `vyapaar_data/service/delivery_reader.py`, returning a Polars `DataFrame` with the target
   shape above (exact `Decimal` delivery-percentage column, per this repo's existing readers'
   convention).
4. Land the ingested data in this repo's existing Parquet catalog pattern (`data/catalog/`),
   keyed so it joins against the existing daily-bar catalog on `(instrument, date)`.
5. Once this lands, `vyapaar-agent/docs/plans/0010-institutional-smart-money-detection-suite.md`
   Phase 2's `delivery_analysis` chat tool can replace its `PortError::unavailable`
   stand-in with a real read.

No code should be written against this gap document until the ingestion-source decision above
is made; it is documentation only, recording the decision point and target shape.
