"""Yahoo Finance (yfinance) symbol-profile provider.

Fetches company reference data (bio, sector / industry, CEO, employee count,
market cap, beta, dividend, 52-week range, active-trading flag) from
``yfinance.Ticker.info`` and maps it onto
:class:`~vyapaar_data.domain.profile.SymbolProfile` rows.

``yfinance`` is an optional dependency: if it is not installed, this module
degrades gracefully (``yfinance_available`` is ``False`` and
``fetch_symbol_profiles`` raises a clear ``ImportError``). Numeric fields that
yfinance does not populate are left as ``None``; every monetary / ratio value
is an exact ``decimal.Decimal``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    pass

try:  # yfinance is optional; degrade gracefully when unavailable
    import yfinance as yf

    _YFINANCE_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without yfinance installed
    yf = None
    _YFINANCE_AVAILABLE = False

_yfinance_available = _YFINANCE_AVAILABLE


@dataclass(frozen=True, slots=True)
class ProfileRow:
    """One raw symbol-profile row."""

    symbol: str
    name: str
    description: str
    ceo: str | None
    employees: str | None
    website: str | None
    headquarters: str | None
    industry: str | None
    sector: str | None
    ipo_date: str | None
    exchange: str | None
    country: str | None
    image: str | None
    market_cap: Decimal | None
    beta: Decimal | None
    last_dividend: Decimal | None
    range_52_week: str | None
    average_volume: int | None
    is_etf: bool
    is_actively_trading: bool


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)  # type: ignore[call-overload]  # value may be non-numeric
    except Exception:
        return None


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _bool_or_false(value: object) -> bool:
    if value is None:
        return False
    try:
        return bool(value)
    except Exception:
        return False


def _map_info(info: dict[str, object], symbol: str) -> ProfileRow:
    """Map a yfinance ``info`` dict onto a typed profile row."""
    officers = cast(list[object], info.get("companyOfficers") or [])
    ceo = None
    for officer in officers:
        if isinstance(officer, dict) and officer.get("title") in ("CEO", "Chief Executive Officer"):
            ceo = officer.get("name")
            break

    market_cap_raw = info.get("marketCap")
    beta_raw = info.get("beta")
    dividend_raw = info.get("trailingAnnualDividendRate") or info.get("dividendRate")
    avg_vol_raw = info.get("averageVolume") or info.get("averageVolume10Days")
    fifty_two_week = info.get("fiftyTwoWeekRange")
    ipo_epoch = info.get("firstTradeDateEpochUtc")
    ipo_date = None
    if ipo_epoch is not None:
        from datetime import UTC, datetime

        try:
            ipo_date = datetime.fromtimestamp(int(ipo_epoch), tz=UTC).date().isoformat()  # type: ignore[call-overload]
        except (ValueError, OSError, OverflowError, TypeError):
            ipo_date = None

    return ProfileRow(
        symbol=symbol,
        name=cast(str, info.get("longName") or info.get("shortName") or symbol),
        description=cast(str, info.get("longBusinessSummary") or ""),
        ceo=ceo,
        employees=str(info.get("fullTimeEmployees"))
        if info.get("fullTimeEmployees") is not None
        else None,
        website=_str_or_none(info.get("website")),
        headquarters=_str_or_none(info.get("headquarters")),
        industry=_str_or_none(info.get("industry")),
        sector=_str_or_none(info.get("sector")),
        ipo_date=ipo_date,
        exchange=_str_or_none(info.get("exchange")),
        country=_str_or_none(info.get("country")),
        image=_str_or_none(info.get("logo_url")),
        market_cap=_decimal_or_none(market_cap_raw),
        beta=_decimal_or_none(beta_raw),
        last_dividend=_decimal_or_none(dividend_raw),
        range_52_week=str(fifty_two_week) if fifty_two_week is not None else None,
        average_volume=_int_or_none(avg_vol_raw),
        is_etf=_bool_or_false(info.get("isEtf")),
        is_actively_trading=_bool_or_false(info.get("regularMarketActive")),
    )


def yfinance_available() -> bool:
    """Return ``True`` when the ``yfinance`` package is importable."""
    return _yfinance_available


def fetch_symbol_profiles(symbols: list[str]) -> list[ProfileRow]:
    """Fetch symbol profiles for ``symbols`` from yfinance.

    Raises :class:`ImportError` when ``yfinance`` is not installed. Unpopulated
    fields are left as ``None``.
    """
    if not _yfinance_available:
        raise ImportError(
            "yfinance is not installed; install it with `pip install yfinance` "
            "to fetch symbol profiles from Yahoo Finance"
        )
    rows: list[ProfileRow] = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            rows.append(_map_info(info, symbol))
        except Exception:  # yfinance is network-backed; one bad symbol must not abort the batch
            rows.append(
                ProfileRow(
                    symbol=symbol,
                    name=symbol,
                    description="",
                    ceo=None,
                    employees=None,
                    website=None,
                    headquarters=None,
                    industry=None,
                    sector=None,
                    ipo_date=None,
                    exchange=None,
                    country=None,
                    image=None,
                    market_cap=None,
                    beta=None,
                    last_dividend=None,
                    range_52_week=None,
                    average_volume=None,
                    is_etf=False,
                    is_actively_trading=False,
                )
            )
    return rows


def rows_to_profiles(rows: list[ProfileRow]) -> list:
    """Map parsed profile rows onto domain :class:`SymbolProfile` objects."""
    from vyapaar_data.domain.profile import SymbolProfile

    return [
        SymbolProfile(
            symbol=row.symbol,
            name=row.name,
            description=row.description,
            ceo=row.ceo,
            employees=row.employees,
            website=row.website,
            headquarters=row.headquarters,
            industry=row.industry,
            sector=row.sector,
            ipo_date=row.ipo_date,
            exchange=row.exchange,
            country=row.country,
            image=row.image,
            market_cap=row.market_cap,
            beta=row.beta,
            last_dividend=row.last_dividend,
            range_52_week=row.range_52_week,
            average_volume=row.average_volume,
            is_etf=row.is_etf,
            is_actively_trading=row.is_actively_trading,
        )
        for row in rows
    ]


__all__ = [
    "ProfileRow",
    "fetch_symbol_profiles",
    "rows_to_profiles",
    "yfinance_available",
]
