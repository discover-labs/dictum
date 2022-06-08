from dataclasses import dataclass
from typing import List

from toolz import compose_left

from dictum.engine.computation import Column, RelationalQuery
from dictum.engine.result import DisplayInfo
from dictum.model import DimensionsUnion, Measure, Model
from dictum.model.time import TimeDimension
from dictum.schema import QueryDimension, QueryDimensionRequest
from dictum.model.scalar import DatetruncTransform


@dataclass
class AggregateQueryBuilder:
    """Holds a list of dimensions and filters that must be applied
    for a given query.

    Contains helper methods that allow to build a query with necessary
    dimensions and filters from any given anchor table.
    """

    model: Model
    dimensions: List[QueryDimensionRequest]
    filters: List[QueryDimension]

    def get_dimension_column(
        self, measure: Measure, request: QueryDimensionRequest
    ) -> Column:
        """Construct a Column with a transformed expression relative to
        a given measure's anchor table.
        """
        anchor = measure.table
        dimension = self.model.dimensions.get(request.dimension.id)

        # if union, replace dimension with it
        if isinstance(dimension, DimensionsUnion):
            dimension = anchor.allowed_dimensions.get(dimension.id)

        transforms = [
            self.model.scalar_transforms[t.id](*t.args)
            for t in request.dimension.transforms
        ]

        # if generic time, prepend transforms with datetrunc
        # and replace the dimension with measure's time
        if isinstance(dimension, TimeDimension):
            if dimension.period is not None:
                transforms = [DatetruncTransform(dimension.period), *transforms]
                if measure.time is None:
                    raise ValueError(
                        f"You requested a generic Time dimension with {measure}, "
                        "but it doesn't have a time dimension specified"
                    )
            dimension = measure.time

        # get the expression with join info
        try:
            join_path = anchor.dimension_join_paths[dimension.id]
        except KeyError:
            raise KeyError(
                f"You requested {dimension}, but it can't be used with "
                f"another measure that you requested on {anchor}"
            )
        expr = dimension.prefixed_expr(join_path)

        result = Column(
            name=request.name,
            expr=expr,
            type=dimension.type,
            display_info=DisplayInfo(
                name=dimension.name if not request.alias else request.alias,
                format=dimension.format,
            ),
        )

        return compose_left(*transforms)(result)

    def get_aggregation(self, measure: Measure) -> RelationalQuery:
        anchor = measure.table
        result = RelationalQuery(source=anchor, join_tree=[])

        for dimension in self.dimensions:
            column = self.get_dimension_column(measure, dimension)
            result.add_groupby(column)

        for filter in self.filters:
            # create a fake request because filters are not requests
            # and get_dimension_column expects a request
            request = QueryDimensionRequest(dimension=filter)
            column = self.get_dimension_column(measure, request)
            result.add_filter_expr(column.expr)  # add just the expr

        for filter in anchor.filters:
            result.add_filter_expr(filter.expr)

        if measure.filter:
            result.add_filter_expr(measure.filter)

        result.add_aggregate(
            column=Column(name=measure.id, expr=measure.expr, type=measure.type)
        )

        return result
