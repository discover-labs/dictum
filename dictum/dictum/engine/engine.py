from collections import defaultdict
from copy import deepcopy
from typing import List

from lark import Tree
from toolz import compose_left

from dictum import model, schema
from dictum.engine.computation import Column, Computation, RelationalQuery


def column_expr(name: str):
    return Tree("expr", [Tree("column", [None, name])])


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
        path = anchor.dimension_join_paths[dimension.id]
        if isinstance(request.dimension, model.DimensionsUnion):
            dimension = anchor.allowed_dimensions.get(dimension.id)
        expr = dimension.prefixed_expr(path)
        column = Column(name=request.name, expr=expr, type=dimension.type)
        return compose_left(*request.transforms)(column)

    def get_aggregation(
        self,
        measures: List["model.Measure"],
        dimensions: List["model.ResolvedQueryDimensionRequest"],
        filters: List["model.ResolvedQueryDimensionRequest"],
    ) -> RelationalQuery:
        anchor = measures[0].table
        result = RelationalQuery(source=anchor, joins=[])

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

        # add literal filters
        result.filters.extend(deepcopy(f.expr) for f in anchor.filters)

        return result

    def get_computation(self, query: "model.ResolvedQuery") -> Computation:
        if len(query.metrics) == 0:
            raise ValueError("You must request at least one metric")

        # group measures by table
        tables = defaultdict(list)
        for request in query.metrics:
            for measure in request.metric.measures:
                tables[measure.table].append(measure)

        result = Computation()

        # add aggregate queries
        for measures in tables.values():
            child_query = self.get_aggregation(
                measures=measures, dimensions=query.dimensions, filters=query.filters
            )
            result.queries.append(child_query)

        # process dimensions for the top level
        for request in query.dimensions:
            result.merge_on.append(request.name)

            column = Column(
                name=request.name,
                expr=column_expr(request.name),
                type=request.dimension.type,
            )
            column.type = compose_left(*request.transforms)(column).type
            result.columns.append(column)

        # populate metrics dict and apply transforms to metric expressions
        table_transforms: List[model.TableTransform] = []
        for request in query.metrics:
            if len(request.transforms) > 0:
                # if there are transforms, we do not add this metric to the "main"
                # computation, the transform will handle everything
                table_transforms.extend(request.transforms)
                continue

            # otherwise add metric
            expr = deepcopy(request.metric.expr)
            for ref in expr.find_data("measure"):
                ref.data = "column"
                ref.children = [None, *ref.children]
            column = Column(name=request.name, expr=expr, type=request.metric.type)
            result.columns.append(column)

        # process limit
        for limit in query.limit:
            table_transforms.extend(limit.transforms)
            # expr = deepcopy(limit.metric.expr)
            # for ref in expr.find_data("measure"):
            #     ref.data = "column"
            #     ref.children = [None, *ref.children]
            # column = Column(name=limit.name, expr=expr, type=limit.metric.type)
            # column = compose_left(*limit.transforms)(column)
            # result.filters.append(column.expr)
            # for transform in limit.transforms:
            #     table_transforms.append(transform.transform_computation)

        # apply table transforms
        for transform in table_transforms:
            base = self.get_computation(transform.query)
            result = transform(base, result)

        result.prepare()
        return result
