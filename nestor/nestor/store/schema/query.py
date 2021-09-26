from typing import List

from pydantic import BaseModel, Field

from nestor.store.schema.types import Identifier


class Query(BaseModel):
    measures: List[Identifier] = Field(..., min_items=1)
    dimensions: List[Identifier] = []
