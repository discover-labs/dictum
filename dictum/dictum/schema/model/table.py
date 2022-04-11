from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from dictum.schema import utils
from dictum.schema.id import ID
from dictum.schema.model.calculations import Dimension, Measure


class RelatedTable(BaseModel):
    str_table: str = Field(alias="table")
    foreign_key: str
    alias: ID = Field(alias="id")
    str_related_key: Optional[str] = Field(alias="related_key")


class Table(BaseModel):
    id: ID
    description: Optional[str]
    source: Union[str, Dict]
    primary_key: Optional[str]
    related: Dict[ID, RelatedTable] = {}
    measures: Dict[ID, Measure] = {}
    dimensions: Dict[ID, Dimension] = {}
    filters: List[str] = []

    set_related_ids = validator("related", allow_reuse=True, pre=True)(utils.set_ids)
    set_measures_ids = validator("measures", allow_reuse=True, pre=True)(utils.set_ids)
    set_dimensions_ids = validator("dimensions", allow_reuse=True, pre=True)(
        utils.set_ids
    )
