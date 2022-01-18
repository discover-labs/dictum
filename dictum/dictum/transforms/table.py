from typing import List, Optional

from lark import Tree

from dictum import engine, model, schema
from dictum.transforms.base import BaseTransform
from dictum.utils import subselect_column, value_to_token

transforms = {}


class TableTransform(BaseTransform):
    """While ScalarTransform operates only on a single expression, TableTransform
    is also applied to a Computation as a whole.

    With a metric and a grouping, a table transform is a small computation itself. So,
    the ResolvedQuery is provided by the resolving model, and the computation can be
    constructed by the calling engine.
    """

    id: str
    name: str
    description: Optional[str] = None
    return_type: Optional[str] = None

    def __init__(
        self,
        *args,
        metric_id: str,
        query: "model.ResolvedQuery",
        of: Optional[List["model.ResolvedQueryDimensionRequest"]] = None,
        within: Optional[List["model.ResolvedQueryDimensionRequest"]] = None,
    ):
        self.metric_id = metric_id
        self.query = query
        self.of = of or []
        self.within = within or []
        super().__init__(*args)

    def __init_subclass__(cls):
        if hasattr(cls, "id"):
            transforms[cls.id] = cls

    def __call__(
        self,
        terminal: "engine.Operator",
        transform: "engine.Operator",
        column: Optional["engine.Column"],
    ) -> "engine.Operator":
        raise NotImplementedError


class TopBottomTransform(TableTransform):
    ascending: bool

    def __init__(
        self,
        n: int,
        metric_id: str,
        query: "model.ResolvedQuery",
        of: Optional[List["model.ResolvedQueryDimensionRequest"]] = None,
        within: Optional[List["model.ResolvedQueryDimensionRequest"]] = None,
    ):
        self.n = n
        super().__init__(n, metric_id=metric_id, query=query, of=of, within=within)

    def transform_transform(self, op: "engine.Operator"):
        if len(self.within) == 0:
            if isinstance(op, engine.QueryOperator):
                op.limit = self.n
                op.order = [
                    engine.LiteralOrderItem(
                        name=op.input._aggregate[0].name, ascending=self.ascending
                    )
                ]
                return op
            if isinstance(op, engine.MergeOperator):
                op.limit = self.n
                op.order = [
                    engine.LiteralOrderItem(
                        name=op.columns[-1].name, ascending=self.ascending
                    )
                ]
                return op
        else:
            if isinstance(op, engine.QueryOperator):
                op.input._aggregate[0].expr = self.wrap_in_row_number(
                    op.input._aggregate[0].expr.children[0], op.input._groupby
                )
                return engine.FilterOperator(
                    op,
                    [
                        Tree(
                            "le",
                            [
                                Tree("column", [None, op.input._aggregate[0].name]),
                                value_to_token(self.n),
                            ],
                        )
                    ],
                )
            elif isinstance(op, engine.MergeOperator):
                # last column is always the metric
                op.columns[-1].expr = self.wrap_in_row_number(
                    op.columns[-1].expr, op.columns[:-1]
                )
                return engine.FilterOperator(
                    op,
                    [
                        Tree(
                            "le",
                            [
                                Tree("column", [None, op.columns[-1].name]),
                                value_to_token(self.n),
                            ],
                        )
                    ],
                )
        raise TypeError

    def wrap_in_row_number(self, expr: Tree, groupby: List["engine.Column"]) -> Tree:
        within_names = set(r.name for r in self.within)
        partition_by = Tree(
            "partition_by", [c.expr for c in groupby if c.name in within_names]
        )
        order_by = Tree("order_by", [Tree("order_by_item", [expr, self.ascending])])
        return Tree("call_window", ["row_number", expr, partition_by, order_by, None])

    def __call__(
        self,
        terminal: "engine.MergeOperator",
        transform: "engine.Operator",
        column: Optional["engine.Column"],
    ):
        transform = self.transform_transform(transform)

        if len(terminal.inputs) == 1:
            # there's only on input to the merge, so the merge will be a no-op
            # this means that the user's query requested a measure
            input = terminal.inputs[0]

            if isinstance(input, (engine.QueryOperator, engine.InnerJoinOperator)):
                # inject the transform as another inner join
                terminal.inputs = [engine.InnerJoinOperator(input, transform)]
                return terminal
            else:
                # this shouldn't happen
                raise TypeError(
                    f"Unexpected merge single input for top: {input.__class__}"
                )
        else:
            # there are multiple input queries
            if all(isinstance(i, engine.TuplesFilterOperator) for i in terminal.inputs):
                # this means that there's already a top with a tuples filter
                # just add self to materialize
                materialize: engine.MaterializeOperator = terminal.inputs[
                    0
                ].materialized
                materialize.inputs.append(transform)
                return terminal
            elif all(isinstance(i, engine.QueryOperator) for i in terminal.inputs):
                # this is the first top, so add materialize and filter with tuples
                materialize = engine.MaterializeOperator([transform])
                filtered = [
                    engine.TuplesFilterOperator(
                        query, materialize, drop_last_column=True
                    )
                    for query in terminal.inputs
                ]
                return engine.MergeOperator(filtered, terminal.columns)

        # this shouldn't happen
        raise TypeError(f"Unexpected terminal type: {terminal.__class__}")


class TopTransform(TopBottomTransform):
    id = "top"
    name = "Top"
    ascending = False


class BottomTransform(TopBottomTransform):
    id = "bottom"
    name = "Bottom"
    ascending = True


class TotalTransform(TableTransform):
    """Calculate a total value on a given level of detail.

    Uses get_expr_total_function. If a function can be defined for an expression,
    compute with a window function. If not, do a subquery join to calculate the total.
    """

    id = "total"
    name = "Total"

    def get_display_name(self, name: str) -> str:
        return f"{name} (∑)"

    def __call__(
        self,
        terminal: "engine.MergeOperator",
        transform: "engine.MergeOperator",
        column: Optional["engine.Column"],
    ) -> "engine.Operator":
        terminal.inputs.append(transform)
        transformed_column = subselect_column(transform.columns[-1])
        column.expr = transformed_column.expr
        return terminal


class PercentTransform(TotalTransform):
    id = "percent"
    name = "Percent of Total"
    return_type = "float"

    def get_format(self, format: schema.FormatConfig) -> schema.FormatConfig:
        return schema.FormatConfig(kind="percent")

    def get_display_name(self, name: str) -> str:
        return f"{name} (%)"

    def __call__(
        self,
        terminal: "engine.MergeOperator",
        transform: "engine.MergeOperator",
        column: Optional["engine.Column"],
    ) -> "engine.Operator":
        # total's terminal
        merge: engine.MergeOperator = super().__call__(terminal, transform, column)

        total = merge.inputs[-1]
        name = total.columns[-1].name

        # divide metric by the total
        expr = Tree(
            "expr",
            [
                Tree(
                    "div",
                    [
                        Tree(
                            "call", ["tonumber", Tree("column", [None, self.metric_id])]
                        ),
                        Tree("column", [None, name]),
                    ],
                )
            ],
        )
        column.expr = expr
        column.type = "float"
        return merge


class SumTransform(TableTransform):
    """
    TODO
    """

    id = "sum"
    name = "Sum"
