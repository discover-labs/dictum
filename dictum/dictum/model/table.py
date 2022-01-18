from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

from lark import Tree

from dictum.model.calculations import Dimension, TableFilter
from dictum.model.dicts import DimensionDict, MeasureDict


@dataclass
class RelatedTable:
    table: Any
    foreign_key: str
    related_key: str
    join_expr: Tree
    alias: str

    @classmethod
    def create(
        self, parent: str, table: str, foreign_key: str, related_key: str, alias: str
    ) -> "RelatedTable":
        join_expr = Tree(
            "expr",
            [
                Tree(
                    "eq",
                    [
                        Tree("column", [parent.id, foreign_key]),
                        Tree("column", [parent.id, alias, related_key]),
                    ],
                )
            ],
        )
        return RelatedTable(
            table=table,
            foreign_key=foreign_key,
            related_key=related_key,
            alias=alias,
            join_expr=join_expr,
        )


@dataclass(repr=False)
class Table:
    """Represents a relational data table"""

    id: str
    source: str
    description: Optional[str] = None
    primary_key: Optional[str] = None
    filters: List[TableFilter] = field(default_factory=list)
    related: Dict[str, RelatedTable] = field(default_factory=dict)
    measures: MeasureDict = field(default_factory=MeasureDict)
    dimensions: DimensionDict = field(default_factory=DimensionDict)
    measure_backlinks: Dict[str, "Table"] = field(
        default_factory=dict
    )  # measure_id -> table

    def find_all_paths(
        self, traversed_tables: Tuple[str] = ()
    ) -> List[Tuple["Table", List["str"]]]:
        """Find all join paths from this table to other tables, avoiding cycles"""
        traversed_tables += (self.id,)
        for rel in self.related.values():
            if isinstance(rel.table, Table) and rel.table.id not in traversed_tables:
                yield rel.table, [rel.alias]
                for target, path in rel.table.find_all_paths(traversed_tables):
                    yield target, [rel.alias, *path]

    @cached_property
    def allowed_join_paths(self) -> Dict["Table", List[str]]:
        """A dict of table id -> tuple list of related table aliases. Join targets for
        which there exists only a single join path.
        """
        paths = defaultdict(lambda: [])
        for target, path in self.find_all_paths():
            paths[target].append(path)
        result = {t: v[0] for t, v in paths.items() if len(v) == 1}
        for rel in self.related.values():
            result[rel.table] = [rel.alias]
        return result

    @cached_property
    def dimension_join_paths(self) -> Dict[str, List[str]]:
        result = {}
        for target, path in self.allowed_join_paths.items():
            for key, dim in target.dimensions.items():
                if not dim.is_union:
                    result[key] = [self.id] + path
        for dimension_id in self.dimensions:
            result[dimension_id] = [self.id]
        return result

    @cached_property
    def allowed_dimensions(self) -> Dict[str, "Dimension"]:
        """Which dimensions are allowed to be used with this table as anchor.
        Only those to which there's a single direct join path. If there isn't,
        dimensions must be declared directly on a table that's available for join.
        Unions are not allowed for joins.
        """
        result = {}
        for target in self.allowed_join_paths.keys():
            result.update(
                {d.id: d for d in target.dimensions.values() if not d.is_union}
            )
        result.update(self.dimensions)
        return result

    def __eq__(self, other: "Table"):
        return isinstance(other, Table) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"Table({self.id})"
