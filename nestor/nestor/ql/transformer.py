from lark import Transformer

from nestor.ql.parser import parse_ql
from nestor.store.schema import Query, QueryTranformRequest


class QlTransformer(Transformer):
    """Compiles a QL query AST into a Query object."""

    def metric(self, children: list):
        """Return metric name as a string"""
        return children[0]

    def select(self, children: list):
        """Just return a list of metric names"""
        return children

    def dimension(self, children: list):
        return children[0]

    def call(self, children: list):
        id, *args = children
        return QueryTranformRequest(id=id, args=args)

    def condition(self, children: list):
        return children

    def where(self, conditions: list):
        result = {}
        for dimension, request in conditions:
            if dimension in result:
                raise KeyError(f"Duplicate dimension in condition: {dimension}")
            result[dimension] = request
        return result

    def grouping(self, children: list):
        return children

    def groupby(self, children: list):
        dimensions = []
        transforms = {}
        for grouping in children:
            dimension = grouping[0]
            if dimension in dimensions:
                raise KeyError(f"Duplicate dimension in GROUP BY: {dimension}")
            if len(grouping) == 2:
                transforms[dimension] = grouping[1]
            dimensions.append(dimension)
        return dimensions, transforms

    def query(self, children: list):
        metrics, *rest = children
        filters, dimensions, transforms = {}, [], {}
        if len(rest) > 0:
            if len(rest) == 2:
                filters, (dimensions, transforms) = rest
            elif isinstance(rest[0], dict):
                filters = rest[0]
            else:
                dimensions, transforms = rest[0]
        return Query(
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            transforms=transforms,
        )


transformer = QlTransformer()


def parse_query(query: str) -> Query:
    expr = parse_ql(query)
    return transformer.transform(expr)
