from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

from dictum import schema


@dataclass
class ExecutedQuery:
    query: str
    time: float


AltairTimeUnit = Literal[
    "year",
    "yearquarter",
    "yearmonth",
    "yearmonthdate",
    "yearmonthdatehours",
    "yearmonthdatehoursminutes",
    "yearmonthdatehoursminutesseconds",
]

DisplayColumnKind = Literal["metric", "dimension"]


@dataclass
class DisplayInfo:
    """Information for the displaying code:
    either data formatter or Altair
    """

    display_name: str
    column_name: str
    format: schema.FormatConfig
    kind: DisplayColumnKind
    type: Optional[schema.Type] = None
    keep_display_name: bool = False
    altair_time_unit: Optional[str] = None


@dataclass
class Result:
    data: List[dict]
    display_info: Dict[str, DisplayInfo]
    executed_queries: List[ExecutedQuery]
