from copy import copy, deepcopy
from typing import List, Optional
from uuid import uuid4

from lark import Tree

from dictum import engine, model
from dictum.model import utils
from dictum.model.calculations import Metric
from dictum.model.expr import get_expr_total_function
from dictum.model.transforms.base import BaseTransform
from dictum.utils import value_to_token

transforms = {
    "top": None,  # for attribute checks
    "bottom": None,
}


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
        query: "model.ResolvedQuery",
        of: Optional[List["model.ResolvedQueryDimensionRequest"]] = None,
        within: Optional[List["model.ResolvedQueryDimensionRequest"]] = None,
    ):
        self.query = query
        self.of = of or []
        self.within = within or []
        super().__init__(*args)

    def __init_subclass__(cls):
        if hasattr(cls, "id"):
            transforms[cls.id] = cls

    def transform_computation(self, computation: "engine.Computation"):
        """Do nothing to the computation by default."""
        return computation

    def __call__(self, base: "engine.Computation", computation: "engine.Computation"):
        """
        Arguments:
            base: A compiled computation corresponding to the metric + of + within from
                the request.
            computation: A computation that's supposed to be transformed.
        """
        raise NotImplementedError


# class TopBottomTransform(TableTransform):
#     """
#     revenue.top(10) of (city) within (country)

#     Only allowed inside limit. Adds an inner join to each AggregateQuery. Doesn't have
#     an ID, because isn't taken from the standard table_transforms dict. Requires access
#     to the underlying metric and the parent model, because has to construct an
#     AggregateQuery.

#     - no of and no within
#         - same anchor: order by + limit
#         - different anchor: inner join, order by + limit
#     - only within
#         - same anchor: add a row number column, wrap in subquery with WHERE <= N
#         - different anchor: inner join, row number with partition by within
#     - both of and within
#         - same anchor: inner join GROUP BY of and within, row number with partition by
#           WITHIN, join ON <= N in condition
#         - different anchor: same
#     """

#     _asc: bool

#     def __init__(
#         self,
#         n: int,
#         query: "model.ResolvedQuery",
#         of: Optional[List] = None,
#         within: Optional[List] = None,
#     ):
#         self.n = n
#         super().__init__(query=query, of=of, within=within)

#     def transform_expr(self, expr: Tree) -> Tree:
#         """All the logic is in transform_computation"""
#         return expr

#     def _get_measure(self, metric):
#         """Extract a measure from the metric, additionally checking that the metric is
#         valid for this transform.
#         """
#         if not metric.is_measure:
#             raise ValueError(
#                 "Top transform can only be applied to metrics that were "
#                 "defined as measures"
#             )
#         return metric.measures[0]

#     def get_join_expr(
#         self, columns: List["engine.Column"], table_id: str, alias: str
#     ) -> Tree:
#         cols = {c.name: c.expr for c in columns}
#         conditions = []
#         for name, expr in cols.items():
#             conditions.append(
#                 Tree("eq", [deepcopy(expr), Tree("column", [table_id, alias, name])])
#             )
#         return Tree("expr", [utils.join_exprs_with_and(conditions)])

#     def filter_joins(self, joins: List["engine.Join"]):
#         """To avoid duplicating joins when there are multiple top/bottom transforms
#         applied, skip existing top joins.
#         """
#         result = []
#         for join in joins:
#             if isinstance(join.source, engine.RelationalQuery):
#                 names = set(c.name for c in join.source.columns)
#                 if not (join.inner and "__top" in names):
#                     result.append(join)
#             else:
#                 result.append(join)
#         return result

#     def transform_queries_basic(self, queries: List["engine.RelationalQuery"], measure):
#         """Transform RelationalQueries in a "basic" case: when there are no "of" or
#         "within" specified:
#             - for the same anchor table: just order and limit
#             - for another anchor table: inner join that same query
#         """
#         main = next(filter(lambda q: q.source == measure.table, queries))
#         main.limit = self._n
#         main.order = [engine.OrderItem(expr=measure.expr, ascending=self._asc)]

#         # a shallow copy, because we only change a bool (subquery)
#         sub = copy(main)
#         sub.joins = self.filter_joins(main.joins)
#         sub.subquery = True

#         secondary = []
#         for query in filter(lambda q: q.source != measure.table, queries):
#             alias = str(uuid4())
#             join = engine.Join(
#                 source=sub,
#                 alias=alias,
#                 inner=True,
#                 expr=self.get_join_expr(query._groupby, query.source.id, alias),
#                 joins=[],
#             )
#             query.joins.append(join)
#             secondary.append(query)
#         return [main, *secondary]

