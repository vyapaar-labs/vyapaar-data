"""Coverage ledger: tracks data availability across the lakehouse.

A coverage ledger entry records the contiguous ``[start, end]`` window of data
known to exist for an instrument+interval. The ledger answers the question
"what date ranges are NOT covered?" so ingestion jobs and researchers can spot
missing history immediately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class CoverageEntry:
    """Contiguous coverage window for one instrument+interval."""

    instrument: str
    interval: str
    start: date
    end: date
    row_count: int = 0
    updated_at: datetime = field(default_factory=lambda: _EPOCH)

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("coverage end must be >= start")
        if self.row_count < 0:
            raise ValueError("row_count must be non-negative")


@dataclass(frozen=True, slots=True)
class CoverageLedger:
    """Immutable set of coverage entries with gap discovery."""

    entries: tuple[CoverageEntry, ...] = ()

    def for_instrument(self, instrument: str, interval: str) -> tuple[CoverageEntry, ...]:
        return tuple(
            e for e in self.entries if e.instrument == instrument and e.interval == interval
        )

    def covered(self, instrument: str, interval: str, day: date) -> bool:
        return any(e.start <= day <= e.end for e in self.for_instrument(instrument, interval))

    def gaps(
        self,
        instrument: str,
        interval: str,
        start: date,
        end: date,
    ) -> list[tuple[date, date]]:
        """Return uncovered half-open-free ranges within ``[start, end]``."""
        if end < start:
            raise ValueError("end must be >= start")
        spans = sorted(
            (e.start, e.end)
            for e in self.for_instrument(instrument, interval)
            if e.end >= start and e.start <= end
        )
        gaps: list[tuple[date, date]] = []
        cursor = start
        for span_start, span_end in spans:
            if span_start > cursor:
                gaps.append((cursor, span_start - timedelta(days=1)))
            if span_end + timedelta(days=1) > cursor:
                cursor = span_end + timedelta(days=1)
            if cursor > end:
                break
        if cursor <= end:
            gaps.append((cursor, end))
        return gaps
