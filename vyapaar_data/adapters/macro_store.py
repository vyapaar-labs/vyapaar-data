"""DuckDB-backed macro series store.

``DuckDbMacroStore`` enforces the point-in-time invariant at query time: an
observation is visible for date ``D`` only when ``as_of_date <= D``. Values are
stored as exact fixed-point ``DECIMAL`` columns — never floating point.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import duckdb

from vyapaar_data.domain.macro import MacroObservation

_MACRO_SERIES_DDL = """
CREATE TABLE IF NOT EXISTS macro_series (
    series_id   VARCHAR,
    as_of_date  DATE,
    value       DECIMAL(38, 10),
    source      VARCHAR
)
"""


class DuckDbMacroStore:
    """Macro series store on DuckDB."""

    def __init__(self, path: str = ":memory:") -> None:
        self._con = duckdb.connect(path)
        self._con.execute(_MACRO_SERIES_DDL)

    def upsert(self, observation: MacroObservation) -> None:
        key = (observation.series_id, observation.as_of_date)
        self._con.execute(
            "DELETE FROM macro_series WHERE series_id = ? AND as_of_date = ?",
            key,
        )
        self._con.execute(
            "INSERT INTO macro_series (series_id, as_of_date, value, source) VALUES (?, ?, ?, ?)",
            (
                observation.series_id,
                observation.as_of_date,
                observation.value,
                observation.source,
            ),
        )

    def query(
        self,
        series_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[MacroObservation]:
        sql = "SELECT series_id, as_of_date, value, source FROM macro_series WHERE series_id = ?"
        params: list[object] = [series_id]
        if start_date is not None:
            sql += " AND as_of_date >= ?"
            params.append(start_date)
        if end_date is not None:
            sql += " AND as_of_date <= ?"
            params.append(end_date)
        sql += " ORDER BY as_of_date"
        rows = self._con.execute(sql, params).fetchall()
        return [
            MacroObservation(
                series_id=row[0],
                as_of_date=row[1],
                value=Decimal(row[2]),
                source=row[3],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._con.close()


__all__ = ["DuckDbMacroStore"]
