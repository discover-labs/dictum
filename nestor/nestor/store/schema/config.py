from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, root_validator, validator

from nestor.store.schema.types import DimensionType, Expression, Identifier


class Base(BaseModel):
    pass


class RelatedTable(Base):
    table: Identifier
    alias: Optional[Identifier]
    foreign_key: str

    @property
    def ref(self):
        return self.alias if self.alias is not None else self.table


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
    description: Optional[str]
    source: str
    primary_key: Optional[Identifier] = Field(
        ..., description="If not set, this table can't be a target of a foreign key."
    )
    related: List[RelatedTable] = []
    measures: Dict[Identifier, Measure] = {}
    dimensions: Dict[Identifier, Dimension] = {}

    @validator("related")
    def check_related_refs_unique(cls, related: List[RelatedTable], values):
        refs = set()
        for rel in related:
            if rel.ref in refs:
                table = values.get("source")
                raise ValueError(
                    f"Duplicate related table refs for table {table}: {rel.ref}"
                )
            refs.add(rel.ref)
        return related


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
        breakpoint()
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
