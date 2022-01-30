from collections import defaultdict
from copy import deepcopy
from typing import List

from lark import Tree
from toolz import compose_left

from dictum import model, schema, utils
from dictum.engine.computation import Column, RelationalQuery
from dictum.engine.operators import (
    FinalizeOperator,
    MaterializeOperator,
    MergeOperator,
    QueryOperator,
)
from dictum.engine.result import DisplayInfo


def metric_expr(expr: Tree):
    expr = deepcopy(expr)
    for ref in expr.find_data("measure"):
        ref.data = "column"
        ref.children = [None, *ref.children]
    return expr


class Engine:
    def suggest_dimensions(self, query: schema.Query):
        ...

    def suggest_measures(self, query: schema.Query):
        ...

    def get_range_computation(self, dimension_id: str) -> RelationalQuery:
        ...

    def get_values_computation(self, dimension_id: str) -> RelationalQuery:
        ...

    def get_dimension_column(
        self, anchor: "model.Table", request: "model.ResolvedQueryDimensionRequest"
    ) -> Column:
        dimension = request.dimension
        try:
            path = anchor.dimension_join_paths[dimension.id]
        except KeyError:
            raise KeyError(
                f"You requested {dimension}, but it can't be used with "
                f"another measure that you requested on {anchor}"
            )
        if isinstance(request.dimension, model.DimensionsUnion):
            dimension = anchor.allowed_dimensions.get(dimension.id)
        expr = dimension.prefixed_expr(path)
        column = Column(
            name=request.name,
            expr=expr,
            type=dimension.type,
            display_info=DisplayInfo(name=dimension.name, format=dimension.format),
        )
        return compose_left(*request.transforms)(column)

    def get_aggregation(
        self,
        measures: List["model.Measure"],
        dimensions: List["model.ResolvedQueryDimensionRequest"],
        filters: List["model.ResolvedQueryDimensionRequest"],
    ) -> RelationalQuery:
        anchor = measures[0].table
        result = RelationalQuery(source=anchor, join_tree=[])

        # add dimensions
        for request in dimensions:
            column = self.get_dimension_column(anchor, request)
            for path in column.join_paths:
                result.add_join_path(path)
            result.add_groupby(column)

        # add measures
        for measure in measures:
            column = Column(
                name=measure.id, expr=deepcopy(measure.expr), type=measure.type
            )
            for path in column.join_paths:
                result.add_join_path(path)
            result.add_aggregate(column)

        # add filters
        for filter in filters:
            column = self.get_dimension_column(anchor, filter)
            assert column.type == "bool"
            for path in column.join_paths:
                result.add_join_path(path)
            result.filters.append(column.expr)

        # add anchor table's filters
        for f in anchor.filters:
            expr = deepcopy(f.expr)
            # add joins necessary for the filter
            for ref in expr.find_data("column"):
                _, *path, _ = ref.children
                result.add_join_path(path)
            result.filters.append(expr)

        return result

    def get_terminal(self, query: "model.ResolvedQuery") -> MergeOperator:
        if len(query.metrics) == 0:
            raise ValueError("You must request at least one metric")

        # group measures by table, don't add the same measure twice
        tables = defaultdict(set)
        for request in query.metrics:
            for measure in request.metric.measures:
                tables[measure.table].add(measure)

        queries = []
        # add aggregate queries
        for measures in tables.values():
            child_query = self.get_aggregation(
                measures=list(measures),
                dimensions=query.dimensions,
                filters=query.filters,
            )
            queries.append(QueryOperator(input=child_query))

        # add limits first
        transforms = []
        for limit in query.limit:
            for transform in limit.transforms:
                transforms.append((transform, None))  # second item is Column

        metrics = []
        for request in query.metrics:
            display_name = (
                request.alias if request.alias is not None else request.metric.name
            )
            column = Column(
                name=request.name,
                expr=metric_expr(request.metric.expr),
                type=request.metric.type,
                display_info=DisplayInfo(
                    name=display_name,
                    type=request.metric.type,
                    format=request.metric.format,
                    keep_name=request.alias is not None,
                ),
            )
            metrics.append(column)
            for transform in request.transforms:
                column.display_info = transform.get_display_info(column.display_info)
                transforms.append((transform, column))

        dimensions = []
        for request in query.dimensions:
            display_name = (
                request.alias if request.alias is not None else request.dimension.name
            )
            column = Column(
                name=request.name,
                expr=utils.column_expr(request.name),
                type=request.dimension.type,
                display_info=DisplayInfo(
                    name=display_name,
                    type=request.dimension.type,
                    format=request.dimension.format,
                    keep_name=request.alias is not None,
                ),
            )
            for transform in request.transforms:
                column.display_info = transform.get_display_info(column.display_info)
                column.type = transform.get_return_type(column.type)
            dimensions.append(column)

        terminal = MergeOperator(
            inputs=queries,
            columns=[*dimensions, *metrics],
        )

        for transform, column in transforms:
            transform_query = self.get_terminal(transform.query)
            terminal = transform(terminal, transform_query, column)

        return terminal

    def get_computation(self, query: "model.ResolvedQuery") -> MergeOperator:
        terminal = self.get_terminal(query)
        return FinalizeOperator(
            input=MaterializeOperator([terminal]),
            aliases={
                r.name: r.alias
                for r in query.metrics + query.dimensions
                if r.alias is not None
            },
        )
