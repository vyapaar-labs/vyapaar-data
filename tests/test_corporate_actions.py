"""Value-object invariants for corporate actions (zero floats, validation)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from vyapaar_data.domain.corporate_actions import (
    Bonus,
    Dividend,
    Rights,
    Split,
    from_record,
    to_record,
)

D = Decimal


def test_split_1_5_price_and_quantity_multipliers() -> None:
    split = Split("NSE:RELIANCE-EQ", date(2024, 1, 2), old_shares=1, new_shares=5)
    assert split.price_multiplier == D("0.2")
    assert split.quantity_multiplier == D("5")
    assert split.apply(D("100.00")) == D("20.00")


def test_split_rejects_invalid_factors() -> None:
    with pytest.raises(ValueError):
        Split("X", date(2024, 1, 2), old_shares=0, new_shares=5)
    with pytest.raises(ValueError):
        Split("X", date(2024, 1, 2), old_shares=2, new_shares=2)


def test_bonus_1_1_halves_price() -> None:
    bonus = Bonus("NSE:RELIANCE-EQ", date(2024, 3, 1), old_shares=1, new_shares=2)
    assert bonus.price_multiplier == D("0.5")
    assert bonus.quantity_multiplier == D("2")
    assert bonus.apply(D("500.00")) == D("250.00")


def test_dividend_subtracts_per_share() -> None:
    dividend = Dividend("NSE:RELIANCE-EQ", date(2024, 1, 3), per_share="10.00")
    assert dividend.price_adjustment == D("10.00")
    assert dividend.apply(D("260.00")) == D("250.00")
    with pytest.raises(ValueError):
        Dividend("X", date(2024, 1, 3), per_share="-1.00")


def test_rights_theoretical_price() -> None:
    rights = Rights("NSE:XYZ", date(2024, 5, 1), old_shares=4, new_shares=1, issue_price="300.00")
    # (500*4 + 300*1) / 5
    assert rights.apply(D("500.00")) == D("460.00")


def test_record_roundtrip_preserves_exact_decimals() -> None:
    for action in [
        Split("NSE:A", date(2024, 1, 2), 1, 5),
        Bonus("NSE:B", date(2024, 2, 1), 1, 2),
        Dividend("NSE:C", date(2024, 3, 1), per_share="10.50"),
        Rights("NSE:D", date(2024, 4, 1), 4, 1, issue_price="300.00"),
    ]:
        assert from_record(to_record(action)) == action
