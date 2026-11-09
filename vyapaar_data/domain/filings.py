"""Regulatory filings value objects.

Zero-floats invariant: filing records carry no float quantities; every value is
an exact string or ``decimal.Decimal``. Value objects are frozen, self-validating
dataclasses that compare by value.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class FilingType(Enum):
    """Canonical classification of a regulatory filing."""

    CORPORATE_ACTION = "corporate_action"
    SHAREHOLDING = "shareholding"
    INSIDER_TRADE = "insider_trade"
    FUND_HOLDING = "fund_holding"
    ANNUAL_REPORT = "annual_report"
    QUARTERLY_RESULT = "quarterly_result"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Filing:
    """A single disclosed regulatory filing (SEBI/BSE/NSE equivalent of EDGAR)."""

    instrument: str
    filing_date: date
    filing_type: FilingType
    title: str
    source_url: str | None = None

    def __post_init__(self) -> None:
        if not self.instrument:
            raise ValueError("instrument must be non-empty")
        if not self.title:
            raise ValueError("title must be non-empty")
