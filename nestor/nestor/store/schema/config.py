from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, Field, validator

from nestor.store.schema.types import CalculationType, Expression, Identifier


class Base(BaseModel):
    pass


class RelatedTable(Base):
    table: Identifier
    foreign_key: str
    alias: str = Field(alias="id")


class CalculationFormat(Base):
    spec: str
    currency_prefix: str = ""
    currency_suffix: str = ""


class Displayed(Base):
    id: str
    name: str
    description: Optional[str]
    format: Optional[CalculationFormat]

    @validator("format", pre=True)
    def validate_format(cls, value):
        if isinstance(value, str):
            return {"spec": value}
        return value


class Calculation(Displayed):
    expr: Expression


class Measure(Calculation):
    metric: bool = True


class Metric(Measure):
    pass


class Dimension(Calculation):
    type: CalculationType
    union: Optional[Identifier]


def _set_ids(data: Dict):
    for k, v in data.items():
        v["id"] = k
    return data


class Table(Base):
    id: str
    description: Optional[str]
    source: str
    primary_key: Optional[Identifier]
    related: Dict[str, RelatedTable] = {}
    measures: Dict[Identifier, Measure] = {}
    dimensions: Dict[Identifier, Dimension] = {}

    set_related_ids = validator("related", allow_reuse=True, pre=True)(_set_ids)
    set_measures_ids = validator("measures", allow_reuse=True, pre=True)(_set_ids)
    set_dimensions_ids = validator("dimensions", allow_reuse=True, pre=True)(_set_ids)


class DimensionsUnion(Displayed):
    type: CalculationType


class Config(Base):
    name: str
    description: Optional[str]
    metrics: Dict[Identifier, Metric] = {}
    tables: Dict[Identifier, Table] = {}
    unions: Dict[Identifier, DimensionsUnion] = {}

    @classmethod
    def from_yaml(cls, path: str):
        data = yaml.load(Path(path).read_text(), Loader=yaml.SafeLoader)
        return cls.parse_obj(data)

    set_metrics_ids = validator("metrics", allow_reuse=True, pre=True)(_set_ids)
    set_tables_ids = validator("tables", allow_reuse=True, pre=True)(_set_ids)
    set_unions_ids = validator("unions", allow_reuse=True, pre=True)(_set_ids)
