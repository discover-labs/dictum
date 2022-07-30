from typing import List, Optional

from lark import Token, Tree

import dictum.engine.engine
from dictum.engine.aggregate_query_builder import AggregateQueryBuilder
from dictum.engine.computation import Column
from dictum.engine.operators import (
    FilterOperator,
    MaterializeOperator,
    MergeOperator,
    QueryOperator,
    RecordsFilterOperator,
)
from dictum.engine.result import DisplayInfo
from dictum.model import Metric, Model
from dictum.schema import (
    FormatConfig,
    Query,
    QueryDimension,
    QueryDimensionRequest,
    QueryMetric,
    QueryMetricRequest,
    QueryTableTransform,
)


class AddMetric:
    """Add a metric to a merge.
    - For each measure of the metric
      - Add the measure aggregation to the merge (if it's not already there)
    - Add the necessary calculation to the merge.
    """

    def __init__(
        self,
        request: QueryMetricRequest,
        builder: Optional[AggregateQueryBuilder] = None,
    ):
        self.request = request
        self.builder = builder

    @property
    def model(self) -> Model:
        return self.builder.model

    @property
    def metric(self) -> Metric:
        return self.model.metrics.get(self.request.metric.id)

    def add_measures(self, merge: MergeOperator) -> MergeOperator:
        existing_measures = {
            q.input._aggregate[0].name
            for q in merge.inputs
            if isinstance(q, QueryOperator)
        }
        for measure in self.metric.measures:
            if measure.id not in existing_measures:
                aggregation = self.builder.get_aggregation(measure)
                merge.add_query(QueryOperator(aggregation))
        return merge

    def get_terminal_for_query(self, query: Query) -> MergeOperator:
        engine = dictum.engine.engine.Engine(self.model)
        return engine.get_terminal(query=query)

    def __call__(self, merge: MergeOperator):
        merge = self.add_measures(merge)
        column = Column(
            name=self.request.digest,
            expr=self.metric.merged_expr,
            type=self.metric.type,
            display_info=DisplayInfo(
                display_name=(
                    self.metric.name if not self.request.alias else self.request.alias
                ),
                column_name=self.request.name,
                format=self.metric.format,
                type=self.metric.type,
                kind="metric",
            ),
        )
        merge.metrics.append(column)
        return merge


transforms = {}


class AddTransformedMetric(AddMetric):
    def __init_subclass__(cls) -> None:
        if hasattr(cls, "id"):
            transforms[cls.id] = cls

    @property
    def transform(self):
        return self.request.metric.transforms[0]

    def get_transform_terminal(
        self,
        request: Optional[QueryMetricRequest] = None,
        dimensions: Optional[List[QueryDimension]] = None,
        filters: Optional[List[QueryDimension]] = None,
    ) -> MergeOperator:
        # create our own query based on the transform
        # dimensions are of + within if not specified
        if request is None:
            request = self.request

        if dimensions is None:
            dimensions = [*self.transform.of, *self.transform.within]

        dimensions = [QueryDimensionRequest(dimension=d) for d in dimensions]

        if filters is None:
            filters = self.builder.filters

        # ignore alias and transforms
        query = Query(
            metrics=[QueryMetricRequest(metric=QueryMetric(id=request.metric.id))],
            dimensions=dimensions,
            filters=filters,
        )
        result = self.get_terminal_for_query(query)

        # replace with the request's expected column name
        result.metrics[0].name = request.digest

        return result

    def get_unlisted_query_dimensions(self) -> List[QueryDimension]:
        """Get a list of requests for dimensions that appear neither
        in "of" nor in "within".
        """
        digests = {d.digest for d in self.transform.of} | {
            d.digest for d in self.transform.within
        }
        return [
            r.dimension
            for r in self.builder.dimensions
            if r.dimension.digest not in digests
        ]


limit_transforms = {}


class AddLimit(AddTransformedMetric):
    """A metric adder user for transforms that are only used in query's limit clause"""

    def __init_subclass__(cls) -> None:
        if hasattr(cls, "id"):
            limit_transforms[cls.id] = cls


