from lark import Transformer

from dictum.ql.parser import parse_ql
from dictum.store.schema.query import (
    Query,
    QueryDimensionFilter,
    QueryDimensionRequest,
    QueryDimensionTransform,
    QueryMetricRequest,
)


class QlTransformer(Transformer):
    """Compiles a QL query AST into a Query object."""

    def metric(self, children: list):
        """Return metric name as a string"""
        return QueryMetricRequest(metric=children[0])

    def select(self, children: list):
        """Just return a list of metric names"""
        return children

    def dimension(self, children: list):
        return children[0]

    def call(self, children: list):
        id, *args = children
        return QueryDimensionTransform(id=id, args=args)

    def condition(self, children: list):
        dimension, filter = children
        return QueryDimensionFilter(dimension=dimension, filter=filter)

    def where(self, conditions: list):
        return conditions

    def grouping(self, children: list):
        return children

    def groupby(self, children: list):
        dimensions = []
        for grouping in children:
            transform = None if len(grouping) == 1 else grouping[1]
            dimensions.append(
                QueryDimensionRequest(dimension=grouping[0], transform=transform)
            )
        return dimensions

    def query(self, children: list):
        metrics, *rest = children
        filters, dimensions = [], []
        if len(rest) > 0:
            if len(rest) == 2:
                filters, dimensions = rest
            elif isinstance(rest[0][0], QueryDimensionFilter):
                filters = rest[0]
            else:
                dimensions = rest[0]
        return Query(
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
        )


transformer = QlTransformer()


def parse_query(query: str) -> Query:
    expr = parse_ql(query)
    return transformer.transform(expr)
