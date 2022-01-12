from dataclasses import dataclass, field
from typing import List, Literal, Optional, Union

from lark import Tree

import dictum.model
from dictum import schema
from dictum.model import utils
from dictum.model.expr import parse_expr

"""
Computation
    the base class

RelationalQuery
    select: a list of named column expressions
    from: a table source or a generic query
    joins: a list of joins
        on: expression
        alias: str
        to: a table source or a RelationalQuery
        inner: bool
        subquery: bool
    where: a list of expressions
    group by: a list of expressions
    order by: a list of expresssions + asc/desc
    limit: a number

MergedRelationalQueries
    queries: a list of RelationalQuery
    merge_on: a list of common column names to merge the queries' results on
    columns: a list of column expressions to select from the merged result
    filters: a list of expressions
    top: a list of RelationalQuery that will return tuples to keep

Top/Bottom
    For RelationalQuery:
        - basic: no of/within, just order by + limit
        - general: of and/or within
            of, if not present, is assumed to be everything that's not within.
            add an inner join. same query, but group by of + within, top is row_number
            with partition by within. join condition is equality on columns in of and
            within plus <= top argument
    For MergedQuery:
        This assumes that there are multiple anchor tables to work with. Add a
        RelationalQuery to top, which will return tuples that should be kept. These
        should be injected into each of the child queries as a filter.

Cases:
- a simple aggregation over an anchor table with joins
    AggregateQuery: just compile and compute at once
- multiple aggregations over several anchor tables
    MergedQuery: compute in parallel, merge in Pandas
- multiple aggregations over several anchor tables with follow-up calculations
    MergedQuery: compute in parallel, merge and calculate metrics in Pandas
- a simple aggregation with an additive total
    AggregateQuery from a subquery: just compile and compute at once
- a simple aggregation with a non-additive total
    AggregateQuery with a subquery: just compile and compute at once
- a simple aggregation with top
- multiple aggregations with follow-up calculations and top
- multiple aggregations with follow-up calculations and total
"""

