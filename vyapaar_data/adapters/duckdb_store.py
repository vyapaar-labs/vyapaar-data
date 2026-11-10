"""DuckDB-backed point-in-time stores.

``DuckDbFundamentalsStore`` enforces the point-in-time invariant at query time:
a record is visible as of date ``D`` only when ``filing_date <= D``. Values are
stored as exact fixed-point ``DECIMAL`` columns — never floating point.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import duckdb

from vyapaar_data.domain.calendar import CalendarEvent
from vyapaar_data.domain.corporate_actions import (
    CorporateAction,
    CorporateActionRecord,
    CorporateActionType,
    from_record,
    to_record,
)
from vyapaar_data.domain.fundamentals import FundamentalRecord
from vyapaar_data.domain.profile import SymbolProfile

_FUNDAMENTALS_DDL = """
CREATE TABLE IF NOT EXISTS fundamentals (
    instrument    VARCHAR,
    period_end    DATE,
    filing_date   DATE,
    metric        VARCHAR,
    value         DECIMAL(38, 10)
)
"""

_CORPORATE_ACTIONS_DDL = """
CREATE TABLE IF NOT EXISTS corporate_actions (
    instrument   VARCHAR,
    action_type  VARCHAR,
    ex_date      DATE,
    old_shares   INTEGER,
    new_shares   INTEGER,
    per_share    DECIMAL(18, 4),
    issue_price  DECIMAL(18, 4),
    currency     VARCHAR
)
"""

_CALENDAR_DDL = """
CREATE TABLE IF NOT EXISTS calendar_events (
    instrument     VARCHAR,
    scheduled_at   TIMESTAMP,
    country        VARCHAR,
    currency       VARCHAR,
    category       VARCHAR,
    event_name     VARCHAR,
    impact_level   VARCHAR,
    actual         DECIMAL(38, 10),
    forecast       DECIMAL(38, 10),
    prior          DECIMAL(38, 10),
    period_label   VARCHAR
)
"""

_PROFILE_DDL = """
CREATE TABLE IF NOT EXISTS symbol_profiles (
    symbol            VARCHAR,
    name              VARCHAR,
    description       VARCHAR,
    ceo               VARCHAR,
    employees         VARCHAR,
    website           VARCHAR,
    headquarters      VARCHAR,
    industry          VARCHAR,
    sector            VARCHAR,
    ipo_date          VARCHAR,
    exchange          VARCHAR,
    country           VARCHAR,
    image             VARCHAR,
    market_cap        DECIMAL(38, 10),
    beta              DECIMAL(38, 10),
    last_dividend     DECIMAL(38, 10),
    range_52_week     VARCHAR,
    average_volume    INTEGER,
    is_etf            BOOLEAN,
    is_actively_trading BOOLEAN
)
"""


def _ensure_utc(value: object) -> datetime:
    """Coerce a DuckDB timestamp into a timezone-aware UTC datetime."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    raise ValueError(f"expected datetime, got {type(value).__name__}")


class DuckDbFundamentalsStore:
    """Point-in-time fundamental store on DuckDB."""

    def __init__(self, path: str = ":memory:") -> None:
        self._con = duckdb.connect(path)
        self._con.execute(_FUNDAMENTALS_DDL)

    def upsert(self, record: FundamentalRecord) -> None:
        key = (record.instrument, record.period_end_date, record.filing_date, record.metric)
        self._con.execute(
            "DELETE FROM fundamentals"
            " WHERE instrument = ? AND period_end = ? AND filing_date = ? AND metric = ?",
            key,
        )
        self._con.execute(
            "INSERT INTO fundamentals"
            " (instrument, period_end, filing_date, metric, value) VALUES (?, ?, ?, ?, ?)",
            (
                record.instrument,
                record.period_end_date,
                record.filing_date,
                record.metric,
                record.value,
            ),
        )

    def query(
        self,
        instrument: str,
        as_of: date,
        metric: str | None = None,
    ) -> list[FundamentalRecord]:
        if metric is not None:
            rows = self._con.execute(
                "SELECT instrument, period_end, filing_date, metric, value"
                " FROM fundamentals"
                " WHERE instrument = ? AND filing_date <= ? AND metric = ?"
                " ORDER BY period_end, filing_date",
                (instrument, as_of, metric),
            ).fetchall()
        else:
            rows = self._con.execute(
                "SELECT instrument, period_end, filing_date, metric, value"
                " FROM fundamentals"
                " WHERE instrument = ? AND filing_date <= ?"
                " ORDER BY period_end, filing_date",
                (instrument, as_of),
            ).fetchall()
        return [
            FundamentalRecord(
                instrument=row[0],
                period_end_date=row[1],
                filing_date=row[2],
                metric=row[3],
                value=Decimal(row[4]),
            )
            for row in rows
        ]

    def close(self) -> None:
        self._con.close()


