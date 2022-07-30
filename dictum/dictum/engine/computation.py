from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional, Union

from lark import Tree

import dictum.model
from dictum import schema
from dictum.engine.result import DisplayInfo
from dictum.model import utils
from dictum.model.expr import parse_expr


@dataclass
class Column:
    """Represents a column selected from a relational calculation result.

    Arguments:
        name — column name in the resulting query
        expr — Lark expression for the column
        type — column data type
        display_info — info for displaying the column in the formatted table
            or an Altair chart
    """

    name: str
    expr: Tree
    type: schema.Type
    display_info: Optional[DisplayInfo] = None

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
    join_tree: List["Join"]

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
                name=measure_id,
                expr=measure.expr,
                type=measure.type,
            )
            subquery = RelationalQuery(
                source=table, join_tree=[], _aggregate=[measure_column]
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
                join_tree=[],
                alias=alias,
                expr=parse_expr(
                    f"{self.source.id}.{alias}.__pk = "
                    f"{self.source.id}.{self.source.primary_key}"
                ),
            )
            self.join_tree.append(join)
            return

        related = self.source.related[alias]
        join = Join(
            expr=related.join_expr,
            source=related.table,
            alias=alias,
            join_tree=[],
        )

        for existing_join in self.join_tree:
            if join == existing_join:  # if this join already exists, go down a level
                existing_join.add_join_path(path)
                return  # and terminate

        # if this join doesn't exist
        self.join_tree.append(join)
        join.add_join_path(path)  # add and go further down

    @property
    def joins(self) -> List["UnnestedJoin"]:
        return list(self._unnested_joins())

    def _unnested_joins(self, path=()):
        if path == ():
            path = (self.source.id,)
        for join in self.join_tree:
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
        for join in self.join_tree:
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
class LiteralOrderItem:
    """Like OrderItem, but by name"""

    name: str
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
        for path in column.join_paths:
            self.add_join_path(path)
        self._groupby.append(column)

    def add_aggregate(self, column: Column):
        for path in column.join_paths:
            self.add_join_path(path)
        self._aggregate.append(column)

    def add_filter_expr(self, expr: Tree):
        expr = deepcopy(expr)
        for ref in expr.find_data("column"):
            _, *path, _ = ref.children
            self.add_join_path(path)
        self.filters.append(expr)

    @property
    def groupby(self) -> List[Tree]:
        return [c.expr for c in self._groupby]

    @property
    def columns(self) -> List[Column]:
        return [*self._groupby, *self._aggregate]

    @staticmethod
    def prepare_expr(expr: Tree) -> Tree:
        expr = deepcopy(expr)
        for ref in expr.find_data("column"):
            *path, id_ = ref.children
            ref.children = [".".join(path), id_]
        return expr

    def prepare(self):
        for column in self._aggregate + self._groupby:
            column.expr = self.prepare_expr(column.expr)
        self.filters = list(map(self.prepare_expr, self.filters))
        for item in self.order:
            item.expr = self.prepare_expr(item.expr)
        for join in self.join_tree:
            join.prepare()
