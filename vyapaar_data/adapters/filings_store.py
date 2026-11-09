"""DuckDB-backed regulatory filings store.

``DuckDbFilingsStore`` enforces the point-in-time invariant at query time: a
filing is visible for date ``D`` only when ``filing_date <= D``.
"""

from __future__ import annotations

from datetime import date

import duckdb

from vyapaar_data.domain.filings import Filing, FilingType

_FILINGS_DDL = """
CREATE TABLE IF NOT EXISTS filings (
    instrument   VARCHAR,
    filing_date  DATE,
    filing_type  VARCHAR,
    title        VARCHAR,
    source_url   VARCHAR
)
"""


class DuckDbFilingsStore:
    """Filings store on DuckDB."""

    def __init__(self, path: str = ":memory:") -> None:
        self._con = duckdb.connect(path)
        self._con.execute(_FILINGS_DDL)

    def upsert(self, filing: Filing) -> None:
        key = (filing.instrument, filing.filing_date, filing.title)
        self._con.execute(
            "DELETE FROM filings WHERE instrument = ? AND filing_date = ? AND title = ?",
            key,
        )
        self._con.execute(
            "INSERT INTO filings (instrument, filing_date, filing_type, title, source_url)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                filing.instrument,
                filing.filing_date,
                filing.filing_type.value,
                filing.title,
                filing.source_url,
            ),
        )

    def query(
        self,
        instrument: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        filing_type: FilingType | None = None,
    ) -> list[Filing]:
        sql = "SELECT instrument, filing_date, filing_type, title, source_url FROM filings"
        params: list[object] = []
        clauses: list[str] = []
        if instrument is not None:
            clauses.append("instrument = ?")
            params.append(instrument)
        if start_date is not None:
            clauses.append("filing_date >= ?")
            params.append(start_date)
        if end_date is not None:
            clauses.append("filing_date <= ?")
            params.append(end_date)
        if filing_type is not None:
            clauses.append("filing_type = ?")
            params.append(filing_type.value)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY filing_date"
        rows = self._con.execute(sql, params).fetchall()
        return [
            Filing(
                instrument=row[0],
                filing_date=row[1],
                filing_type=FilingType(row[2]),
                title=row[3],
                source_url=row[4],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._con.close()


__all__ = ["DuckDbFilingsStore"]
