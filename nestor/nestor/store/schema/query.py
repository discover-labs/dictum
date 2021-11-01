from typing import Dict, List, Optional

from lark import Transformer
from pydantic import BaseModel, Field

from nestor.store.expr import parse_expr
from nestor.store.schema.types import Identifier


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
        return QueryTranformRequest(id=id.lower(), args=args)

    def __default__(self, _, data, *__):
        raise ValueError(
            f"Only constants are allowed inside filters and transforms, got {data}"
        )


transformer = TransformExprTransformer()


class QueryTranformRequest(BaseModel):
    id: str
    args: List

    @classmethod
    def parse(self, call: Optional[str]) -> Optional["QueryTranformRequest"]:
        if call is None:
            return None
        expr = parse_expr(call).children[0]
        if expr.data != "call":
            raise ValueError(
                f"Transforms and filters are defined as function calls, got {call}"
            )
        return transformer.transform(expr)


class Query(BaseModel):
    """A query object that a store understands. Represents a request for metrics
    from a user.
    measures: list of measure identifiers
    dimensions: list of dimension identifiers
    filters: list of boolean expressions. will be concatenated with AND
    """

    metrics: List[Identifier] = Field(..., min_items=1)
    dimensions: List[Identifier] = []
    transforms: Dict[str, QueryTranformRequest] = {}
    filters: Dict[str, QueryTranformRequest] = {}
