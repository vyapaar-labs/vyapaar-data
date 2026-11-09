"""Deterministic macroeconomic series parser.

Parses macro releases (RBI policy rates, WPI/CPI inflation, bond yields, etc.)
into :class:`~vyapaar_data.domain.macro.MacroObservation` rows with exact
``decimal.Decimal`` values.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from vyapaar_data.domain.macro import MacroObservation


@dataclass(frozen=True, slots=True)
class MacroRow:
    """One macro series line with an exact ``Decimal`` value."""

    series_id: str
    date: date
    value: Decimal
    source: str = "macro"


def _decimal(text: str, field: str) -> Decimal:
    try:
        return Decimal(text.strip())
    except Exception as exc:
        raise ValueError(f"invalid {field!r} value in macro data: {text!r}") from exc


def _date(text: str, field: str) -> date:
    text = text.strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"invalid {field!r} date in macro data: {text!r}")


def parse_macro(text: str) -> list[MacroRow]:
    """Parse raw macro CSV text into typed rows (header is mandatory)."""
    reader = csv.DictReader(line for line in text.splitlines() if line.strip())
    if reader.fieldnames is None or not reader.fieldnames:
        raise ValueError("macro data is empty or missing a header")
    rows: list[MacroRow] = []
    for raw in reader:
        if not any(raw.values()):
            continue
        rows.append(
            MacroRow(
                series_id=raw["series_id"].strip(),
                date=_date(raw["date"], "date"),
                value=_decimal(raw["value"], "value"),
                source=raw.get("source", "macro").strip() or "macro",
            )
        )
    return rows


def read_macro(path: str | Path) -> list[MacroRow]:
    """Read and parse a macro CSV file from disk."""
    with open(path, encoding="utf-8") as handle:
        return parse_macro(handle.read())


def rows_to_observations(rows: list[MacroRow]) -> list[MacroObservation]:
    """Map parsed macro rows onto domain observations."""
    return [
        MacroObservation(
            series_id=r.series_id,
            as_of_date=r.date,
            value=r.value,
            source=r.source,
        )
        for r in rows
    ]


__all__ = ["MacroRow", "parse_macro", "read_macro", "rows_to_observations"]
