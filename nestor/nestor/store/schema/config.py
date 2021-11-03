from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from babel.numbers import list_currencies
from pydantic import BaseModel, Field, root_validator, validator

from nestor.store.schema.types import CalculationType, Expression, Identifier


class Base(BaseModel):
    pass


class RelatedTable(Base):
    table: Identifier
    foreign_key: str
    alias: str = Field(alias="id")


class Displayed(Base):
    id: str
    name: str
    description: Optional[str]
    format: Optional[str]
    type: CalculationType
    currency: Optional[str]

    @validator("format", pre=True)
    def validate_format(cls, value):
        if isinstance(value, str):
            return {"spec": value}
        return value

    @validator("type")
    def validate_type(cls, value):
        values = {"number", "percent", "date", "datetime", "string", "currency"}
        if value not in values:
            raise ValueError(f"Calculation type must be one of {values}")
        return value

    @root_validator(skip_on_failure=True)
    def validate_currency(cls, values):
        if values["type"] != "currency":
            return values
        if values["currency"] is None:
            raise ValueError(
                "currency field is required for calculations of currency type"
            )
        if values["currency"] not in list_currencies():
            raise ValueError(f"{values['currency']} is not a supported currency")
        return values


class Calculation(Displayed):
    expr: Expression
    missing: Any

    @root_validator
    def set_default_missing(cls, values):
        missing = values.get("missing")
        if values["type"] in {"date", "datetime"} and missing is not None:
            raise ValueError(
                "Missing values for types date, datetime are not supported"
            )
        _type = values.get("type")
        if missing is None:
            if _type in {"number", "decimal", "percent", "currency"}:
                missing = 0
            elif _type == "string":
                missing = "N/A"
        values["missing"] = missing
        return values


class Measure(Calculation):
    type: CalculationType = "number"
    metric: bool = True


class Metric(Measure):
    pass


class DimensionQueryDefaults(Base):
    filter: Optional[str] = None
    transform: Optional[str] = None


class Dimension(Calculation):
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
    args: list = []
    expr: str
    return_type: Optional[str]
    format: Optional[str]


class Config(Base):
    name: str
    description: Optional[str]
    locale: str = "en_US"
    metrics: Dict[Identifier, Metric] = {}
    unions: Dict[Identifier, DimensionsUnion] = {}
    tables: Dict[Identifier, Table] = {}
    filters: Dict[Identifier, Transform] = {}
    transforms: Dict[Identifier, Transform] = {}

    @classmethod
    def from_yaml(cls, path: str):
        path = Path(path)
        config = yaml.load(path.read_text(), Loader=yaml.SafeLoader)

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
