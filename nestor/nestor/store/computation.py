from dataclasses import dataclass, field
from typing import Dict, List

from lark import Tree

from nestor.store.table import Table


@dataclass
class Join:
    """A single join in the join tree"""

    foreign_key: str
    related_key: str  # primary key of the related table
    to: "JoinTree"

    def __eq__(self, other: "Join"):
        return (
            self.foreign_key == other.foreign_key
            and self.related_key == other.related_key
            and self.to == other.to
        )


@dataclass
class UnnestedJoin:
    """A flat join"""

    left_identity: str
    left_key: str

    right_source: str
    right_identity: str
    right_key: str


@dataclass
class JoinTree:
    """A table and an optional tree of joins. Which tables need to be joined
    to which. Keeps track of joins, so that no join is performed twice.

    Each table is supplied with an identity to be used in the select list to signify
    on which column to perform a calculation. To be used as e.g. SQL aliases or prefixes
    for pandas column names.
    """

    table: Table
    identity: str  # table identity (see the docstring)
    joins: List[Join] = field(default_factory=list)

    def add_path(self, tables: List[str]):
        """Add a single path to the existing join tree. Tables will be joined on the
        relevant foreign key.
        """
        if len(tables) == 0:
            return
        table_or_alias, *tables = tables
        related = self.table.related[table_or_alias]
        fk = related.foreign_key
        table = related.table
        identity = f"{self.identity}.{table_or_alias}"
        join = Join(
            foreign_key=fk,
            related_key=table.primary_key,
            to=JoinTree(table=table, identity=identity),
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
        """Unnested joins in the correct order."""
        for join in self.joins:
            yield UnnestedJoin(
                left_identity=self.identity,
                left_key=join.foreign_key,
                right_source=join.to.table.source,
                right_identity=join.to.identity,
                right_key=join.related_key,
            )
            yield from join.to.unnested_joins

    def _print(self):
        print("\n".join(self._paths()))

    def _paths(self) -> List[str]:
        result = []
        result.append(self.identity)
        for join in self.joins:
            result += join.to._paths()
        return result

    def __eq__(self, other: "JoinTree"):
        return self.identity == other.identity


@dataclass
class RelationalQuery:
    """Represents a fact table aggregated to a relevant (for the request) level of
    detail.
    """

    join_tree: JoinTree
    aggregate: Dict[str, Tree] = field(default_factory=lambda: {})
    groupby: Dict[str, Tree] = field(default_factory=lambda: {})
    filters: List[Tree] = field(default_factory=lambda: [])


@dataclass
class Computation:
    """What the backend gets to compile and execute."""

    queries: List[RelationalQuery]
    merge: List[str] = field(default_factory=lambda: [])
