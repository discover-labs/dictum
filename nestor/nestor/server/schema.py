import json
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypeVar

from pydantic import BaseModel, Field

from nestor.server import static
from nestor.store.schema import CalculationMetadata, Query
from nestor.store.schema.types import DimensionType, Identifier

static = Path(static.__file__).parent


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


class LocaleDefinition(BaseModel):
    number: Dict[str, Any]
    time: Dict[str, Any]

    @classmethod
    @cache
    def from_locale_name(cls, locale_name: str):
        base = static / "locale"
        file = f"{locale_name}.json"
        number = base / "number" / file
        time = base / "time" / file
        assert base in number.parents
        assert base in time.parents
        if not (number.is_file() and time.is_file()):
            return cls.default()
        number = json.loads(number.read_text())
        time = json.loads(time.read_text())
        return cls(number=number, time=time)

    @classmethod
    def default(cls):
        return cls.from_locale_name("en-US")


class QueryResultMetadata(BaseModel):
    locale: LocaleDefinition
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
