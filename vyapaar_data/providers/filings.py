"""Deterministic regulatory filings parser.

Parses SEBI/BSE/NSE corporate filings (shareholding, insider trades, fund
holdings, quarterly results, annual reports) into
:class:`~vyapaar_data.domain.filings.Filing` rows.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from vyapaar_data.domain.filings import Filing, FilingType


@dataclass(frozen=True, slots=True)
class FilingRow:
    """One filings line."""

    instrument: str
    filing_date: date
    filing_type: str
    title: str
    source_url: str | None = None


def _date(text: str, field: str) -> date:
    text = text.strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"invalid {field!r} date in filings data: {text!r}")


def parse_filings(text: str) -> list[FilingRow]:
    """Parse raw filings CSV text into typed rows (header is mandatory)."""
    reader = csv.DictReader(line for line in text.splitlines() if line.strip())
    if reader.fieldnames is None or not reader.fieldnames:
        raise ValueError("filings data is empty or missing a header")
    rows: list[FilingRow] = []
    for raw in reader:
        if not any(raw.values()):
            continue
        rows.append(
            FilingRow(
                instrument=raw["instrument"].strip(),
                filing_date=_date(raw["filing_date"], "filing_date"),
                filing_type=raw.get("filing_type", "other").strip() or "other",
                title=raw["title"].strip(),
                source_url=raw.get("source_url", "").strip() or None,
            )
        )
    return rows


def read_filings(path: str | Path) -> list[FilingRow]:
    """Read and parse a filings CSV file from disk."""
    with open(path, encoding="utf-8") as handle:
        return parse_filings(handle.read())


def rows_to_filings(rows: list[FilingRow]) -> list[Filing]:
    """Map parsed filings rows onto domain filings."""
    filings: list[Filing] = []
    for row in rows:
        try:
            filing_type = FilingType(row.filing_type)
        except ValueError:
            filing_type = FilingType.OTHER
        filings.append(
            Filing(
                instrument=row.instrument,
                filing_date=row.filing_date,
                filing_type=filing_type,
                title=row.title,
                source_url=row.source_url,
            )
        )
    return filings


__all__ = ["FilingRow", "parse_filings", "read_filings", "rows_to_filings"]