"""
What is the best structure for computation?
Backend
    should be as dumb as possible.
    shouldn't know anything about the model, transforms etc, just computations

What is a computation?
    Compute and join tables, compute stuff based on the joined tables, infinitely
    nested.

Is model/engine/backend architecture wrong?
    Well, if we want to make writing new backends easy, we must make them as dumb as
    possible. At the same time, there's a problem with optimization: we might produce
    suboptimal queries if we don't know what the query is about. This is a tradeoff
    between generating optimized queries and duplicating code between backend plugins.

    Sometimes we might wanna run multiple queries in parallel and then compute stuff
    in Python etc. This might be even preferrable, but doesn't work with e.g. top
    transform. Should top-k even be a transform? Maybe it's something else?

    OK, maybe a computation is this: run these queries in parallel, merge them in Pandas,
    and then compute table calculations. What about top? Top should be something like
    "run these queries, then filter the other queries with their results". So it's like
    a DAG of queries, with queries as nodes and operations (e.g. filter these on results
    of these) as directed edges. Maybe even edges between columns or groups of columns.

    Which operations might there be?
    - merge multiple queries
    - filter query on the results of a previous query e.g. compute top -> filter

    Maybe queries are edges and operations are nodes? This makes more sense, the data
    just passes though operators. So, something like a QueryFilter operator requires
    N input queries to use as filters and M queries to filter.
    Operators:
    - CompileQueryOperator — turns a RelationalQuery into something else that the backend
        understands. This is an analog to current Compiler class.
    - FilterWithQueryOperator (for top/bottom) — takes in a number of queries that will
        be used as filters and another number of queries that will be output. Decides
        whether to inject the filtering queries as an inner join (maybe if there's a
        single output query) or to materialize them and use as filters.
    - MergeQueriesOperator (for merging queries together e.g. full outer join). Decides
        whether to materialize (or maybe they are already materialized).
    - MaterializeOperator (for returning results)
    - TypeCastOperator
    - CalculateOperator (for calculating metrics) — a single input relation and a number
        of output columns to calculate. Wrap in subquery and calculate if a Select,
        calculate directly if a DataFrame.

    Then what is common between backends and hence can be decided at the level of
    the Engine? And what absolutely must be implemented at the level of the backend?
    - Query compilation and execution absolutely must be backend-specific.
    - Deciding whether to inject a filtering query or to materialize and filter — this
        should be decided by the engine. So, there are really two operators:
        - InnerJoinOperator adds an inner join
        - FilterWithTableOperator adds a filter from a number of tuples

    Then Computation becomes a graph structure. It has a set of Operator instances which
    each in turn have upstreams and downstreams. Hmmm, doesn't this look like streamz?
    It kind of does, but each node only executes once, there's not stream in there.

    How does a backend execute a computation? Maybe Computation is a callable that
    requires a backend and calls it's methods? Then it's something like this:
        class Project:
            ...
            def execute(self, query: schema.Query) -> pd.DataFrame:
                resolved: model.ResolvedQuery = self.model.get_resolved_query(query)
                computation: engine.Computation = self.engine.get_computation(resolved)
                return computation.execute(self.backend)

    How do table transforms work in this case?
    - Transforms can be operators themselves.
        Multiple tops should be run in parallel, probably should be separate operators.
    - Transforms can operate on the graph.
        This is probably better, but need to figure the exact interface.

    Are merge and calculate the same thing? Probably yes, in the end any of them can be
    a no-op.

    So TableTransforms probably operate on the MergeCalculate operator.
    - TOP: take the incoming queries, replace with FilterTuples + the needed tops
    - TOTAL: if additive, just add a column to Finalize. if not, add another query.
        if any of the queries are FilterTuples, copy and replace query with self.

    TOP vs TOTAL: totals queries are added to Finalize first, then all of the Finalize
        queries get filtered with TOP.
    GT vs TOTAL:

    Totals must be aware of existing limits, so limits are applied first, then table
    calcs.
    Table calcs are applied to the terminal Finalize. Finalize is always a terminal.
    Finalize should be able to handle both Query and DataFrame inputs.

    How is the graph constructed?
    - Build RelationalQueries, same as now. Scalar transforms are applied here too.
    - Add Finalize
    - Apply limits to the Finalize in query order.
    - Apply metric transforms to the Finalize in query order.

    CONVENTION: DataFrames always have dimensions as named (Multi)Index.

Join
    to: Table | Computation <-- subquery
    alias: str <-- identity
    type: left | inner | full
    expr: Tree
    jointree: List[Join]
    joins: @property like unnested_joins

Computation
    from: Table | Computation <-- subquery
    jointree: List[Join]
    joins: @property like unnested_joins

Why is a universal RelationalQuery bad?
- It doesn't always make sense to include everything in a single query — sometimes we
    might wanna compute stuff in parallel

Some kind of computational graph like in dask?
- Doesn't take advantage of SQL database optimizers.
"""


@dataclass
class Column:
    name: str
    expr: Tree
    type: schema.Type

    @property
    def join_paths(self) -> List[str]:
        result = []
        for ref in self.expr.find_data("column"):
            path = ref.children[1:-1]
            if path:
                result.append(path)
        return result


@dataclass
class Relation:
    source: Union["dictum.model.Table", "RelationalQuery"]
    joins: List["Join"]

    def add_join_path(self, path: List[str]):
        """Add a single path to the existing join tree. Tables will be joined on the
        relevant foreign key. Path starts with the first related table alias.
        """
        if isinstance(self.source, RelationalQuery):
            raise TypeError(
                "Can't add a join path to a Relation that has a subquery as a source"
            )

        if len(path) == 0:
            return

        alias, *path = path

        # the join path requests a subquery metric join
        # in case of an aggregate dimension
        # inject the necessary subquery and terminate
        if alias.startswith("__subquery__"):
            measure_id = alias.replace("__subquery__", "")
            table = self.source.measure_backlinks.get(measure_id)

            # aggregate table by self.source.primary_key
            measure = table.measures.get(measure_id)
            measure_column = Column(
                name=measure_id, expr=measure.expr, type=measure.type
            )
            subquery = RelationalQuery(
                source=table, joins=[], _aggregate=[measure_column]
            )
            for join_path in measure_column.join_paths:
                subquery.add_join_path(join_path)
            join_path = table.allowed_join_paths[self.source]
            subquery.add_join_path(join_path)
            pk = Column(
                name="__pk",
                type=None,
                expr=Tree(
                    "expr",
                    [Tree("column", [table.id, *join_path, self.source.primary_key])],
                ),
            )
            subquery.add_groupby(pk)
            join = Join(
                source=subquery,
                joins=[],
                alias=alias,
                expr=parse_expr(
                    f"{self.source.id}.{alias}.__pk = {self.source.id}.{self.source.primary_key}"
                ),
            )
            self.joins.append(join)
            return

        related = self.source.related[alias]
        join = Join(
            expr=related.join_expr,
            source=related.table,
            alias=alias,
            joins=[],
        )

        for existing_join in self.joins:
            if join == existing_join:  # if this join already exists, go down a level
                existing_join.add_join_path(path)
                return  # and terminate

        # if this join doesn't exist
        self.joins.append(join)
        join.add_join_path(path)  # add and go further down

    @property
    def unnested_joins(self) -> List["UnnestedJoin"]:
        return list(self._unnested_joins())

    def _unnested_joins(self, path=()):
        if path == ():
            path = (self.source.id,)
        for join in self.joins:
            prefix = (*path, join.alias)
            yield UnnestedJoin(
                expr=utils.prepare_expr(join.expr, path),
                right_identity=".".join(prefix),
                right=join.source,
                inner=join.inner,
            )
            if not isinstance(join.source, RelationalQuery):
                yield from join._unnested_joins(path + (join.alias,))


