from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, validator

from nestor.store.schema.types import CalculationType, Expression, Identifier


class Base(BaseModel):
    pass


class RelatedTable(Base):
    table: Identifier
    foreign_key: str


class CalculationFormat(Base):
    spec: str
    currency_prefix: str = ""
    currency_suffix: str = ""


class Calculation(Base):
    name: str
    expr: Expression
    description: Optional[str]
    format: Optional[CalculationFormat]

    @validator("format", pre=True)
    def validate_format(cls, value):
        if isinstance(value, str):
            return {"spec": value}
        return value


class Measure(Calculation):
    key: bool = False
    metric: bool = True


class Metric(Measure):
    pass


class Dimension(Calculation):
    type: CalculationType


class Table(Base):
    description: Optional[str]
    source: str
    primary_key: Optional[Identifier]
    related: Dict[str, RelatedTable] = {}
    measures: Dict[Identifier, Measure] = {}
    dimensions: Dict[Identifier, Dimension] = {}


class Config(Base):
    name: str
    description: Optional[str]
    metrics: Dict[Identifier, Metric] = {}
    tables: Dict[Identifier, Table] = {}

    @classmethod
    def from_yaml(cls, path: str):
        data = yaml.load(Path(path).read_text(), Loader=yaml.SafeLoader)
        return cls.parse_obj(data)
