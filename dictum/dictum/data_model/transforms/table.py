from copy import copy
from typing import List, Optional
from uuid import uuid4

from lark import Tree

from dictum.data_model import utils
from dictum.data_model.computation import (
    AggregateQuery,
    ColumnCalculation,
    Computation,
    Join,
    OrderItem,
)
from dictum.data_model.transforms.base import BaseTransform
from dictum.schema import QueryDimensionRequest
from dictum.utils import value_to_token

transforms = {
    "top": None,  # for attribute checks
    "bottom": None,
}


class TableTransform(BaseTransform):
    """While ScalarTransform operates only on a single expression, TableTransform
    is also applied to a Computation as a whole.
    """

    id: str
    name: str
    description: Optional[str] = None
    return_type: Optional[str] = None

    def __init__(self, *args, of: Optional[List] = None, within: Optional[List] = None):
        self._of = of or []
        self._within = within or []
        super().__init__(*args)

    def __init_subclass__(cls):
        if hasattr(cls, "id"):
            transforms[cls.id] = cls

    def transform_computation(self, computation: Computation):
        """Do nothing to the computation by default."""
        return computation


class TopBottomTransform(TableTransform):
    """
    revenue.top(10) of (city) within (country)

    Only allowed inside limit. Adds an inner join to each AggregateQuery. Doesn't have
    an ID, because isn't taken from the standard table_transforms dict. Requires access
    to the underlying metric and the parent data_model, because has to construct an
    AggregateQuery.

    - no of and no within
        - same anchor: order by + limit
        - different anchor: inner join, order by + limit
    - only within
        - same anchor: add a row number column, wrap in subquery with WHERE <= N
        - different anchor: inner join, row number with partition by within
    - both of and within
        - same anchor: inner join GROUP BY of and within, row number with partition by
          WITHIN, join ON <= N in condition
        - different anchor: same
    """

    def __init__(
        self,
        n: int,
        ascending: bool,
        metric,
        of: Optional[List] = None,
        within: Optional[List] = None,
    ):
        self._metric = metric
        self._n = n
        self._asc = ascending
        super().__init__(of=of, within=within)

    def transform_expr(self, expr: Tree) -> Tree:
        """All the logic is in transform_computation"""
        return expr

    def _get_measure(self, metric):
        """Extract a measure from the metric, additionally checking that the metric is
        valid for this transform.
        """
        if not metric.is_measure:
            raise ValueError(
                "Top transform can only be applied to metrics that were "
                "defined as measures"
            )
        return metric.measures[0]

    def get_join_expr(
        self, columns: List[ColumnCalculation], table_id: str, alias: str
    ) -> Tree:
        cols = {c.name: c.expr for c in columns}
        conditions = []
        for name, expr in cols.items():
            conditions.append(
                Tree("eq", [expr, Tree("column", [table_id, alias, name])])
            )
        return Tree("expr", [utils.join_exprs_with_and(conditions)])

    def filter_joins(self, joins: List[Join]):
        """To avoid duplicating joins when there are multiple top/bottom transforms
        applied, skip existing top joins.
        """
        result = []
        for join in joins:
            names = set(c.name for c in join.to.aggregate)
            if not (join.inner and "__top" in names):
                result.append(join)
        return result

    def transform_queries_basic(self, queries: List[AggregateQuery], measure):
        """Transform AggregateQueries in a "basic" case: when there are no "of" or
        "within" specified:
            - for the same anchor table: just order and limit
            - for another anchor table: inner join that same query"
        """
        main = next(filter(lambda q: q.table == measure.table, queries))
        main.limit = self._n
        main.order = [OrderItem(expr=measure.expr, ascending=self._asc)]

        # a shallow copy, because we only change a bool (subquery)
        sub = copy(main)
        sub.joins = self.filter_joins(main.joins)
        sub.subquery = True

        secondary = []
        for query in filter(lambda q: q.table != measure.table, queries):
            alias = str(uuid4())
            join = Join(
                to=sub,
                alias=alias,
                inner=True,
                expr=self.get_join_expr(query.groupby, query.table.id, alias),
            )
            query.joins.append(join)
            secondary.append(query)
        return [main, *secondary]

    def transform_queries_within(self, queries: List[AggregateQuery], measure):
        """Transform AggregateQueries in a "within" case: when there's only "within"
        specified and no "of" (assumed "of" for all columns).
            - for the same anchor table: wrap in a subquery
              TODO: actually implement it like this
            - for others: join on all dimension columns and __top <= N
        """
        main = next(filter(lambda q: q.table == measure.table, queries))

        sub = copy(main)
        sub.joins = self.filter_joins(main.joins)
        names = set(QueryDimensionRequest(dimension=d).name for d in self._within)
        partition_by = [c.expr for c in sub.groupby if c.name in names]
        order_by = [
            Tree("order_by_item", [measure.expr.children[0], value_to_token(self._asc)])
        ]
        row_number = Tree(
            "call_window",
            [
                "row_number",
                Tree("partition_by", partition_by),
                Tree("order_by", order_by),
                None,
            ],
        )
        sub.aggregate = [
            *sub.aggregate,
            ColumnCalculation(name="__top", type="int", expr=row_number),
        ]
        sub.subquery = True

        # TODO: do as said in the docstring for the main query. right now AggregateQuery
        # doesn't support a subquery as a source, which is needed for this

        for query in queries:
            alias = str(uuid4())
            expr = utils.join_exprs_with_and(
                [
                    Tree(
                        "le",
                        [
                            Tree("column", [query.table.id, alias, "__top"]),
                            value_to_token(self._n),
                        ],
                    ),
                    self.get_join_expr(query.groupby, query.table.id, alias),
                ]
            )
            join = Join(
                expr=expr,
                alias=alias,
                to=sub,
                inner=True,
            )
            query.joins.append(join)

        return queries

    def transform_queries_general(self, queries: List[AggregateQuery], measure):
        """Transform AggregateQueries in the "general" case: when there's at least one
        "of" present.  Doesn't matter if there's "within" or not.

        Subquery groups by what's in "within" and "of", and then partitions row_number
        by "within".
        """
        main = next(filter(lambda q: q.table == measure.table, queries))
        aggregate = next(filter(lambda c: c.name == measure.id, main.aggregate))
        groupby_names = set(
            QueryDimensionRequest(dimension=d).name for d in self._of + self._within
        )
        partition_names = set(
            QueryDimensionRequest(dimension=d).name for d in self._within
        )

        groupby = list(filter(lambda c: c.name in groupby_names, main.groupby))
        partition_by = list(filter(lambda c: c.name in partition_names, main.groupby))

        top = Tree(
            "call_window",
            [
                "row_number",
                Tree("partition_by", [c.expr for c in partition_by]),
                Tree(
                    "order_by",
                    [
                        Tree(
                            "order_by_item", [aggregate.expr, value_to_token(self._asc)]
                        )
                    ],
                ),
                None,
            ],
        )
        sub = AggregateQuery(
            table=measure.table,
            groupby=groupby,
            joins=self.filter_joins(main.joins),
            aggregate=[ColumnCalculation(name="__top", type="int", expr=top)],
            subquery=True,
            filters=[*main.filters],
        )

        for query in queries:
            alias = str(uuid4())
            join_expr = self.get_join_expr(
                [c for c in query.groupby if c.name in groupby_names],
                query.table.id,
                alias,
            )
            join_expr = utils.join_exprs_with_and(
                [
                    Tree(
                        "le",
                        [
                            Tree("column", [query.table.id, alias, "__top"]),
                            value_to_token(self._n),
                        ],
                    ),
                    join_expr,
                ]
            )
            join = Join(expr=join_expr, alias=alias, to=sub, inner=True)
            query.joins.append(join)

        return queries

    def transform_computation(self, computation: Computation):
        measure = self._get_measure(self._metric)

        if len(self._of) + len(self._within) == 0:
            # basic case: bare top
            computation.queries = self.transform_queries_basic(
                computation.queries, measure
            )
        elif len(self._within) > 0 and len(self._of) == 0:
            # within case: only within
            computation.queries = self.transform_queries_within(
                computation.queries, measure
            )
        else:
            # general case: of and within (can be empty)
            computation.queries = self.transform_queries_general(
                computation.queries, measure
            )

        return computation


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


class TotalTransform(TableTransform):
    """For additive expressions: adds a post-calculation.
    For non-additive expressions (e.g. with COUNTD): adds a join, a total and a post-
        calculation.
    """

    # id = "total"
    name = "Total"

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
        partition_by = None
        names = [utils.merged_expr(r.name) for r in self._of + self._within]
        if names:
            partition_by = names
        return Tree("call_window", ["sum", expr.children[0], partition_by, None, None])


class TopTransform(TableTransform):
    """Only allowed in the limit clause. Adds an inner join."""


class PercentTransform(TableTransform):
    """Like total, but divides the value by the total."""