class AddTopBottomLimit(AddLimit):
    """Adds a top and or bottom limit to the computation.

    The general logic is that we need to construct a query
    with the requested metric, wrap the metric in row_number
    and only leave the rows where row_number is <= (or >=)
    than the specified limit. Then the dimension tuples of
    the result are taken and put into the WHERE clause of
    each measure query. So basically we first compute which
    dimension values must be in the result and then filter
    by these values.

    Multiple such queries are computed in parallel saving
    time, but generally this requires at least two separate
    backend queries to be run in sequence.

    TODO: optimize by computing everything in the database
    when there's only one limit (with an inner join to subquery)
    """

    ascending: bool

    def __init__(
        self, metric: QueryMetric, builder: Optional[AggregateQueryBuilder] = None
    ):
        super().__init__(QueryMetricRequest(metric=metric), builder)

    def wrap_in_row_number(self, merge: MergeOperator, within: List[QueryDimension]):
        """Add row_number to the terminal operator."""
        column = merge.columns[-1]
        metric_expr = column.expr.children[0]
        order_by = Tree(
            "order_by",
            [Tree("order_by_item", [metric_expr, self.ascending])],
        )

        within_names = {r.digest for r in within}
        partition_by = Tree(
            "partition_by", [c.expr for c in merge.columns if c.name in within_names]
        )

        column.expr = Tree(
            "expr",
            [
                Tree(
                    "call_window",
                    ["row_number", metric_expr, partition_by, order_by, None],
                )
            ],
        )
        column.name = "__row_number"
        column.type = "int"
        return merge

    def __call__(self, merge: MergeOperator):
        # if "of" is empty then "of" is everything that's not "within"
        if len(self.transform.of) == 0:
            # TODO: do not mutate the original request
            self.transform.of = self.get_unlisted_query_dimensions()

        terminal = self.get_transform_terminal()
        terminal = self.wrap_in_row_number(terminal, self.transform.within)

        # add <= filter by row_number
        terminal = FilterOperator(
            input=terminal,
            conditions=[
                Tree(
                    "le",
                    [
                        Tree("column", [None, "__row_number"]),
                        Token("INTEGER", self.transform.args[0]),
                    ],
                )
            ],
        )

        # if the inputs to the merge are TuplesFilters, it means that
        # this top isn't the first, so we just add the terminal to
        # materialize
        if all(isinstance(i, RecordsFilterOperator) for i in merge.inputs):
            materialized = merge.inputs[0].materialized
            materialized.inputs.append(terminal)
            return merge

        # otherwize create MaterializeOperator and add a TuplesFilter
        # before each query

        # terminal Merge -> Materialize
        materialized = MaterializeOperator([terminal])

        # add TuplesFilter to each input of the original merge
        # (excluding merges which mean transformed metrics)
        new_inputs = []
        for input in merge.inputs:
            new_inputs.append(
                RecordsFilterOperator(
                    query=input, materialized=materialized, drop_last_column=True
                )
            )
        merge.inputs = new_inputs

        return merge


class AddTopLimit(AddTopBottomLimit):
    id = "top"
    name = "Top"
    ascending: bool = False


class AddBottomLimit(AddTopBottomLimit):
    id = "bottom"
    name = "Bottom"
    ascending: bool = True


class AddTotalMetric(AddTransformedMetric):
    """Totals are computed as a merge added as a source to the merge."""

    id = "total"
    name = "Total"

    def get_column(self) -> Column:
        return

    def add_base_dimensions(self, merge: MergeOperator):
        """To have all the dimensions in the merge for sure, we have to add the measures
        for the original metric in case the total is the only one requested
        """
        merge = AddMetric(request=self.request, builder=self.builder)(merge)
        merge.metrics.pop(-1)  # remove the last metric, we only need the query

    def get_total_metric_request(
        self, dimensions: Optional[List[QueryDimension]] = None
    ) -> QueryMetricRequest:
        if dimensions is None:
            dimensions = [*self.transform.of, *self.transform.within]
        return QueryMetricRequest(
            metric=QueryMetric(
                id=self.metric.id,
                transforms=[QueryTableTransform(id="total", within=dimensions)],
            )
        )

    def __call__(self, merge: MergeOperator):
        # TODO: optimize by using get_expr_total_function
        # if the total function is defined (expr is additive),
        # then use a window function instead of adding another
        # query to the merge

        self.add_base_dimensions(merge)
        terminal = self.get_transform_terminal(request=self.get_total_metric_request())
        merge.add_merge(terminal)
        column = Column(
            name=self.request.name,
            expr=Tree("expr", [Tree("column", [None, terminal.metrics[0].name])]),
            type=self.metric.type,
            display_info=DisplayInfo(
                display_name=(
                    f"{self.metric.name} (Total)"
                    if self.request.alias is None
                    else self.request.alias
                ),
                column_name=self.request.name,
                format=self.metric.format,
                type=self.metric.type,
                kind="metric",
            ),
        )
        merge.metrics.append(column)
        return merge