@dataclass
class Join(Relation):
    alias: str
    expr: Tree
    inner: bool = False

    def prepare(self):
        if isinstance(self.source, RelationalQuery):
            self.source.prepare()
        for join in self.joins:
            join.prepare()

    def __eq__(self, other: "Join"):
        return (
            isinstance(other, Join)
            and self.expr == other.expr
            and self.alias == other.alias
            and self.source == other.source
        )


@dataclass
class UnnestedJoin:
    expr: Tree
    right_identity: str
    right: Union["dictum.model.Table", "RelationalQuery"]
    inner: bool


@dataclass
class OrderItem:
    expr: Tree
    ascending: bool


@dataclass
class RelationalQuery(Relation):
    """
    A simple relational query.

    Arguments:
        _aggregate: A list of aggregate columns.
        _groupby: A list of non-aggregate columns to group by.
        filters: A list of boolean-valued expressions.
        order: A list of OrderItem, each one of which is an expression and a boolean
            telling if the order is ascending or descending.
        limit: An integer limit.
    """

    _aggregate: List[Column] = field(default_factory=list)
    _groupby: List[Column] = field(default_factory=list)
    filters: List[Tree] = field(default_factory=list)
    order: List[OrderItem] = field(default_factory=list)
    limit: Optional[int] = None

    def add_groupby(self, column: Column):
        self._groupby.append(column)

    def add_aggregate(self, column: Column):
        self._aggregate.append(column)

    @property
    def groupby(self) -> List[Tree]:
        return [c.expr for c in self._groupby]

    @property
    def columns(self) -> List[Column]:
        return [*self._groupby, *self._aggregate]

    @staticmethod
    def prepare_expr(expr: Tree) -> Tree:
        for ref in expr.find_data("column"):
            *path, id_ = ref.children
            ref.children = [".".join(path), id_]
        return expr

    def prepare(self):
        for column in self._aggregate + self._groupby:
            self.prepare_expr(column.expr)
        self.filters = list(map(self.prepare_expr, self.filters))
        for item in self.order:
            self.prepare_expr(item.expr)
        for join in self.joins:
            join.prepare()


@dataclass
class Computation:
    """
    Parameters:
        queries: A list of RelationalQuery.
        computations: A list of Computations.
        merge_on: A list of column names to merge on. The results of both queries and
            computations should be merged.
        columns: After merging, finalize the computation by computing these columns
            on the result of merging.
        top: A list of computations the results of which will further limit the result set.
        filters: A list of boolean expressions to filter the result set on.
        order, limit: as in RelationalQuery
    """

    queries: List[RelationalQuery] = field(default_factory=list)
    computations: List["Computation"] = field(default_factory=list)
    merge_on: List[str] = field(default_factory=list)
    columns: List[Column] = field(default_factory=list)
    top: List["Computation"] = field(default_factory=list)
    filters: List[Tree] = field(default_factory=list)
    order: List[OrderItem] = field(default_factory=list)
    limit: Optional[int] = None

    def prepare(self):
        for query in self.queries:
            query.prepare()

    @property
    def types(self) -> dict:
        result = {}
        for column in self.columns:
            result[column.name] = column.type
        return result


@dataclass
class SuperJoin:
    to: Union["Super", "dictum.model.Table"]
    expr: Tree
    type: Literal["inner", "left", "full"]
    alias: str
    joins: List["SuperJoin"]


@dataclass
class Super:
    select: List[Column] = field(default_factory=list)
    groupby: List[Column] = field(default_factory=list)
