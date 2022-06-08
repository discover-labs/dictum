from dataclasses import dataclass
from typing import Dict, List, Optional

from dictum import schema


@dataclass
class ExecutedQuery:
    query: str
    time: float


@dataclass
class DisplayInfo:
    """Information for the displaying code:
    either data formatter or Altair
    """

    name: str
    format: schema.FormatConfig
    type: Optional[schema.Type] = None
    keep_name: bool = False


@dataclass
class Result:
    data: List[dict]
    display_info: Dict[str, DisplayInfo]
    executed_queries: List[ExecutedQuery]
