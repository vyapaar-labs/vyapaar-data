"""Macro series reader (RBI, WPI, yields, etc.).

Reads macro observations from a
:class:`~vyapaar_data.ports.repositories.MacroSeriesRepository` and returns them
as Polars frames with exact ``Decimal(18,4)`` values.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import polars as pl

from vyapaar_data.ports.repositories import MacroSeriesRepository


class PythonMacroReader:
    """Macro reader backed by a macro series repository."""

    def __init__(self, repository: MacroSeriesRepository) -> None:
        self.repository = repository

    def get_series(
        self,
        series_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pl.DataFrame:
        """Macro series ``series_id`` over ``[start_date, end_date]``.

        Returns an empty canonical frame when no observations exist for the
        requested window. All values are exact ``Decimal(18,4)`` (zero floats).
        """
        observations = self.repository.query(series_id, start_date, end_date)
        if not observations:
            return pl.DataFrame(
                {
                    "ts": [],
                    "series_id": [],
                    "value": [],
                },
                schema={
                    "ts": pl.Datetime("us"),
                    "series_id": pl.String,
                    "value": pl.Decimal(18, 4),
                },
            )
        return pl.DataFrame(
            {
                "ts": [datetime.combine(o.as_of_date, time.min, tzinfo=UTC) for o in observations],
                "series_id": [o.series_id for o in observations],
                "value": [o.value for o in observations],
            },
            schema={
                "ts": pl.Datetime("us"),
                "series_id": pl.String,
                "value": pl.Decimal(18, 4),
            },
        )


__all__ = ["PythonMacroReader"]