class AddPercentMetric(AddTotalMetric):
    id = "percent"
    name = "Percent"

    def get_metric_expr(self) -> Tree:
        return self.metric.merged_expr.children[0]

    def __call__(self, merge: MergeOperator):
        """Percent actually includes two separate queries:
        - the value for the numerator
        - the value for the denominator

        cases (all by country, city, region):

        1. bare percent — all rows add up to 100%
            divide metric by total
        2. percent within (country) — all tuples within country add up to 100%
            so "of" is evetyhing that's not "within"
            just divide metric by total like above
        3. percent of (city) within (country) — ignores region
            numerator: total within (city, country)
            denominator: total within (country)
        4. percent of (city) — all cities within each tuple add up to 100%
            "within" is everything that's not "of", i.e.
            percent of (city) within (country, region)
            This case gets reduced to the previous case:
                numerator: total within (city, country, region)
                denominator: total within (country, region)
            The numerator is already computed — it's the metric itself, so we can just
            divide the metric by total within (country, region)
        """
        self.add_base_dimensions(merge)

        # figure out which case we're dealing with
        # based on that info, we can construct queries for the numerator and denominator
        if len(self.transform.of) == 0:
            # cases 1 and 2, just divide metric by total
            numerator = self.get_metric_expr()
            dimensions = [*self.transform.of, *self.transform.within]
            denominator_terminal = self.get_transform_terminal(
                request=self.get_total_metric_request(dimensions),
                dimensions=dimensions,
            )
            denominator = Tree("column", [None, denominator_terminal.metrics[0].name])
            merge.add_merge(denominator_terminal)
        elif len(self.transform.within) == 0:
            # case 4, of present, within absent
            dimensions = self.get_unlisted_query_dimensions()
            denominator_terminal = self.get_transform_terminal(
                request=self.get_total_metric_request(dimensions),
                dimensions=dimensions,
            )
            denominator = Tree("column", [None, denominator_terminal.metrics[0].name])
            numerator = self.get_metric_expr()
            merge.add_merge(denominator_terminal)
        else:
            # case 3, we need to actually construct two terminals
            # like in total, add the metric query
            merge = AddMetric(request=self.request, builder=self.builder)(merge)
            merge.metrics.pop(-1)  # remove the last metric, we only need the query

            # add numerator
            dimensions = [*self.transform.of, *self.transform.within]
            numerator_terminal = self.get_transform_terminal(
                request=self.get_total_metric_request(dimensions),
                dimensions=self.transform.of + self.transform.within,
            )
            numerator = Tree("column", [None, numerator_terminal.metrics[0].name])
            merge.add_merge(numerator_terminal)

            denominator_terminal = self.get_transform_terminal(
                request=self.get_total_metric_request(self.transform.within),
                dimensions=self.transform.within,
            )
            denominator = Tree("column", [None, denominator_terminal.metrics[0].name])
            merge.add_merge(denominator_terminal)

        column = Column(
            name=self.request.name,
            expr=Tree(
                "expr",
                [Tree("div", [numerator, denominator])],
            ),
            type="float",
            display_info=DisplayInfo(
                display_name=(
                    f"{self.metric.name} (%)"
                    if self.request.alias is None
                    else self.request.alias
                ),
                column_name=self.request.name,
                format=FormatConfig(kind="percent"),
                type=self.metric.type,
                kind="metric",
            ),
        )
        merge.metrics.append(column)
        return merge


class AddAdditivelyTransformedMetric(AddTransformedMetric):
    """Sum, max, min"""

    def get_column(self) -> Column:
        raise NotImplementedError

    def __call__(self, merge: MergeOperator):
        # we have to add the measures for the original metric in case this transform
        # is the only one requested
        merge = AddMetric(request=self.request, builder=self.builder)(merge)
        merge.metrics.pop(-1)  # remove the last metric, we only need the query

        merge.metrics.append(self.get_column())
        return merge


class AddSumMetric(AddAdditivelyTransformedMetric):
    id = "sum"
    name = "Sum"

    def get_column(self) -> Column:
        expr = self.metric.merged_expr.children[0]
        dimensions = self.transform.of + self.transform.within
        partition_by = Tree(
            "partition_by", [Tree("column", [None, d.digest]) for d in dimensions]
        )
        return Column(
            name=self.request.name,
            expr=Tree(
                "expr", [Tree("call_window", ["sum", expr, partition_by, None, None])]
            ),
            type=self.metric.type,
            display_info=DisplayInfo(
                display_name=(
                    self.metric.name
                    if self.request.alias is None
                    else self.request.alias
                ),
                column_name=self.request.name,
                format=self.metric.format,
                type=self.metric.type,
                kind="metric",
            ),
        )
