"""Regulatory filings reader (SEBI/BSE/NSE equivalent of EDGAR)."""

from __future__ import annotations

from datetime import date

from vyapaar_data.domain.filings import Filing, FilingType
from vyapaar_data.ports.repositories import FilingsRepository


class LakehouseFilingsReader:
    """Filings reader backed by a filings repository."""

    def __init__(self, repository: FilingsRepository) -> None:
        self.repository = repository

    def list_filings(
        self,
        instrument: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        filing_type: FilingType | None = None,
    ) -> list[Filing]:
        """Return filings, optionally filtered by instrument/date/type.

        Filings are point-in-time: a filing is visible for date ``D`` only when
        ``filing_date <= D``.
        """
        return self.repository.query(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            filing_type=filing_type,
        )


__all__ = ["LakehouseFilingsReader"]
