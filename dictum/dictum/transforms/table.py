from typing import List, Optional

from lark import Tree

from dictum import engine, model
from dictum.model import utils
from dictum.transforms.base import BaseTransform
from dictum.utils import value_to_token

transforms = {}


def subselect_column(column: "engine.Column") -> "engine.Column":
    return engine.Column(
        name=column.name,
        expr=Tree("expr", [Tree("column", [None, column.name])]),
        type=column.type,
    )


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
        self, terminal: "engine.Operator", transform: "engine.Operator"
    ) -> engine.Operator:
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

    def wrap_in_row_number(self, expr: Tree, groupby: List[engine.Column]) -> Tree:
        within_names = set(r.name for r in self.within)
        partition_by = Tree(
            "partition_by", [c.expr for c in groupby if c.name in within_names]
        )
        order_by = Tree("order_by", [Tree("order_by_item", [expr, self.ascending])])
        return Tree("call_window", ["row_number", expr, partition_by, order_by, None])

    def __call__(
        self,
        terminal: "engine.Operator",
        transform: "engine.Operator",
    ):
        transform = self.transform_transform(transform)

        if isinstance(terminal, (engine.QueryOperator, engine.InnerJoinOperator)):
            return engine.InnerJoinOperator(terminal, transform)

        elif isinstance(terminal, engine.MergeOperator):
            if all(isinstance(i, engine.TuplesFilterOperator) for i in terminal.inputs):
                materialize: engine.MaterializeOperator = terminal.inputs[
                    0
                ].materialized
                materialize.inputs.append(transform)
                return terminal
            else:
                materialize = engine.MaterializeOperator([transform])
                filtered = [
                    engine.TuplesFilterOperator(
                        query, materialize, drop_last_column=True
                    )
                    for query in terminal.inputs
                ]
                return engine.MergeOperator(filtered, terminal.columns)

        breakpoint()
        raise TypeError


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

    def __call__(
        self, terminal: "engine.MergeOperator", transform: "engine.MergeOperator"
    ) -> "engine.Operator":
        # if isinstance(terminal, engine.QueryOperator):
        #     columns = list(map(subselect_column, terminal.input.columns))
        #     if isinstance(transform, engine.QueryOperator):
        #         columns.append(subselect_column(transform.input._aggregate[0]))
        #     elif isinstance(transform, engine.MergeOperator):
        #         columns.append(subselect_column(transform.columns[-1]))
        #     else:
        #         raise TypeError
        #     return engine.MergeOperator([terminal, transform], columns)
        # elif isinstance(terminal, engine.MergeOperator):
        terminal.inputs.append(transform)
        terminal.columns.append(subselect_column(transform.columns[-1]))
        return terminal


class PercentTransform(TotalTransform):
    id = "percent"
    name = "Percent of Total"

    def __call__(
        self, terminal: "engine.MergeOperator", transform: "engine.MergeOperator"
    ) -> "engine.Operator":
        # total's terminal
        merge: engine.MergeOperator = super().__call__(terminal, transform)
        total = merge.inputs[-1]
        name = total.columns[-1].name
        expr = Tree(
            "expr",
            [
                Tree(
                    "div",
                    [
                        Tree("column", [None, self.metric_id]),
                        Tree("column", [None, name]),
                    ],
                )
            ],
        )
        merge.columns[-1] = engine.Column(name=name, expr=expr, type="float")
        return merge


class SumTransform(TableTransform):
    id = "sum"
    name = "Sum"

    def transform_expr(self, expr: Tree) -> Tree:
        """The argument is a merged column expression.

        Window func expression is:
            Tree("call_window", [
                func_name,
                *args,
                partition_by,
                order_by,
                [window_start, window_end]
            ])

        All parts are always present, to at least 4 children are required.
        """
        partition_by = []
        names = [utils.merged_expr(r.name) for r in self._of + self._within]
        if names:
            partition_by = names
        return Tree(
            "call_window", ["sum", expr, Tree("partition_by", partition_by), None, None]
        )


class PercentTransform(TableTransform):
    """Like total, but divides the value by the total."""
