from lark import Transformer, Tree

from dictum.ql.parser import (
    parse_dimension,
    parse_dimension_request,
    parse_metric_request,
    parse_ql,
)
from dictum.schema.query import (
    Query,
    QueryDimension,
    QueryDimensionRequest,
    QueryMetric,
    QueryMetricRequest,
    QueryScalarTransform,
    QueryTableTransform,
)


class QlTransformer(Transformer):
    """Compiles a QL query AST into a Query object."""

    def table_transform(self, children: list):
        id, *rest = children
        args = []
        of, within = [], []
        for item in rest:
            if isinstance(item, Tree):
                if item.data == "of":
                    of = item.children
                elif item.data == "within":
                    within = item.children
            else:
                args.append(item)
        return QueryTableTransform(id=id.lower(), args=args, of=of, within=within)

    def metric(self, children: list):
        id, *transforms = children
        return QueryMetric(id=id, transforms=transforms)

    def scalar_transform(self, children: list):
        id, *args = children
        return QueryScalarTransform(id=id.lower(), args=args)

    def dimension(self, children: list):
        id, *transforms = children
        return QueryDimension(id=id, transforms=transforms)

    def alias(self, children: list):
        return children[0]

    def dimension_request(self, children: list):
        dimension, *rest = children
        alias = rest[0] if rest else None
        return QueryDimensionRequest(dimension=dimension, alias=alias)

    def metric_request(self, children: list):
        metric, *rest = children
        alias = rest[0] if rest else None
        return QueryMetricRequest(metric=metric, alias=alias)

    def select(self, children: list):
        return children

    def query(self, children: list):
        metrics, *rest = children
        filters, dimensions, limit = [], [], []
        for item in rest:
            if item.data == "where":
                filters = item.children
            elif item.data == "groupby":
                dimensions = item.children
            elif item.data == "limit":
                limit = item.children
        return Query(
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            limit=limit,
        )


ql_transformer = QlTransformer()


def compile_query(query: str) -> Query:
    return ql_transformer.transform(parse_ql(query))


def compile_dimension(expr: str) -> QueryDimension:
    return ql_transformer.transform(parse_dimension(expr))


def compile_dimension_request(expr: str) -> QueryDimensionRequest:
    return ql_transformer.transform(parse_dimension_request(expr))


def compile_metric_request(expr: str) -> QueryMetricRequest:
    return ql_transformer.transform(parse_metric_request(expr))
