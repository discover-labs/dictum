from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, validator

from dictum.schema import utils
from dictum.schema.data_model.calculations import DimensionsUnion, Metric
from dictum.schema.data_model.table import Table
from dictum.schema.data_model.transform import Transform


class DataModel(BaseModel):
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

    set_metrics_ids = validator("metrics", allow_reuse=True, pre=True)(utils.set_ids)
    set_tables_ids = validator("tables", allow_reuse=True, pre=True)(utils.set_ids)
    set_unions_ids = validator("unions", allow_reuse=True, pre=True)(utils.set_ids)
    set_filters_ids = validator("filters", allow_reuse=True, pre=True)(utils.set_ids)
    set_transforms_ids = validator("transforms", allow_reuse=True, pre=True)(
        utils.set_ids
    )
