from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, root_validator

from nestor.store.schema.types import DimensionType, Expression, Identifier


class Base(BaseModel):
    pass


class ForeignKey(Base):
    column: Identifier
    to: Expression


class Measure(Base):
    name: str
    description: Optional[str]
    shorthand: Optional[Identifier]
    expr: Expression


class Dimension(Base):
    expr: str
    name: str
    description: Optional[str]
    type: DimensionType


class Table(Base):
    source: str
    description: Optional[str]
    primary_key: Optional[Identifier] = Field(
        ..., description="If not set, this table can't be a target of a foreign key."
    )
    foreign_keys: List[ForeignKey] = []
    measures: Dict[Identifier, Measure] = {}
    dimensions: Dict[Identifier, Dimension] = {}


class Config(Base):
    tables: Dict[Identifier, Table]

    @classmethod
    def from_yaml(cls, path: str):
        data = yaml.load(Path(path).read_text(), Loader=yaml.SafeLoader)
        return cls.parse_obj(data)

    @root_validator
    def validate_unique_ids(cls, values: dict):
        """Check that measure and dimension IDs are unique across all tables."""
        ids = set()
        for table_id, table in values["tables"].items():
            for id in table.measures:
                if id in ids:
                    raise ValueError(f"Duplicate measure: {id} in table {table_id}")
                ids.add(id)
            for id in table.dimensions:
                if id in ids:
                    raise ValueError(f"Duplicate dimension: {id} in table {table_id}")
                ids.add(id)
        return values
