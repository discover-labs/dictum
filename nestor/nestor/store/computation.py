from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from lark import Tree

from nestor.store.table import Table


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
class AggregateQuery:
    """A table and an optional tree of joins. Which tables need to be joined
    to which. Keeps track of joins, so that no join is performed twice.

    Each table is supplied with an identity to be used in the select list to signify
    on which column to perform a calculation. To be used as e.g. SQL aliases or prefixes
    for pandas column names.
    """

    table: Table
    aggregate: Dict[str, Tree] = field(default_factory=dict)
    groupby: Dict[str, Tree] = field(default_factory=dict)
    filters: List[Tree] = field(default_factory=list)
    joins: List[Join] = field(default_factory=list)
    subquery: bool = False

    def add_measure(self, measure_id: str):
        measure = self.table.measures.get(measure_id)
        self.aggregate[measure_id] = self.prefix_columns([self.table.id], measure.expr)
        self.joins.extend(measure.joins)

    def join_dimension(
        self, dimension_id: str, _path: Tuple[str, ...] = ()
    ) -> Tuple["AggregateQuery", Tuple[str, ...]]:
        """Add the necessary joins for a dimension.
        Returns innermost RelationalQuery.
        """
        # termination: dimension is right here
        if dimension_id in self.table.dimensions:
            dimension = self.table.dimensions.get(dimension_id)
            self.joins.extend(dimension.joins)
            return self, _path  # terminate

        path = self.table.dimension_join_paths.get(dimension_id)
        if path is None:
            raise KeyError(
                f"Can't find a path from {self.table} to dimension {dimension_id}"
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

    @staticmethod
    def prefix_columns(prefix: List[str], expr: Tree):
        result = deepcopy(expr)
        for ref in result.find_data("column"):
            *tables, field = ref.children
            ref.children = [".".join([*prefix, *tables]), field]
        return result

    def add_dimension(
        self, dimension_id: str, transform: Optional[Callable[[Any], Tree]] = None
    ):
        query, path = self.join_dimension(dimension_id)
        dimension = query.table.dimensions.get(dimension_id)
        expr = self.prefix_columns(
            (self.table.id, *path),
            dimension.expr,
        )
        if transform is not None:
            expr = transform(expr)
        self.groupby[dimension_id] = expr

    def add_filter(self, dimension_id: str, filter: Callable[[Any], Tree]):
        query, path = self.join_dimension(dimension_id)
        dimension = query.table.dimensions.get(dimension_id)
        expr = self.prefix_columns((self.table.id, *path), dimension.expr)
        expr = filter(expr)
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
        print("\n".join(self._paths()))

    def _paths(self) -> List[str]:
        result = []
        result.append(self.identity)
        for join in self.joins:
            result += join.to._paths()
        return result

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

    types: Dict[str, str]
    queries: List[AggregateQuery]
    metrics: Dict[str, Tree]
    merge: List[str] = field(default_factory=list)
