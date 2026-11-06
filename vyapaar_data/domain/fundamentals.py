"""Point-in-time fundamental records.

A ``FundamentalRecord`` pairs the *period* being reported (``period_end_date``)
with the *filing* date on which the disclosure became public. As-of queries must
filter on ``filing_date`` so a backtest on date ``D`` can never observe a
financial fact that was not yet filed — this is the core anti-look-ahead-bias
invariant of the lakehouse.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from vyapaar_data._compat import to_decimal


@dataclass(frozen=True, slots=True)
class FundamentalRecord:
    """A single disclosed fundamental metric for one period."""

    instrument: str
    period_end_date: date
    filing_date: date
    metric: str
    value: Decimal

    def __post_init__(self) -> None:
        if self.filing_date < self.period_end_date:
            raise ValueError(
                "filing_date must be >= period_end_date "
                "(a metric cannot be filed before its period ends; "
                "this guard prevents look-ahead bias)"
            )
        if not self.metric:
            raise ValueError("metric must be non-empty")
        object.__setattr__(self, "value", to_decimal(self.value))
