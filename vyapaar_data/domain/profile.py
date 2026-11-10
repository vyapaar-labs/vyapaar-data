"""Company symbol profile / fundamentals reference data.

A ``SymbolProfile`` is point-in-time company reference data (bio, sector /
industry classification, CEO, employee count, market cap, beta, dividend,
52-week range, active-trading flag) — distinct from ``FundamentalRecord``
(period-end financial-statement metrics such as net_profit / revenue with
filing dates). Profiles are heavier, rarer-fetched reference payloads, not
real-time market data.

Zero-floats invariant: every monetary or ratio value is an exact
``decimal.Decimal``. Value objects are frozen, self-validating dataclasses
that compare by value. Numeric fields are optional (``Decimal | None``) because
an external profile source may not populate every field.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from vyapaar_data._compat import to_decimal


@dataclass(frozen=True, slots=True)
class SymbolProfile:
    """One company symbol profile, mirroring the vela.luxalgo.com
    ``GET /api/markets/public-get-symbol-profile`` contract."""

    symbol: str
    name: str
    description: str
    ceo: str | None = None
    employees: str | None = None
    website: str | None = None
    headquarters: str | None = None
    industry: str | None = None
    sector: str | None = None
    ipo_date: str | None = None
    exchange: str | None = None
    country: str | None = None
    image: str | None = None
    market_cap: Decimal | None = None
    beta: Decimal | None = None
    last_dividend: Decimal | None = None
    range_52_week: str | None = None
    average_volume: int | None = None
    is_etf: bool = False
    is_actively_trading: bool = True

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol must be non-empty")
        if not self.name:
            raise ValueError("name must be non-empty")
        object.__setattr__(
            self,
            "market_cap",
            self.market_cap if self.market_cap is None else to_decimal(self.market_cap),
        )
        object.__setattr__(self, "beta", self.beta if self.beta is None else to_decimal(self.beta))
        object.__setattr__(
            self,
            "last_dividend",
            self.last_dividend if self.last_dividend is None else to_decimal(self.last_dividend),
        )


__all__ = ["SymbolProfile"]
