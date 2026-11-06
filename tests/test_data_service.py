"""Unified data service: corporate-action back-adjustment of history."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from vyapaar_data import VyapaarDataService
from vyapaar_data.domain.corporate_actions import Split


def build_service(
    catalog, corporate_actions_store, fundamentals_store, actions, bars
) -> VyapaarDataService:
    for action in actions:
        corporate_actions_store.add(action)
    catalog.write_bars("NSE:RELIANCE-EQ", bars)
    return VyapaarDataService(
        corporate_actions=corporate_actions_store,
        fundamentals=fundamentals_store,
        catalog=catalog,
    )


def test_adjusted_history_applies_split_and_dividend(
    catalog, corporate_actions_store, fundamentals_store, sample_bars, sample_actions
) -> None:
    service = build_service(
        catalog, corporate_actions_store, fundamentals_store, sample_actions, sample_bars
    )
    adjusted = service.adjusted_history("NSE:RELIANCE-EQ")
    closes = adjusted.sort("ts")["close"].to_list()

    # 2023-12-28 bar: both a 1:2 split (multiply by 1/2) and a Rs.10 dividend
    # are applied: (1250 * 0.5) - 10 = 615.00
    # 2023-12-29 bar: (1260 * 0.5) - 10 = 620.00
    # 2024-01-02 bar: ex-date of split -> only the dividend: 1270 - 10 = 1260.00
    # 2024-01-03 bar: ex-date of dividend -> raw close: 1280.00
    assert closes == [
        Decimal("615.0000"),
        Decimal("620.0000"),
        Decimal("1260.0000"),
        Decimal("1280.0000"),
    ]


def test_adjusted_history_restates_volume_for_split(
    catalog, corporate_actions_store, fundamentals_store, sample_bars
) -> None:
    actions = [Split("NSE:RELIANCE-EQ", date(2024, 1, 2), old_shares=1, new_shares=2)]
    service = build_service(
        catalog, corporate_actions_store, fundamentals_store, actions, sample_bars
    )
    adjusted = service.adjusted_history("NSE:RELIANCE-EQ").sort("ts")
    volumes = adjusted["volume"].to_list()
    assert volumes == [
        Decimal("2000000.0000"),
        Decimal("2000000.0000"),
        Decimal("1000000.0000"),
        Decimal("1000000.0000"),
    ]


def test_coverage_reports_catalog_window(
    catalog, corporate_actions_store, fundamentals_store, sample_bars
) -> None:
    service = build_service(catalog, corporate_actions_store, fundamentals_store, [], sample_bars)
    coverage = service.coverage("NSE:RELIANCE-EQ")
    assert coverage is not None
    assert coverage.start == date(2023, 12, 28)
    assert coverage.end == date(2024, 1, 3)
    assert coverage.row_count == 4
