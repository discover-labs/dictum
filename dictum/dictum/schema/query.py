from typing import List, Optional

from pydantic import BaseModel, Field, validator


class QueryDimensionTransform(BaseModel):
    id: str
    args: List = []


class DimensionTopK(BaseModel):
    k: int
    on: str
    top: bool = True


class QueryDimensionRequest(BaseModel):
    dimension: str
    transform: Optional[QueryDimensionTransform]
    alias: Optional[str]

    @property
    def name(self):
        if self.alias is not None:
            return self.alias
        if self.transform is not None:
            suffix = "_".join(
                [self.transform.id, *(str(a) for a in self.transform.args)]
            )
            return f"{self.dimension}__{suffix}"
        return self.dimension


class QueryDimensionFilter(BaseModel):
    dimension: str
    filter: QueryDimensionTransform


class QueryMetricRequest(BaseModel):
    metric: str

    @property
    def name(self):
        return self.metric


class Query(BaseModel):
    """A query object that a store understands. Represents a request for metrics
    from a user.
    measures: list of measure identifiers
    dimensions: list of dimension identifiers
    filters: list of boolean expressions. will be concatenated with AND
    """

    metrics: List[QueryMetricRequest] = Field(..., min_items=1)
    dimensions: List[QueryDimensionRequest] = []
    filters: List[QueryDimensionFilter] = []
    formatting: bool = False

    @validator("dimensions", always=True)
    def validate_dimensions(cls, value: dict):
        """Assert that the requested dimensions do not have duplicate names."""
        names = set()
        for v in value:
            request = QueryDimensionRequest.parse_obj(v)
            if request.name in names:
                raise ValueError(f"Duplicate dimension names in query: {request.name}")
            names.add(request.name)
        return value
