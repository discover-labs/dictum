from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, validator

from dictum.schema import utils
from dictum.schema.model.calculations import DimensionsUnion, Metric
from dictum.schema.model.table import Table
from dictum.schema.model.transform import Transform

root_keys = {"tables", "metrics", "unions"}


class Model(BaseModel):
    name: str
    description: Optional[str]
    locale: str = "en_US"

    metrics: Dict[str, Metric] = {}
    unions: Dict[str, DimensionsUnion] = {}

    tables: Dict[str, Table] = {}
    transforms: Dict[
        str, Transform
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
    set_tables_ids = validator("tables", allow_reuse=True, pre=True)(utils.set_ids)
    set_unions_ids = validator("unions", allow_reuse=True, pre=True)(utils.set_ids)
    set_transforms_ids = validator("transforms", allow_reuse=True, pre=True)(
        utils.set_ids
    )
