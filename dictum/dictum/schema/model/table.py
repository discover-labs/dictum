from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from dictum.schema import utils
from dictum.schema.model.calculations import Dimension, Measure


class RelatedTable(BaseModel):
    table: str
    foreign_key: str
    alias: str = Field(alias="id")
    related_key: Optional[str]


class Table(BaseModel):
    id: str
    description: Optional[str]
    source: Union[str, Dict]
    primary_key: Optional[str]
    related: Dict[str, RelatedTable] = {}
    measures: Dict[str, Measure] = {}
    dimensions: Dict[str, Dimension] = {}
    filters: List[str] = []

    set_related_ids = validator("related", allow_reuse=True, pre=True)(utils.set_ids)
    set_measures_ids = validator("measures", allow_reuse=True, pre=True)(utils.set_ids)
    set_dimensions_ids = validator("dimensions", allow_reuse=True, pre=True)(
        utils.set_ids
    )
