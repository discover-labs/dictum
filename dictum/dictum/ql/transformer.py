from lark import Transformer

from dictum.ql.parser import parse_filter, parse_grouping, parse_ql
from dictum.query import (
    Query,
    QueryDimensionFilter,
    QueryDimensionRequest,
    QueryDimensionTransform,
    QueryMetricRequest,
)


class TransformMixin:
    def dimension(self, children: list):
        return children[0]

    def call(self, children: list):
        id, *args = children
        return QueryDimensionTransform(id=id.lower(), args=args)

    def filter(self, children: list):
        dimension, filter = children
        return QueryDimensionFilter(dimension=dimension, filter=filter)

    def grouping(self, children: list):
        dimension, *rest = children
        transform = None
        alias = None
        if len(rest) == 2:
            transform, alias = rest
        elif len(rest) == 1 and isinstance(rest[0], QueryDimensionTransform):
            transform = rest[0]
        elif len(rest) == 1:
            alias = rest[0]
        return QueryDimensionRequest(
            dimension=dimension, transform=transform, alias=alias
        )


class QlTransformer(TransformMixin, Transformer):
    """Compiles a QL query AST into a Query object."""

    def metric(self, children: list):
        """Return metric name as a string"""
        return QueryMetricRequest(metric=children[0])

    def select(self, children: list):
        """Just return a list of metric names"""
        return children

    def alias(self, children: list):
        return children[0]

    def where(self, children: list):
        return children

    def groupby(self, children: list):
        return children

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


ql_transformer = QlTransformer()


def compile_query(query: str) -> Query:
    return ql_transformer.transform(parse_ql(query))


class FilterTrasformer(TransformMixin, Transformer):
    pass


filter_transformer = FilterTrasformer()


def compile_filter(expr: str) -> QueryDimensionFilter:
    return filter_transformer.transform(parse_filter(expr))


class GroupingTransformer(TransformMixin, Transformer):
    pass


grouping_transformer = GroupingTransformer()


def compile_grouping(expr: str) -> QueryDimensionRequest:
    return grouping_transformer.transform(parse_grouping(expr))
