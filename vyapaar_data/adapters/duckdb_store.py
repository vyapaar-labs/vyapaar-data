"""DuckDB-backed point-in-time stores.

``DuckDbFundamentalsStore`` enforces the point-in-time invariant at query time:
a record is visible as of date ``D`` only when ``filing_date <= D``. Values are
stored as exact fixed-point ``DECIMAL`` columns — never floating point.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import duckdb

from vyapaar_data.domain.corporate_actions import (
    CorporateAction,
    CorporateActionRecord,
    CorporateActionType,
    from_record,
    to_record,
)
from vyapaar_data.domain.fundamentals import FundamentalRecord

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
