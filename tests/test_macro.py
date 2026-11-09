"""Macro series ingestion: provider, DuckDB store, and PythonMacroReader."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import polars as pl

from vyapaar_data import MacroObservation, PythonMacroReader
from vyapaar_data.providers.macro import MacroRow, parse_macro, rows_to_observations


def test_macro_store_upsert_and_query(macro_store, sample_macro_rows):
    for obs in sample_macro_rows:
        macro_store.upsert(obs)

    rows = macro_store.query("RBI_REPO_RATE")
    assert len(rows) == 2
    assert rows[0].series_id == "RBI_REPO_RATE"
    assert rows[0].as_of_date == date(2024, 1, 1)
    assert rows[0].value == Decimal("6.50")
    assert rows[1].value == Decimal("6.75")


def test_macro_store_date_window_filters(macro_store, sample_macro_rows):
    for obs in sample_macro_rows:
        macro_store.upsert(obs)

    rows = macro_store.query("RBI_REPO_RATE", start_date=date(2024, 1, 15))
    assert len(rows) == 1
    assert rows[0].as_of_date == date(2024, 2, 1)

    rows = macro_store.query("RBI_REPO_RATE", end_date=date(2024, 1, 15))
    assert len(rows) == 1
    assert rows[0].as_of_date == date(2024, 1, 1)


def test_macro_store_unknown_series_returns_empty(macro_store):
    assert macro_store.query("DOES_NOT_EXIST") == []


def test_macro_store_upsert_is_idempotent(macro_store):
    obs = MacroObservation("RBI_REPO_RATE", date(2024, 1, 1), "6.50", "rbi")
    macro_store.upsert(obs)
    macro_store.upsert(MacroObservation("RBI_REPO_RATE", date(2024, 1, 1), "7.00", "rbi"))
    rows = macro_store.query("RBI_REPO_RATE")
    assert len(rows) == 1
    assert rows[0].value == Decimal("7.00")


def test_python_macro_reader_get_series(macro_store, sample_macro_rows):
    for obs in sample_macro_rows:
        macro_store.upsert(obs)
    reader = PythonMacroReader(macro_store)

    frame = reader.get_series("RBI_REPO_RATE")
    assert frame.columns == ["ts", "series_id", "value"]
    assert frame["value"].dtype == pl.Decimal(18, 4)
    assert frame["series_id"].to_list() == ["RBI_REPO_RATE", "RBI_REPO_RATE"]
    assert frame["value"].to_list() == [Decimal("6.5000"), Decimal("6.7500")]


def test_python_macro_reader_get_series_date_window(macro_store, sample_macro_rows):
    for obs in sample_macro_rows:
        macro_store.upsert(obs)
    reader = PythonMacroReader(macro_store)

    frame = reader.get_series(
        "RBI_REPO_RATE", start_date=date(2024, 1, 15), end_date=date(2024, 2, 1)
    )
    assert len(frame) == 1
    assert frame["value"].to_list() == [Decimal("6.7500")]


def test_python_macro_reader_empty_when_no_data(macro_store):
    reader = PythonMacroReader(macro_store)
    frame = reader.get_series("MISSING")
    assert frame.is_empty()
    assert frame.columns == ["ts", "series_id", "value"]
    assert frame["value"].dtype == pl.Decimal(18, 4)


def test_parse_macro_csv():
    text = (
        "series_id,date,value,source\n"
        "RBI_REPO_RATE,01-Feb-2024,6.75,rbi\n"
        "WPI_INFLATION,15-Jan-2024,0.70,eaindustry.nic.in\n"
    )
    rows = parse_macro(text)
    assert len(rows) == 2
    assert rows[0] == MacroRow("RBI_REPO_RATE", date(2024, 2, 1), Decimal("6.75"), "rbi")
    assert rows[1].value == Decimal("0.70")


def test_rows_to_observations_round_trip():
    rows = [MacroRow("RBI_REPO_RATE", date(2024, 1, 1), Decimal("6.50"), "rbi")]
    obs = rows_to_observations(rows)
    assert len(obs) == 1
    assert obs[0].series_id == "RBI_REPO_RATE"
    assert obs[0].as_of_date == date(2024, 1, 1)
    assert obs[0].value == Decimal("6.50")


def test_macro_values_are_decimal_never_float(macro_store):
    macro_store.upsert(MacroObservation("RBI_REPO_RATE", date(2024, 1, 1), "6.50", "rbi"))
    reader = PythonMacroReader(macro_store)
    frame = reader.get_series("RBI_REPO_RATE")
    assert frame["value"].dtype == pl.Decimal(18, 4)
    assert all(isinstance(v, Decimal) for v in frame["value"].to_list())
