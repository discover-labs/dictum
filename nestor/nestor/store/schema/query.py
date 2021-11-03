from typing import List, Optional

from lark import Transformer
from pydantic import BaseModel, Field

from nestor.store.expr import parse_expr


class TransformExprTransformer(Transformer):
    def TRUE(self, _):
        return True

    def FALSE(self, _):
        return False

    def FLOAT(self, _):
        return float(_)

    def INTEGER(self, _):
        return int(_)

    def STRING(self, _):
        return str(_)

    def call(self, args: list):
        id, *args = args
        return QueryDimensionTransform(id=id.lower(), args=args)

    def __default__(self, _, data, *__):
        raise ValueError(
            f"Only constants are allowed inside filters and transforms, got {data}"
        )


transformer = TransformExprTransformer()


class QueryDimensionTransform(BaseModel):
    id: str
    args: List

    @classmethod
    def parse(self, call: Optional[str]) -> Optional["QueryDimensionTransform"]:
        if call is None:
            return None
        expr = parse_expr(call).children[0]
        if expr.data != "call":
            raise ValueError(
                f"Transforms and filters are defined as function calls, got {call}"
            )
        return transformer.transform(expr)


class QueryDimensionRequest(BaseModel):
    dimension: str
    transform: Optional[QueryDimensionTransform]


class QueryDimensionFilter(BaseModel):
    dimension: str
    filter: QueryDimensionTransform


class QueryMetricRequest(BaseModel):
    metric: str


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
