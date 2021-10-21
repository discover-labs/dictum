from typing import List

from pydantic import BaseModel, Field

from nestor.store.schema.types import Identifier


class Query(BaseModel):
    """A query object that a store understands. Represents a request for metrics
    from a user.
    measures: list of measure identifiers
    dimensions: list of dimension identifiers
    filters: list of boolean expressions. will be concatenated with AND
    """

    metrics: List[Identifier] = Field(..., min_items=1)
    dimensions: List[Identifier] = []
    filters: List[str] = []
