"""Point-in-time fundamentals: look-ahead guard and as-of querying."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from vyapaar_data.domain.fundamentals import FundamentalRecord


def test_look_ahead_guard_rejects_early_filing() -> None:
    with pytest.raises(ValueError):
        FundamentalRecord(
            instrument="NSE:RELIANCE-EQ",
            period_end_date=date(2024, 3, 31),
            filing_date=date(2024, 1, 15),
            metric="net_profit",
            value="100.00",
        )


def test_record_coerces_value_to_decimal(fundamentals_store) -> None:
    record = FundamentalRecord(
        instrument="NSE:RELIANCE-EQ",
        period_end_date=date(2024, 3, 31),
        filing_date=date(2024, 4, 25),
        metric="net_profit",
        value="72100.00",
    )
    assert record.value == Decimal("72100.00")


def test_upsert_is_idempotent_and_as_of_query_respects_filing_date(
    fundamentals_store, sample_fundamentals
) -> None:
    for record in sample_fundamentals:
        fundamentals_store.upsert(record)
    fundamentals_store.upsert(sample_fundamentals[0])  # same key -> replace

    # As of Jan 25 2024 only the first filing is visible.
    visible = fundamentals_store.query("NSE:RELIANCE-EQ", as_of=date(2024, 1, 25))
    assert len(visible) == 1
    assert visible[0].value == Decimal("68000.00")

    # As of May 1 2024 both filings are visible.
    later = fundamentals_store.query("NSE:RELIANCE-EQ", as_of=date(2024, 5, 1))
    assert len(later) == 2

    # Metric filtering.
    metric = fundamentals_store.query("NSE:RELIANCE-EQ", as_of=date(2024, 5, 1), metric="revenue")
    assert metric == []
