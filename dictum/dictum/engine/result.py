from dataclasses import dataclass
from typing import Dict, List

from dictum import schema


@dataclass
class ExecutedQuery:
    query: str
    time: float


@dataclass
class DisplayInfo:
    name: str
    format: schema.FormatConfig
    keep_name: bool = False


@dataclass
class Result:
    data: List[dict]
    display_info: Dict[str, DisplayInfo]
    executed_queries: List[ExecutedQuery]
