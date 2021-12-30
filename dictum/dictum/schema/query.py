from typing import List, Optional

from pydantic import BaseModel, root_validator

from dictum.utils import repr_expr_constant


class QueryTransform(BaseModel):
    id: str
    args: List = []

    @property
    def suffix(self):
        args = "_".join(str(a) for a in self.args)
        if len(args) > 0:
            args = f"_{args}"
        return f"{self.id}{args}"

    def render(self) -> str:
        args = ", ".join(repr_expr_constant(a) for a in self.args)
        return f"{self.id}({args})"


class QueryScalarTransform(QueryTransform):
    pass


class QueryTableTransform(QueryTransform):
    of: List["QueryDimension"] = []
    within: List["QueryDimension"] = []

    @property
    def suffix(self) -> str:
        suffix = super().suffix
        for dim in self.of:
            suffix += f"_of_{dim.name}"
        for dim in self.within:
            suffix += f"_within_{dim.name}"
        return suffix

    def render(self) -> str:
        result = super().render()
        if self.of:
            requests = ", ".join(r.render() for r in self.of)
            result += f" of ({requests})"
        if self.within:
            requests = ", ".join(r.render() for r in self.within)
            result += f" within ({requests})"
        return result


class QueryCalculation(BaseModel):
    id: str
    transforms: List[QueryTransform] = []

    @property
    def name(self):
        suffixes = []
        for transform in self.transforms:
            suffixes.append(transform.suffix)
        if len(suffixes) > 0:
            _suff = "_".join(suffixes)
            return f"{self.id}__{_suff}"
        return self.id

    def render(self) -> str:
        result = self.id
        if self.transforms:
            for transform in self.transforms:
                result += f".{transform.render()}"
        return result


class QueryCalculationRequest(BaseModel):
    alias: Optional[str]

    @property
    def name(self) -> str:
        if self.alias is not None:
            return self.alias
        return self.calculation.name

    @property
    def calculation(self) -> QueryCalculation:
        raise NotImplementedError

    def render(self) -> str:
        result = self.calculation.render()
        if self.alias:
            result += f' as "{self.alias}"'
        return result


class QueryDimension(QueryCalculation):
    transforms: List[QueryScalarTransform] = []


class QueryDimensionRequest(QueryCalculationRequest):
    dimension: QueryDimension

    @property
    def calculation(self) -> QueryDimension:
        return self.dimension


ops = {
    "eq": "=",
    "ne": "!=",
    "lt": "<",
    "le": "<=",
    "gt": ">",
    "ge": "<",
    "isnull": "is null",
    "isnotnotnull": "is not null",
}


class QueryMetric(QueryCalculation):
    transforms: List[QueryTableTransform] = []

    def render(self):
        """A special case, because no more than 2 are allowed."""
        if len(self.transforms) < 2:
            return super().render()
        table, scalar = self.transforms
        result = f"{self.id}.{table.render()}"
        op = ops[scalar.id]
        val = repr_expr_constant(scalar.args[0]) if scalar.args else ""
        result += f" {op} {val}"
        return result


class QueryMetricRequest(QueryCalculationRequest):
    metric: QueryMetric
    alias: Optional[str]

    @property
    def calculation(self) -> QueryMetric:
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
    filters: List[QueryDimension] = []
    limit: List[QueryMetric] = []

    @root_validator(skip_on_failure=True)
    def validate_names(cls, values: dict):
        names = set()
        for item in values.get("metrics", []):
            request = QueryMetricRequest.parse_obj(item)
            if request.name in names:
                raise ValueError(f"Duplicate column name in query: {request.name}")
            names.add(request.name)
        for item in values.get("dimensions", []):
            request = QueryDimensionRequest.parse_obj(item)
            if request.name in names:
                raise ValueError(f"Duplicate column name in query: {request.name}")
            names.add(request.name)
        return values


QueryTableTransform.update_forward_refs()
