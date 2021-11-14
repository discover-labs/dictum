from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeVar

from pydantic import BaseModel, Field

from dictum.server import static
from dictum.store.schema import CalculationMetadata, Query
from dictum.store.schema.types import CalculationType, Identifier

static = Path(static.__file__).parent


class Base(BaseModel):
    pass


class Calculation(BaseModel):
    id: Identifier
    name: str
    description: Optional[str]
    expr: str = Field(..., alias="str_expr")
    type: CalculationType

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class Measure(Calculation):
    type: CalculationType = CalculationType.continuous


class Dimension(Calculation):
    pass


class Table(BaseModel):
    id: str
    source: str
    measures: List[Measure]
    dimensions: List[Dimension]


class QueryResultMetadata(BaseModel):
    columns: Dict[str, CalculationMetadata]
    store: "Store"


class QueryResult(BaseModel):
    query: Query
    metadata: QueryResultMetadata
    data: List[Dict]


class Store(BaseModel):
    measures: List[Measure]
    dimensions: List[Dimension]


T = TypeVar("T")


class FilterInfo(Base):
    range: Optional[Tuple[T, T]]
    values: Optional[List[T]]


class Filter(Base):
    dimension: Dimension
    info: FilterInfo


QueryResultMetadata.update_forward_refs()
