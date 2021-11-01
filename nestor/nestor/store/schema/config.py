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


class DimensionQueryDefaults(Base):
    filter: Optional[str] = None
    transform: Optional[str] = None


class Dimension(Calculation):
    type: CalculationType
    union: Optional[Identifier]
    query_defaults: DimensionQueryDefaults = DimensionQueryDefaults()


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


class Transform(Base):
    id: str
    name: str
    description: Optional[str]
    args: list
    expr: str


class Config(Base):
    name: str
    description: Optional[str]
    metrics: Dict[Identifier, Metric] = {}
    tables: Dict[Identifier, Table] = {}
    unions: Dict[Identifier, DimensionsUnion] = {}
    filters: Dict[Identifier, Transform] = {}  # undocumented
    transforms: Dict[Identifier, Transform] = {}  # undocumented

    @classmethod
    def from_yaml(cls, path: str):
        config = yaml.load(Path(path).read_text(), Loader=yaml.SafeLoader)

        # inject built-in transforms and filters
        builtins = yaml.load(
            (Path(__file__).parent / "builtins.yml").read_text(), Loader=yaml.SafeLoader
        )
        config_filters = config.get("filters", {})
        config_transforms = config.get("transforms", {})
        collision = set(builtins["filters"]) & set(config_filters)
        if collision:
            raise ValueError(
                f"Can't give a filter the same name as a built-in: {collision}"
            )
        collision = set(builtins["transforms"]) & set(config_transforms)
        if collision:
            raise ValueError(
                f"Can't give a transform the same name as a built-in: {collision}"
            )
        builtins["filters"].update(config_filters)
        builtins["transforms"].update(config_transforms)
        config["filters"] = builtins["filters"]
        config["transforms"] = builtins["transforms"]

        # inject file-based tables
        tables_dir = config.pop("tables_dir", "tables")
        tables_dir = path.parent / tables_dir
        if tables_dir.is_dir():
            extensions = ("yml", "yaml")
            paths = [p for ext in extensions for p in tables_dir.glob(f"**/*.{ext}")]
            if "tables" not in config:
                config["tables"] = {}
            for path in paths:
                if path.stem in config["tables"]:
                    raise KeyError(f"Duplicate table: {path.stem}")
                config["tables"][path.stem] = yaml.load(
                    path.read_text(), Loader=yaml.SafeLoader
                )

        return cls.parse_obj(config)

    set_metrics_ids = validator("metrics", allow_reuse=True, pre=True)(_set_ids)
    set_tables_ids = validator("tables", allow_reuse=True, pre=True)(_set_ids)
    set_unions_ids = validator("unions", allow_reuse=True, pre=True)(_set_ids)
    set_filters_ids = validator("filters", allow_reuse=True, pre=True)(_set_ids)
    set_transforms_ids = validator("transforms", allow_reuse=True, pre=True)(_set_ids)
