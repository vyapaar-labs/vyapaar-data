"""vyapaar-data — Point-in-Time Financial Lakehouse & Corporate Actions.

Tier 6A bounded context. Domain value objects are pure and self-validating;
ports are protocols; adapters implement DuckDB/Parquet storage; providers ingest
official NSE files; the service facade composes everything into a
look-ahead-bias-free data service.
"""

from __future__ import annotations

from vyapaar_data._compat import VYAAPAAR_AVAILABLE
from vyapaar_data.adapters import (
    DuckDbCalendarStore,
    DuckDbCorporateActionsStore,
    DuckDbFilingsStore,
    DuckDbFundamentalsStore,
    DuckDbMacroStore,
    DuckDbProfileStore,
    ParquetCatalog,
)
from vyapaar_data.domain.calendar import CalendarEvent
from vyapaar_data.domain.corporate_actions import (
    Bonus,
    CorporateAction,
    CorporateActionRecord,
    CorporateActionType,
    Dividend,
    Rights,
    Split,
    from_record,
    to_record,
)
from vyapaar_data.domain.coverage import (
    CoverageEntry,
    CoverageLedger,
    CoverageReport,
    InstrumentCoverage,
)
from vyapaar_data.domain.filings import Filing, FilingType
from vyapaar_data.domain.fundamentals import FundamentalRecord
from vyapaar_data.domain.macro import MacroObservation
from vyapaar_data.domain.profile import SymbolProfile
from vyapaar_data.ports.data_feeds import (
    CalendarReader,
    ComparisonOp,
    FilingsReader,
    MacroReader,
    MarketReader,
    ProfileReader,
    ReferenceExporter,
    ScreenCondition,
    ScreenerReader,
    ScreenQuery,
    ScreenResult,
    ScreenValue,
)
from vyapaar_data.ports.repositories import (
    CalendarRepository,
    FilingsRepository,
    MacroSeriesRepository,
    ProfileRepository,
)
from vyapaar_data.providers.bhavcopy import (
    BhavcopyRow,
    parse_bhavcopy,
    read_bhavcopy,
    rows_to_bars,
)
from vyapaar_data.providers.calendar import (
    CalendarRow,
    parse_calendar,
    read_calendar,
    rows_to_events,
    stubbed_calendar_rows,
)
from vyapaar_data.providers.filings import (
    FilingRow,
    parse_filings,
    read_filings,
    rows_to_filings,
)
from vyapaar_data.providers.macro import (
    MacroRow,
    parse_macro,
    read_macro,
    rows_to_observations,
)
from vyapaar_data.providers.profile import (
    ProfileRow,
    fetch_symbol_profiles,
    rows_to_profiles,
    yfinance_available,
)
from vyapaar_data.service.calendar_reader import LakehouseCalendarReader
from vyapaar_data.service.data_service import VyapaarDataService
from vyapaar_data.service.filings_reader import LakehouseFilingsReader
from vyapaar_data.service.macro_reader import PythonMacroReader
from vyapaar_data.service.market_reader import LakehouseMarketReader
from vyapaar_data.service.profile_reader import LakehouseProfileReader
from vyapaar_data.service.reference_exporter import InMemoryReferenceExporter
from vyapaar_data.service.screener import VectorizedScreener

__version__ = "0.1.0"

__all__ = [
    "VYAAPAAR_AVAILABLE",
    "BhavcopyRow",
    "Bonus",
    "CalendarEvent",
    "CalendarReader",
    "CalendarRepository",
    "CalendarRow",
    "ComparisonOp",
    "CorporateAction",
    "CorporateActionRecord",
    "CorporateActionType",
    "CoverageEntry",
    "CoverageLedger",
    "CoverageReport",
    "Dividend",
    "DuckDbCalendarStore",
    "DuckDbCorporateActionsStore",
    "DuckDbFilingsStore",
    "DuckDbFundamentalsStore",
    "DuckDbMacroStore",
    "DuckDbProfileStore",
    "Filing",
    "FilingRow",
    "FilingType",
    "FilingsReader",
    "FilingsRepository",
    "FundamentalRecord",
    "InMemoryReferenceExporter",
    "InstrumentCoverage",
    "LakehouseCalendarReader",
    "LakehouseFilingsReader",
    "LakehouseMarketReader",
    "LakehouseProfileReader",
    "MacroObservation",
    "MacroReader",
    "MacroRow",
    "MacroSeriesRepository",
    "MarketReader",
    "ParquetCatalog",
    "ProfileReader",
    "ProfileRepository",
    "ProfileRow",
    "PythonMacroReader",
    "ReferenceExporter",
    "Rights",
    "ScreenCondition",
    "ScreenQuery",
    "ScreenResult",
    "ScreenValue",
    "ScreenerReader",
    "Split",
    "SymbolProfile",
    "VectorizedScreener",
    "VyapaarDataService",
    "__version__",
    "fetch_symbol_profiles",
    "from_record",
    "parse_bhavcopy",
    "parse_calendar",
    "parse_filings",
    "parse_macro",
    "read_bhavcopy",
    "read_calendar",
    "read_filings",
    "read_macro",
    "rows_to_bars",
    "rows_to_events",
    "rows_to_filings",
    "rows_to_observations",
    "rows_to_profiles",
    "stubbed_calendar_rows",
    "to_record",
    "yfinance_available",
]
