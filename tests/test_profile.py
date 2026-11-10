"""Symbol profile ingestion (gap 0002): domain, yfinance provider, DuckDB
store, and LakehouseProfileReader service.

Profile data is sourced from Yahoo Finance (yfinance) when available; the
provider degrades gracefully when yfinance is not installed.
"""

from __future__ import annotations

from decimal import Decimal

from vyapaar_data import (
    DuckDbProfileStore,
    LakehouseProfileReader,
    SymbolProfile,
    rows_to_profiles,
    yfinance_available,
)
from vyapaar_data.providers.profile import ProfileRow, _map_info


def test_symbol_profile_validation() -> None:
    profile = SymbolProfile(
        symbol="NSE:RELIANCE-EQ",
        name="Reliance Industries Ltd.",
        description="Integrated energy conglomerate.",
        ceo="Mukesh Ambani",
        employees="347000",
        website="https://www.ril.com",
        headquarters="Mumbai, India",
        industry="Oil & Gas",
        sector="Energy",
        ipo_date="1977-10-01",
        exchange="NSE",
        country="IN",
        image="https://logo.clearbit.com/ril.com",
        market_cap=Decimal("1800000000000.00"),
        beta=Decimal("0.95"),
        last_dividend=Decimal("10.00"),
        range_52_week="2400.00 - 3100.00",
        average_volume=5_000_000,
        is_etf=False,
        is_actively_trading=True,
    )
    assert profile.symbol == "NSE:RELIANCE-EQ"
    assert profile.market_cap == Decimal("1800000000000.00")
    assert profile.beta == Decimal("0.95")
    assert profile.is_etf is False
    assert profile.is_actively_trading is True


def test_symbol_profile_rejects_empty_symbol() -> None:
    try:
        SymbolProfile(symbol="", name="X", description="")
    except ValueError as exc:
        assert "symbol" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError for empty symbol")


def test_map_info_extracts_yfinance_fields() -> None:
    info = {
        "longName": "Apple Inc.",
        "shortName": "Apple",
        "longBusinessSummary": "Apple designs and sells consumer electronics.",
        "companyOfficers": [
            {"name": "Tim Cook", "title": "CEO"},
            {"name": "Luca Maestri", "title": "CFO"},
        ],
        "fullTimeEmployees": 164000,
        "website": "https://www.apple.com",
        "headquarters": "Cupertino, California",
        "industry": "Consumer Electronics",
        "sector": "Technology",
        "firstTradeDateEpochUtc": 1234567890,
        "exchange": "NASDAQ",
        "country": "US",
        "logo_url": "https://logo.clearbit.com/apple.com",
        "marketCap": 3500000000000.0,
        "beta": 1.2,
        "trailingAnnualDividendRate": 0.92,
        "fiftyTwoWeekRange": "150.00 - 250.00",
        "averageVolume": 55_000_000,
        "isEtf": False,
        "regularMarketActive": True,
    }
    row = _map_info(info, "AAPL")
    assert row.symbol == "AAPL"
    assert row.name == "Apple Inc."
    assert row.description.startswith("Apple designs")
    assert row.ceo == "Tim Cook"
    assert row.employees == "164000"
    assert row.sector == "Technology"
    assert row.industry == "Consumer Electronics"
    assert row.market_cap == Decimal("3500000000000.0")
    assert row.beta == Decimal("1.2")
    assert row.last_dividend == Decimal("0.92")
    assert row.range_52_week == "150.00 - 250.00"
    assert row.average_volume == 55_000_000
    assert row.is_etf is False
    assert row.is_actively_trading is True


def test_rows_to_profiles_round_trip() -> None:
    row = ProfileRow(
        symbol="NSE:TCS-EQ",
        name="Tata Consultancy Services",
        description="IT services.",
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
        is_actively_trading=True,
    )
    profiles = rows_to_profiles([row])
    assert len(profiles) == 1
    assert profiles[0].symbol == "NSE:TCS-EQ"
    assert profiles[0].market_cap is None
    assert profiles[0].is_etf is False


def test_yfinance_available_flag() -> None:
    # yfinance is installed in this environment.
    assert yfinance_available() is True


def test_profile_store_upsert_and_query() -> None:
    store = DuckDbProfileStore(":memory:")
    profile = SymbolProfile(
        symbol="NSE:RELIANCE-EQ",
        name="Reliance Industries Ltd.",
        description="Integrated energy conglomerate.",
        sector="Energy",
        industry="Oil & Gas",
    )
    store.upsert(profile)

    rows = store.query(symbol="NSE:RELIANCE-EQ")
    assert len(rows) == 1
    assert rows[0].name == "Reliance Industries Ltd."
    assert rows[0].sector == "Energy"

    rows = store.query(sector="Energy")
    assert len(rows) == 1

    rows = store.query(symbol="NSE:NOPE-EQ")
    assert rows == []

    store.close()


def test_profile_store_upsert_is_idempotent() -> None:
    store = DuckDbProfileStore(":memory:")
    profile = SymbolProfile(
        symbol="NSE:RELIANCE-EQ",
        name="Reliance Industries Ltd.",
        description="v1",
    )
    store.upsert(profile)
    store.upsert(
        SymbolProfile(
            symbol="NSE:RELIANCE-EQ",
            name="Reliance Industries Ltd.",
            description="v2",
        )
    )
    rows = store.query(symbol="NSE:RELIANCE-EQ")
    assert len(rows) == 1
    assert rows[0].description == "v2"
    store.close()


def test_lakehouse_profile_reader() -> None:
    store = DuckDbProfileStore(":memory:")
    profile = SymbolProfile(
        symbol="NSE:RELIANCE-EQ",
        name="Reliance Industries Ltd.",
        description="Integrated energy conglomerate.",
    )
    store.upsert(profile)
    reader = LakehouseProfileReader(store)

    got = reader.get_profile("NSE:RELIANCE-EQ")
    assert got is not None
    assert got.symbol == "NSE:RELIANCE-EQ"
    assert got.name == "Reliance Industries Ltd."

    assert reader.get_profile("NSE:NOPE-EQ") is None

    profiles = reader.get_profiles(symbols=["NSE:RELIANCE-EQ"])
    assert len(profiles) == 1

    profiles = reader.get_profiles()
    assert len(profiles) == 1

    store.close()
