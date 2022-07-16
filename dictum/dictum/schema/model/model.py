from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, root_validator, validator

from dictum.schema import utils
from dictum.schema.id import ID
from dictum.schema.model.calculations import DetachedDimension, DimensionsUnion, Metric
from dictum.schema.model.table import Table
from dictum.schema.model.transform import Transform

root_keys = {"tables", "metrics", "unions"}


class Model(BaseModel):
    name: str
    description: Optional[str]
    locale: str = "en_US"
    currency: str = "USD"

    dimensions: Dict[ID, DetachedDimension] = {}
    metrics: Dict[ID, Metric] = {}
    unions: Dict[ID, DimensionsUnion] = {}

    tables: Dict[ID, Table] = {}
    transforms: Dict[
        ID, Transform
    ] = {}  # ignored for now, TODO: load as LiteralTransform

    theme: Optional[dict]

    @classmethod
    def from_yaml(cls, path: str):
        path = Path(path)
        config = yaml.load(path.read_text(), Loader=yaml.SafeLoader)

        # inject file-based tables
        tables_dir = config.pop("tables_dir", "tables")
        tables_dir = path.parent / tables_dir
        if tables_dir.is_dir():
            extensions = ("yml", "yaml")
            paths = [p for ext in extensions for p in tables_dir.glob(f"**/*.{ext}")]
            if "tables" not in config:
                config["tables"] = {}
            for table_path in paths:
                if table_path.stem in config["tables"]:
                    raise KeyError(f"Duplicate table: {table_path.stem}")
                config["tables"][table_path.stem] = yaml.load(
                    table_path.read_text(), Loader=yaml.SafeLoader
                )

        theme_path = path.parent / config.get("altair_theme", "altair_theme.yml")
        if theme_path.is_file():
            config["theme"] = yaml.load(theme_path.read_text(), Loader=yaml.SafeLoader)

        return cls.parse_obj(config)

    set_metrics_ids = validator("metrics", allow_reuse=True, pre=True)(utils.set_ids)
    set_dimensions_ids = validator("dimensions", allow_reuse=True, pre=True)(
        utils.set_ids
    )
    set_tables_ids = validator("tables", allow_reuse=True, pre=True)(utils.set_ids)
    set_unions_ids = validator("unions", allow_reuse=True, pre=True)(utils.set_ids)
    set_transforms_ids = validator("transforms", allow_reuse=True, pre=True)(
        utils.set_ids
    )

    @root_validator(pre=True)
    def set_default_currency(cls, value: dict):
        currency = value.get("currency", "USD")

        def _set(calculation: dict):
            if calculation.get("format") == "currency":
                calculation["format"] = dict(kind="currency", currency=currency)
            if calculation.get("format", {}).get("kind") == "currency":
                calculation["format"].setdefault("currency", currency)

        for table in value.get("tables", {}).values():
            for key in ["measures", "dimensions"]:
                for calculation in table.get(key, {}).values():
                    _set(calculation)
        for key in ["metrics", "dimensions", "unions"]:
            for calculation in value.get(key, {}).values():
                _set(calculation)
        return value