#     def transform_queries_general(
#         self, queries: List["engine.RelationalQuery"], measure
#     ):
#         """Transform AggregateQueries in a "general" case: where there's at least one
#         "of" or "within" specified, missing "of" assumed to be all dimension that are
#         not "within"
#             - for the same anchor table: wrap in a subquery
#               TODO: actually implement it like this
#             - for others: join on all dimension columns and __top <= N
#         """
#         main = next(filter(lambda q: q.source == measure.table, queries))

#         sub = copy(main)
#         sub = engine.RelationalQuery(
#             source=main.source, joins=self.filter_joins(main.joins)
#         )

#         names_within = set(r.name for r in self._within)
#         # of, if not specified, is assumed to be everything that's not within
#         names_of = set(r.name for r in self._of)
#         if len(names_of) == 0:
#             names_of = set(c.name for c in main._groupby) - names_within

#         # group by of + within
#         names = names_of | names_within
#         for column in main._groupby:
#             if column.name in names:
#                 sub.add_groupby(column)

#         # partition by within, order by calculation
#         partition_by = [c.expr for c in sub.columns if c.name in names_within]
#         order_by = [
#             Tree("order_by_item", [measure.expr.children[0], value_to_token(self._asc)])
#         ]
#         row_number = Tree(
#             "call_window",
#             [
#                 "row_number",
#                 Tree("partition_by", partition_by),
#                 Tree("order_by", order_by),
#                 None,
#             ],
#         )
#         sub.add_aggregate(engine.Column(name="__top", type="int", expr=row_number))

#         # TODO: do as said in the docstring for the main query. right now AggregateQuery
#         # doesn't support a subquery as a source, which is needed for this

#         for query in queries:
#             alias = str(uuid4())
#             groupby = [c for c in query._groupby if c.name in names]
#             expr = utils.join_exprs_with_and(
#                 [
#                     Tree(
#                         "le",
#                         [
#                             Tree("column", [query.source.id, alias, "__top"]),
#                             value_to_token(self._n),
#                         ],
#                     ),
#                     self.get_join_expr(groupby, query.source.id, alias),
#                 ]
#             )
#             join = engine.Join(expr=expr, alias=alias, source=sub, inner=True, joins=[])
#             query.joins.append(join)

#         return queries

#     def transform_computation(self, computation: "engine.Computation"):
#         measure = self._get_measure(self._metric)

#         if len(self._of) + len(self._within) == 0:
#             # basic case: bare top
#             computation.queries = self.transform_queries_basic(
#                 computation.queries, measure
#             )
#         else:
#             # general case: of and/or within
#             computation.queries = self.transform_queries_general(
#                 computation.queries, measure
#             )

#         return computation


class TopBottomTransform(TableTransform):
    def __init__(
        self,
        n: int,
        query: "model.ResolvedQuery",
        of: Optional[List["model.ResolvedQueryDimensionRequest"]] = None,
        within: Optional[List["model.ResolvedQueryDimensionRequest"]] = None,
    ):
        self.n = n
        super().__init__(n, query=query, of=of, within=within)

    @staticmethod
    def row_number(expr: Tree):
        return Tree("call_window", ["row_number", ])

    def __call__(self, base: "engine.Computation", computation: "engine.Computation"):
        breakpoint()
        return super().__call__(base, computation)


class TopTransform(TopBottomTransform):
    id = "top"
    name = "Top"
    _asc = False


class BottomTransform(TopBottomTransform):
    id = "bottom"
    name = "Bottom"
    _asc = True


class TotalTransform(TableTransform):
    """Calculate a total value on a given level of detail.

    Uses get_expr_total_function. If a function can be defined for an expression,
    compute with a window function. If not, do a subquery join to calculate the total.
    """

    id = "total"
    name = "Total"

    def transform_expr(self, expr: Tree) -> Tree:
        fn = get_expr_total_function(expr)
        if fn is not None:  # apply window function
            partition_by = None
            columns = [utils.merged_expr(r.name) for r in self._of + self._within]
            if columns:
                partition_by = Tree("partition_by", columns)
            fn = f"window_{fn}"
            return Tree("call_window", [fn, expr.children[0], partition_by, None, None])

        # no known window function, the result will be calculated with as subquery
        return super().transform_expr(expr)

    def transform_computation(self, computation: "engine.Computation"):
        return super().transform_computation(computation)


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
