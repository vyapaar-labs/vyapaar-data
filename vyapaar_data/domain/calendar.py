"""Scheduled economic/earnings/dividends/splits/IPO calendar events.

A ``CalendarEvent`` is a forward-looking, multi-category scheduled-events
calendar entry: an upcoming (or recently-released) economic release, earnings
report, dividend/split corporate action, or IPO, each with its own release
datetime, impact level, and actual/forecast/prior values.

This domain is intentionally distinct from ``FundamentalRecord`` (point-in-time
financial-statement metrics) and ``CorporateAction`` (ex-date price/volume
adjustments): a calendar event is a *scheduled* announcement, not an executed
corporate action, and it carries forecast/actual values plus an impact badge.

Zero-floats invariant: every numeric value is an exact ``decimal.Decimal``.
Value objects are frozen, self-validating dataclasses that compare by value.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from vyapaar_data._compat import to_decimal

_VALID_CATEGORIES = ("Economic", "Earnings", "Dividends", "Splits", "IPO")
_VALID_IMPACT_LEVELS = ("High", "Medium", "Low")


@dataclass(frozen=True, slots=True)
class CalendarEvent:
    """One scheduled calendar event (economic release, earnings, dividend,
    split, or IPO)."""

    instrument: str | None
    """Affected instrument symbol (e.g. ``"NSE:RELIANCE-EQ"`` for an earnings
    release); ``None`` for pure macroeconomic events."""

    scheduled_at: datetime
    """Release datetime (timezone-aware UTC)."""

    country: str
    """Country code (e.g. ``"IN"``, ``"US"``)."""

    currency: str
    """Currency code (e.g. ``"INR"``, ``"USD"``)."""

    category: str
    """Event category: one of ``Economic``, ``Earnings``, ``Dividends``,
    ``Splits``, ``IPO``."""

    event_name: str
    """Human-readable event name (e.g. ``"GDP Growth Rate QoQ"``)."""

    impact_level: str
    """Impact badge: one of ``High``, ``Medium``, ``Low``."""

    actual: Decimal | None
    """Released actual value (``None`` before the event occurs)."""

    forecast: Decimal | None
    """Consensus forecast value."""

    prior: Decimal | None
    """Prior-period value."""

    period_label: str | None
    """Period label (e.g. ``"Oct"``, ``"Q3"``, ``"Nov/06"``)."""

    def __post_init__(self) -> None:
        if self.category not in _VALID_CATEGORIES:
            raise ValueError(
                f"invalid category {self.category!r}; must be one of {_VALID_CATEGORIES}"
            )
        if self.impact_level not in _VALID_IMPACT_LEVELS:
            raise ValueError(
                f"invalid impact_level {self.impact_level!r}; must be one of {_VALID_IMPACT_LEVELS}"
            )
        if not self.event_name:
            raise ValueError("event_name must be non-empty")
        if not self.country:
            raise ValueError("country must be non-empty")
        if not self.currency:
            raise ValueError("currency must be non-empty")
        if self.scheduled_at.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")
        object.__setattr__(
            self, "actual", self.actual if self.actual is None else to_decimal(self.actual)
        )
        object.__setattr__(
            self, "forecast", self.forecast if self.forecast is None else to_decimal(self.forecast)
        )
        object.__setattr__(
            self, "prior", self.prior if self.prior is None else to_decimal(self.prior)
        )


__all__ = ["CalendarEvent"]
