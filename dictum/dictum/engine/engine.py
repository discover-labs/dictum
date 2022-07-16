from copy import deepcopy

from lark import Tree
from toolz import compose_left

from dictum import model, schema
from dictum.engine.aggregate_query_builder import AggregateQueryBuilder
from dictum.engine.computation import RelationalQuery
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

    def get_terminal(self, query: "schema.Query") -> MergeOperator:
        """
        - Create a Merge
        - For each metric:
            - For each measure in the metric
              check that the measure isn't already in the merge
              add measure to the merge
        """
        if len(query.metrics) == 0:
            raise ValueError("You must request at least one metric")

        builder = AggregateQueryBuilder(
            model=self.model, dimensions=query.dimensions, filters=query.filters
        )

        merge = MergeOperator(inputs=[])

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
        return FinalizeOperator(
            input=MaterializeOperator([terminal]),
            aliases={
                r.name: r.alias
                for r in query.metrics + query.dimensions
                if r.alias is not None
            },
        )
