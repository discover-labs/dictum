from copy import deepcopy
from itertools import chain

from lark import Tree
from toolz import compose_left

from dictum import model, schema
from dictum.engine.aggregate_query_builder import AggregateQueryBuilder
from dictum.engine.computation import LiteralOrderItem, RelationalQuery
from dictum.engine.metrics import AddMetric, limit_transforms, transforms
from dictum.engine.operators import FinalizeOperator, MaterializeOperator, MergeOperator


def metric_expr(expr: Tree):
    expr = deepcopy(expr)
    for ref in expr.find_data("measure"):
        ref.data = "column"
        ref.children = [None, *ref.children]
    return expr


class Engine:
    def __init__(self, model: "model.Model"):
        self.model = model

    def suggest_dimensions(self, query: schema.Query):
        ...

    def suggest_measures(self, query: schema.Query):
        ...

    def get_range_computation(self, dimension_id: str) -> RelationalQuery:
        ...

    def get_values_computation(self, dimension_id: str) -> RelationalQuery:
        ...

    @staticmethod
    def validate_query(query: "schema.Query"):
        """Basic query validity checks"""
        # at least one metric is present
        if len(query.metrics) == 0:
            raise ValueError("You must request at least one metric")

        # no duplicate column names
        names = set()
        for request in chain(query.metrics, query.dimensions):
            name = request.name
            if name in names:
                raise ValueError(f"Duplicate column name in query: {name}")
            names.add(name)

        # all OF/WITHIN dimensions are also present in query.dimensions
        dimensions_digests = set(r.digest for r in query.dimensions)
        for request in query.metrics:
            for transform in request.metric.transforms:
                for item in chain(transform.of, transform.within):
                    exc = ValueError(
                        "All dimensions used in OF/WITHIN must also be present in the "
                        "query's dimension list.\n"
                        f"Metric: {request.render()}\nTransform: {transform.id}\n"
                        f"Dimension expression: {item.render()}"
                    )
                    if item.digest not in dimensions_digests:
                        raise exc

    def get_terminal(self, query: "schema.Query") -> MergeOperator:
        self.validate_query(query)

        builder = AggregateQueryBuilder(
            model=self.model, dimensions=query.dimensions, filters=query.filters
        )

        merge = MergeOperator(query=query)

        # add metrics
        adders = []
        for request in query.metrics:
            if len(request.metric.transforms) == 0:
                adders.append(AddMetric(request=request, builder=builder))
            elif len(request.metric.transforms) == 1:
                transform_id = request.metric.transforms[0].id
                adder = transforms.get(transform_id)
                if adder is None:
                    raise KeyError(f"Transform {transform_id} does not exist")
                adders.append(adder(request=request, builder=builder))

        for metric in query.limit:
            transform_id = metric.transforms[0].id
            adder = limit_transforms.get(transform_id)
            if adder is None:
                raise KeyError(f"Transform {transform_id} does not exist")
            adders.append(adder(metric=metric, builder=builder))

        return compose_left(*adders)(merge)

    def get_computation(self, query: schema.Query) -> MergeOperator:
        terminal = self.get_terminal(query)
        terminal.order = [LiteralOrderItem(r.digest, True) for r in query.dimensions]
        return FinalizeOperator(
            input=MaterializeOperator([terminal]),
            aliases={r.digest: r.name for r in query.metrics + query.dimensions},
        )
