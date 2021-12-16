from typing import List, Optional

from pydantic import BaseModel, validator


class QueryDimensionTransform(BaseModel):
    id: str
    args: List = []

    @property
    def suffix(self):
        args = "_".join(str(a) for a in self.args)
        if len(args) > 0:
            args = f"_{args}"
        return f"{self.id}{args}"


class DimensionTopK(BaseModel):
    k: int
    on: str
    top: bool = True


class QueryDimensionRequest(BaseModel):
    dimension: str
    transforms: List[QueryDimensionTransform] = []
    alias: Optional[str]

    @property
    def name(self):
        if self.alias is not None:
            return self.alias
        suffixes = []
        for transform in self.transforms:
            suffixes.append(transform.suffix)
        if len(suffixes) > 0:
            _suff = "_".join(suffixes)
            return f"{self.dimension}__{_suff}"
        return self.dimension


class QueryDimensionFilter(BaseModel):
    dimension: str
    transforms: List[QueryDimensionTransform] = []


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

    metrics: List[QueryMetricRequest] = []
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
