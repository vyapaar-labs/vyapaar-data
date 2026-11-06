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


@dataclass(frozen=True, slots=True)
class InstrumentCoverage:
    """Coverage summary for a single instrument and interval."""

    instrument: str
    interval: str
    entry: CoverageEntry | None = None
    gaps: tuple[tuple[date, date], ...] = ()

    @property
    def is_covered(self) -> bool:
        """True if the instrument has at least one recorded row in the catalog."""
        return self.entry is not None and self.entry.row_count > 0

    @property
    def is_fully_covered(self) -> bool:
        """True if covered with no uncovered date gaps."""
        return self.is_covered and len(self.gaps) == 0

    @property
    def start(self) -> date | None:
        return self.entry.start if self.entry is not None else None

    @property
    def end(self) -> date | None:
        return self.entry.end if self.entry is not None else None

    @property
    def row_count(self) -> int:
        return self.entry.row_count if self.entry is not None else 0


@dataclass(frozen=True, slots=True)
class CoverageReport:
    """Consolidated coverage report across a target list of instruments."""

    catalog_root: str
    interval: str
    target_start: date | None = None
    target_end: date | None = None
    instruments: tuple[InstrumentCoverage, ...] = ()

    @property
    def total_count(self) -> int:
        return len(self.instruments)

    @property
    def covered_count(self) -> int:
        return sum(1 for item in self.instruments if item.is_covered)

    @property
    def missing_count(self) -> int:
        return sum(1 for item in self.instruments if not item.is_covered)

    @property
    def fully_covered_count(self) -> int:
        return sum(1 for item in self.instruments if item.is_fully_covered)

    @property
    def covered_symbols(self) -> tuple[str, ...]:
        return tuple(item.instrument for item in self.instruments if item.is_covered)

    @property
    def missing_symbols(self) -> tuple[str, ...]:
        return tuple(item.instrument for item in self.instruments if not item.is_covered)

    def summary_table(self) -> str:
        """Render a formatted ASCII table summarizing coverage."""
        target_span = (
            f"[{self.target_start.isoformat()} .. {self.target_end.isoformat()}]"
            if (self.target_start and self.target_end)
            else "unconstrained"
        )
        total = self.total_count
        covered = self.covered_count
        missing = self.missing_count
        hdr = f"{'Instrument':<18} {'Status':<10} {'Start':<12} {'End':<12} {'Rows':>8} {'Gaps':>6}"
        lines = [
            f"Catalog Root: {self.catalog_root}",
            f"Timeframe:    {self.interval}",
            f"Target Range: {target_span}",
            f"Coverage:     {covered}/{total} instruments present ({missing} missing)",
            "-" * 72,
            hdr,
            "-" * 72,
        ]
        for item in self.instruments:
            status = (
                "FULL" if item.is_fully_covered else ("PARTIAL" if item.is_covered else "MISSING")
            )
            start_str = item.start.isoformat() if item.start else "-"
            end_str = item.end.isoformat() if item.end else "-"
            rows_str = str(item.row_count) if item.is_covered else "0"
            gaps_str = str(len(item.gaps))
            row = (
                f"{item.instrument:<18} {status:<10} {start_str:<12} "
                f"{end_str:<12} {rows_str:>8} {gaps_str:>6}"
            )
            lines.append(row)
        lines.append("-" * 72)
        return "\n".join(lines)
