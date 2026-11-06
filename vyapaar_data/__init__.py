"""vyapaar-data — Point-in-Time Financial Lakehouse & Corporate Actions.

Tier 6A bounded context. Domain value objects are pure and self-validating;
ports are protocols; adapters implement DuckDB/Parquet storage; providers ingest
official NSE files; the service facade composes everything into a
look-ahead-bias-free data service.
"""

from __future__ import annotations

from vyapaar_data._compat import VYAAPAAR_AVAILABLE
from vyapaar_data.adapters import (
    DuckDbCorporateActionsStore,
    DuckDbFundamentalsStore,
    ParquetCatalog,
)
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
from vyapaar_data.domain.fundamentals import FundamentalRecord
from vyapaar_data.providers.bhavcopy import (
    BhavcopyRow,
    parse_bhavcopy,
    read_bhavcopy,
    rows_to_bars,
)
from vyapaar_data.service.data_service import VyapaarDataService

__version__ = "0.1.0"

__all__ = [
    "VYAAPAAR_AVAILABLE",
    "BhavcopyRow",
    "Bonus",
    "CorporateAction",
    "CorporateActionRecord",
    "CorporateActionType",
    "CoverageEntry",
    "CoverageLedger",
    "CoverageReport",
    "Dividend",
    "DuckDbCorporateActionsStore",
    "DuckDbFundamentalsStore",
    "FundamentalRecord",
    "InstrumentCoverage",
    "ParquetCatalog",
    "Rights",
    "Split",
    "VyapaarDataService",
    "__version__",
    "from_record",
    "parse_bhavcopy",
    "read_bhavcopy",
    "rows_to_bars",
    "to_record",
]
