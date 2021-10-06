from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from nestor.store.schema import Query
from nestor.store.schema.types import DimensionType, Identifier


class Base(BaseModel):
    pass


class Calculation(BaseModel):
    id: Identifier
    name: str
    description: Optional[str]
    expr: str = Field(..., alias="str_expr")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class Measure(Calculation):
    pass


class Dimension(Calculation):
    type: DimensionType


class Table(BaseModel):
    id: str
    source: str
    measures: List[Measure]
    dimensions: List[Dimension]


class QueryResultMetadata(BaseModel):
    columns: Dict[str, str]
    store: "Store"


class QueryResult(BaseModel):
    query: Query
    metadata: QueryResultMetadata
    data: List[Dict]


class Store(BaseModel):
    measures: List[Measure]
    dimensions: List[Dimension]


QueryResultMetadata.update_forward_refs()
