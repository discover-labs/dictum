from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple, Union

from lark import Tree

from dictum.data_model.table import Table


@dataclass
class Join:
    """A single join in the join tree"""

    foreign_key: str
    related_key: str
    alias: str
    to: "AggregateQuery"

    def __eq__(self, other: "Join"):
        return (
            self.foreign_key == other.foreign_key
            and self.related_key == other.related_key
            and self.alias == other.alias
            and self.to == other.to
        )


@dataclass
class UnnestedJoin:
    """A flat join"""

    left_identity: str
    left_key: str

    right: Union[str, "AggregateQuery"]
    right_identity: str
    right_key: str


@dataclass
class Column:
    name: str
    type: str


@dataclass
class ColumnCalculation(Column):
    expr: Tree

    def apply_transform(self, transform) -> "ColumnCalculation":
        """A transform is a callable that gets a callable and returns a callable.
        It can change the name, type and expr.
        """


@dataclass
class AggregateQuery:
    """A table and an optional tree of joins. Which tables need to be joined
    to which. Keeps track of joins, so that no join is performed twice.

    Each table is supplied with an identity to be used in the select list to signify
    on which column to perform a calculation. To be used as e.g. SQL aliases or prefixes
    for pandas column names.
    """

    table: Table
    aggregate: List[ColumnCalculation] = field(default_factory=list)
    groupby: List[ColumnCalculation] = field(default_factory=list)
    filters: List[Tree] = field(default_factory=list)
    joins: List[Join] = field(default_factory=list)
    subquery: bool = False

    @staticmethod
    def prefix_columns(prefix: List[str], expr: Tree):
        result = deepcopy(expr)
        for ref in result.find_data("column"):
            *tables, field = ref.children
            ref.children = [".".join([*prefix, *tables]), field]
        return result

    def add_measure(self, measure_id: str):
        measure = self.table.measures.get(measure_id)
        column = ColumnCalculation(
            expr=measure.prepare_expr([self.table.id]),
            name=measure.id,
            type=measure.type,
        )
        for join in measure.joins:
            if join not in self.joins:
                self.joins.append(join)
        self.aggregate.append(column)

    def join_dimension(
        self, dimension_id: str, _path: Tuple[str, ...] = ()
    ) -> Tuple["AggregateQuery", Tuple[str, ...]]:
        """Add the necessary joins for a dimension.
        Returns innermost AggregateQuery.
        """
        # termination: dimension is right here
        if dimension_id in self.table.dimensions:
            dimension = self.table.dimensions.get(dimension_id)
            self.merge_joins(dimension.joins)
            return self, _path  # terminate

        path = self.table.dimension_join_paths.get(dimension_id)
        if path is None:
            names = ", ".join(a.name for a in self.aggregate)
            raise KeyError(
                f"Dimension {dimension_id} is unrelated to {self.table} and "
                f"the requested aggregations: {names}"
            )
        _, *path = path  # first item in path is self.table.id

        for existing_join in self.joins:
            if existing_join.alias == path[0]:
                # add to the existing join and terminate
                return existing_join.to.join_dimension(
                    dimension_id, (*_path, existing_join.alias)
                )

        # no existing join: add it and join the dimension to the target
        alias = path[0]
        related = self.table.related[alias]
        join = Join(
            foreign_key=related.foreign_key,
            related_key=related.table.primary_key,
            alias=alias,
            to=AggregateQuery(table=related.table),
        )
        self.joins.append(join)
        return join.to.join_dimension(dimension_id, (*_path, alias))

    def add_dimension(
        self,
        dimension_id: str,
        name: str,
        transforms: Callable[[ColumnCalculation], ColumnCalculation],
    ):
        query, path = self.join_dimension(dimension_id)
        dimension = query.table.dimensions.get(dimension_id)
        expr = dimension.prepare_expr([self.table.id, *path])
        column = transforms(
            ColumnCalculation(expr=expr, name=name, type=dimension.type)
        )
        self.groupby.append(column)

    def add_filter(
        self,
        dimension_id: str,
        filter: Callable[[ColumnCalculation], ColumnCalculation],
    ):
        query, path = self.join_dimension(dimension_id)
        dimension = query.table.dimensions.get(dimension_id)
        expr = dimension.prepare_expr([self.table.id, *path])
        column = filter(ColumnCalculation(name=None, type=dimension.type, expr=expr))
        if column.type != "bool":
            raise TypeError(
                f"Filter expression must be of type 'bool', got {column.type}"
            )
        self.filters.append(column.expr)

    def add_literal_filter(self, expr: Tree):
        expr = deepcopy(expr)
        for ref in expr.find_data("column"):
            anchor, *path, field = ref.children
            self.add_path(path)
            ref.children = [".".join([anchor, *path]), field]
        self.filters.append(expr)

    def add_path(self, tables: List[str]):
        """Add a single path to the existing join tree. Tables will be joined on the
        relevant foreign key. Path starts with the first related table alias.
        """
        if len(tables) == 0:
            return
        table_or_alias, *tables = tables
        related = self.table.related[table_or_alias]
        to = (
            related.table
            if isinstance(related.table, AggregateQuery)
            else AggregateQuery(table=related.table)
        )
        join = Join(
            foreign_key=related.foreign_key,
            related_key=related.related_key,
            to=to,
            alias=table_or_alias,
        )
        for existing_join in self.joins:
            if join == existing_join:  # if this join already exists, go down a level
                existing_join.to.add_path(tables)
                return  # and terminate
        # if this join doesn't exist
        self.joins.append(join)
        join.to.add_path(tables)  # add and go further down

    def merge_joins(self, joins: List[Join]):
        """Merge a list of joins into the existing joins, avoiding duplication."""
        for join in joins:
            if join not in self.joins:
                self.joins.append(join)
                continue
            for existing_join in self.joins:
                if join == existing_join:
                    existing_join.to.merge_joins(join.to.joins)

    @property
    def unnested_joins(self):
        """Unnested joins in the correct order, depth-first"""
        return list(self._unnested_joins())

    def _unnested_joins(self, path=()):
        if len(path) == 0:
            path = (self.table.id,)
        for join in self.joins:
            prefix = [*path, join.alias]
            yield UnnestedJoin(
                left_identity=".".join(path),
                left_key=join.foreign_key,
                right=join.to,
                right_identity=".".join(prefix),
                right_key=join.related_key,
            )
            if not join.to.subquery:
                yield from join.to._unnested_joins((*path, join.alias))

    def _print(self):
        for join in self.unnested_joins:
            print(join.left_identity, join.right_identity)

    def __eq__(self, other: "AggregateQuery"):
        return (
            isinstance(other, AggregateQuery)
            and self.table.id == other.table.id
            and self.groupby == other.groupby
            and self.aggregate == other.aggregate
            and self.subquery == other.subquery
        )


@dataclass
class Computation:
    """What the backend gets to compile and execute."""

    queries: List[AggregateQuery]
    metrics: List[ColumnCalculation]
    dimensions: List[ColumnCalculation] = field(default_factory=list)

    @property
    def types(self) -> Dict[str, str]:
        result = {}
        for metric in self.metrics:
            result[metric.name] = metric.type
        for dimension in self.dimensions:
            result[dimension.name] = dimension.type
        return result
