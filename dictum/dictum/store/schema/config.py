from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import yaml
from babel.numbers import list_currencies
from pydantic import BaseModel, Field, root_validator, validator

currencies = set(list_currencies())


class Base(BaseModel):
    pass


class RelatedTable(Base):
    table: str
    foreign_key: str
    alias: str = Field(alias="id")


FormatKind = Literal["number", "decimal", "percent", "currency", "date", "datetime"]


class FormatConfig(Base):
    kind: FormatKind
    pattern: Optional[str]
    currency: Optional[str]

    @root_validator(skip_on_failure=True)
    def validate_currency(cls, values):
        if values["kind"] != "currency":
            if values.get("currency") is not None:
                raise ValueError(
                    "'currency' format option is only valid with 'currency' format kind"
                )
            return values
        if values.get("currency") is None:
            raise ValueError(
                "'currency' formatting option is required if format kind is 'currency'"
            )
        if values["currency"] not in currencies:
            raise ValueError(f"{values['currency']} is not a supported currency")
        return values


Format = Union[FormatKind, FormatConfig]
Type = Literal["int", "float", "date", "datetime", "str"]


class Displayed(Base):
    id: str
    name: str
    description: Optional[str]
    type: Type
    format: Optional[Format]
    missing: Optional[Any]

    @staticmethod
    def get_default_format(type: Type) -> Optional[FormatConfig]:
        if type in {"int", "float"}:
            return FormatConfig(kind="number")
        if type in {"date", "datetime"}:
            return FormatConfig(kind=type)

    @root_validator
    def set_default_format(cls, values):
        fmt = values.get("format")
        if fmt is None:
            values["format"] = cls.get_default_format(values.get("type", "float"))
        if isinstance(fmt, str):
            values["format"] = FormatConfig(kind=fmt)
        return values

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
    str_expr: str = Field(..., alias="expr")


class Measure(Calculation):
    type: Type = "float"
    metric: bool = True


class Metric(Calculation):
    type: Type = "float"


class Dimension(Calculation):
    union: Optional[str]


def _set_ids(data: Dict):
    for k, v in data.items():
        v["id"] = k
    return data


class Table(Base):
    id: str
    description: Optional[str]
    source: Union[str, Dict]
    primary_key: Optional[str]
    related: Dict[str, RelatedTable] = {}
    measures: Dict[str, Measure] = {}
    dimensions: Dict[str, Dimension] = {}
    filters: List[str] = []

    set_related_ids = validator("related", allow_reuse=True, pre=True)(_set_ids)
    set_measures_ids = validator("measures", allow_reuse=True, pre=True)(_set_ids)
    set_dimensions_ids = validator("dimensions", allow_reuse=True, pre=True)(_set_ids)


class DimensionsUnion(Displayed):
    pass


class Transform(Base):
    id: str
    name: str
    description: Optional[str]
    args: list = []
    str_expr: str = Field(..., alias="expr")
    format: Optional[Format]
    return_type: Optional[Type]


class Config(Base):
    name: str
    description: Optional[str]
    locale: str = "en_US"
    metrics: Dict[str, Metric] = {}
    unions: Dict[str, DimensionsUnion] = {}
    tables: Dict[str, Table] = {}
    filters: Dict[str, Transform] = {}
    transforms: Dict[str, Transform] = {}

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