class DuckDbCalendarStore:
    """Calendar events store on DuckDB."""

    def __init__(self, path: str = ":memory:") -> None:
        self._con = duckdb.connect(path)
        self._con.execute(_CALENDAR_DDL)

    def upsert(self, event: CalendarEvent) -> None:
        self._con.execute(
            "DELETE FROM calendar_events"
            " WHERE instrument IS NOT DISTINCT FROM ? AND scheduled_at = ? AND event_name = ?",
            (event.instrument, event.scheduled_at, event.event_name),
        )
        self._con.execute(
            "INSERT INTO calendar_events"
            " (instrument, scheduled_at, country, currency, category, event_name,"
            " impact_level, actual, forecast, prior, period_label)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event.instrument,
                event.scheduled_at,
                event.country,
                event.currency,
                event.category,
                event.event_name,
                event.impact_level,
                event.actual,
                event.forecast,
                event.prior,
                event.period_label,
            ),
        )

    def query(
        self,
        instrument: str | None = None,
        category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[CalendarEvent]:
        sql = (
            "SELECT instrument, scheduled_at, country, currency, category, event_name,"
            " impact_level, actual, forecast, prior, period_label FROM calendar_events"
        )
        params: list[object] = []
        clauses: list[str] = []
        if instrument is not None:
            clauses.append("instrument IS NOT DISTINCT FROM ?")
            params.append(instrument)
        if category is not None:
            clauses.append("category = ?")
            params.append(category)
        if start_date is not None:
            clauses.append("CAST(scheduled_at AS DATE) >= ?")
            params.append(start_date)
        if end_date is not None:
            clauses.append("CAST(scheduled_at AS DATE) <= ?")
            params.append(end_date)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY scheduled_at, event_name"
        rows = self._con.execute(sql, params).fetchall()
        return [
            CalendarEvent(
                instrument=row[0],
                scheduled_at=_ensure_utc(row[1]),
                country=row[2],
                currency=row[3],
                category=row[4],
                event_name=row[5],
                impact_level=row[6],
                actual=None if row[7] is None else Decimal(str(row[7])),
                forecast=None if row[8] is None else Decimal(str(row[8])),
                prior=None if row[9] is None else Decimal(str(row[9])),
                period_label=row[10],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._con.close()


class DuckDbProfileStore:
    """Symbol profiles store on DuckDB."""

    def __init__(self, path: str = ":memory:") -> None:
        self._con = duckdb.connect(path)
        self._con.execute(_PROFILE_DDL)

    def upsert(self, profile: SymbolProfile) -> None:
        self._con.execute("DELETE FROM symbol_profiles WHERE symbol = ?", (profile.symbol,))
        self._con.execute(
            "INSERT INTO symbol_profiles"
            " (symbol, name, description, ceo, employees, website, headquarters,"
            " industry, sector, ipo_date, exchange, country, image, market_cap,"
            " beta, last_dividend, range_52_week, average_volume, is_etf,"
            " is_actively_trading)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                profile.symbol,
                profile.name,
                profile.description,
                profile.ceo,
                profile.employees,
                profile.website,
                profile.headquarters,
                profile.industry,
                profile.sector,
                profile.ipo_date,
                profile.exchange,
                profile.country,
                profile.image,
                profile.market_cap,
                profile.beta,
                profile.last_dividend,
                profile.range_52_week,
                profile.average_volume,
                profile.is_etf,
                profile.is_actively_trading,
            ),
        )

    def query(
        self,
        symbol: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
    ) -> list[SymbolProfile]:
        sql = (
            "SELECT symbol, name, description, ceo, employees, website, headquarters,"
            " industry, sector, ipo_date, exchange, country, image, market_cap,"
            " beta, last_dividend, range_52_week, average_volume, is_etf,"
            " is_actively_trading FROM symbol_profiles"
        )
        params: list[object] = []
        clauses: list[str] = []
        if symbol is not None:
            clauses.append("symbol = ?")
            params.append(symbol)
        if sector is not None:
            clauses.append("sector = ?")
            params.append(sector)
        if industry is not None:
            clauses.append("industry = ?")
            params.append(industry)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY symbol"
        rows = self._con.execute(sql, params).fetchall()
        return [
            SymbolProfile(
                symbol=row[0],
                name=row[1],
                description=row[2],
                ceo=row[3],
                employees=row[4],
                website=row[5],
                headquarters=row[6],
                industry=row[7],
                sector=row[8],
                ipo_date=row[9],
                exchange=row[10],
                country=row[11],
                image=row[12],
                market_cap=None if row[13] is None else Decimal(str(row[13])),
                beta=None if row[14] is None else Decimal(str(row[14])),
                last_dividend=None if row[15] is None else Decimal(str(row[15])),
                range_52_week=row[16],
                average_volume=None if row[17] is None else int(row[17]),
                is_etf=bool(row[18]),
                is_actively_trading=bool(row[19]),
            )
            for row in rows
        ]

    def close(self) -> None:
        self._con.close()


class DuckDbCorporateActionsStore:
    """Corporate action store on DuckDB."""

    def __init__(self, path: str = ":memory:") -> None:
        self._con = duckdb.connect(path)
        self._con.execute(_CORPORATE_ACTIONS_DDL)

    def add(self, action: CorporateAction) -> None:
        record = to_record(action)
        self._con.execute(
            "DELETE FROM corporate_actions"
            " WHERE instrument = ? AND action_type = ? AND ex_date = ?",
            (record.instrument, record.action_type.value, record.ex_date),
        )
        self._con.execute(
            "INSERT INTO corporate_actions"
            " (instrument, action_type, ex_date, old_shares, new_shares, per_share,"
            " issue_price, currency)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.instrument,
                record.action_type.value,
                record.ex_date,
                record.old_shares,
                record.new_shares,
                record.per_share,
                record.issue_price,
                record.currency,
            ),
        )

    def list(
        self, instrument: str | None = None, as_of: date | None = None
    ) -> list[CorporateAction]:
        sql = (
            "SELECT instrument, action_type, ex_date, old_shares, new_shares, per_share,"
            " issue_price, currency FROM corporate_actions"
        )
        params: list[object] = []
        clauses: list[str] = []
        if instrument is not None:
            clauses.append("instrument = ?")
            params.append(instrument)
        if as_of is not None:
            clauses.append("ex_date <= ?")
            params.append(as_of)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY ex_date"
        rows = self._con.execute(sql, params).fetchall()
        return [
            from_record(
                CorporateActionRecord(
                    instrument=row[0],
                    action_type=CorporateActionType(row[1]),
                    ex_date=row[2],
                    old_shares=row[3],
                    new_shares=row[4],
                    per_share=None if row[5] is None else Decimal(row[5]),
                    issue_price=None if row[6] is None else Decimal(row[6]),
                    currency=row[7],
                )
            )
            for row in rows
        ]

    def close(self) -> None:
        self._con.close()


__all__ = [
    "DuckDbCalendarStore",
    "DuckDbCorporateActionsStore",
    "DuckDbFundamentalsStore",
    "DuckDbProfileStore",
]
