"""Macroeconomic series observations.

Zero-floats invariant: every macro value is a ``decimal.Decimal``. Value objects
are frozen, self-validating dataclasses that compare by value.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from vyapaar_data._compat import to_decimal


@dataclass(frozen=True, slots=True)
class MacroObservation:
    """A single macroeconomic observation (e.g. RBI repo rate, WPI inflation)."""

    series_id: str
    as_of_date: date
    value: Decimal
    source: str = "macro"

    def __post_init__(self) -> None:
        if not self.series_id:
            raise ValueError("series_id must be non-empty")
        object.__setattr__(self, "value", to_decimal(self.value))
