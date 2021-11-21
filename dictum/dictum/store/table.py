from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from functools import cached_property, reduce
from typing import Dict, List, Optional, Tuple, Union

from lark import Tree

import dictum.store
from dictum.store.calculations import Dimension, Measure
from dictum.store.expr.parser import parse_expr


@dataclass
class RelatedTable:
    table: Union["Table", "dictum.store.AggregateQuery"]
    foreign_key: str
    related_key: str
    alias: str


@dataclass(repr=False)
class JoinPathItem:
    table: "Table"
    alias: str

    def __eq__(self, other):
        return self.table == other.table

    def __hash__(self):
        return hash(self.table)

    def __str__(self):
        return f"{self.alias}:{self.table}"

    def __repr__(self):
        return str(self)


JoinPath = Tuple[JoinPathItem, ...]


@dataclass
class TableFilter:
    table: "Table"
    expr: Tree

    def __post_init__(self):
        self.expr = parse_expr(self.expr)
        for ref in self.expr.find_data("column"):
            ref.children = [self.table.id, *ref.children]

    def prepare_expr(self):
        expr = deepcopy(self.expr)
        for ref in expr.find_data("column"):
            *path, field = ref.children
            ref.children = [".".join(path), field]
        return expr


@dataclass(repr=False)
class Table:
    """Represents a relational data table"""

    id: str
    source: str
    description: Optional[str]
    primary_key: str
    filters: List[TableFilter] = field(default_factory=list)
    related: Dict[str, RelatedTable] = field(default_factory=dict)
    measures: Dict[str, Measure] = field(default_factory=dict)
    dimensions: Dict[str, Dimension] = field(default_factory=dict)
    measure_backlinks: Dict[str, "Table"] = field(
        default_factory=dict
    )  # measure_id -> table

    _resolved: bool = False

    def find_all_paths(self, path: JoinPath = ()) -> List[JoinPath]:
        """Find all join paths from this table to other tables"""
        result = []
        if path:
            result.append(path)
        for alias, rel in self.related.items():
            item = JoinPathItem(rel.table, alias)
            if item in path:
                continue  # skip on cycle
            if isinstance(rel.table, Table):  # skip related subqueries
                result.extend(rel.table.find_all_paths(path + (item,)))
        return result

    @cached_property
    def allowed_join_paths(self) -> Dict[str, JoinPath]:
        """A dict of table id -> tuple of JoinPathItem. Join targets for which there
        exists only a single join path.
        """

        def _acc_paths(acc: dict, path: JoinPath):
            acc[path[-1]].append(path)
            return acc

        paths = reduce(_acc_paths, self.find_all_paths(), defaultdict(lambda: []))
        return {k.table.id: v[0] for k, v in paths.items() if len(v) == 1}

    @cached_property
    def dimension_join_paths(self) -> Dict[str, List[str]]:
        result = {}
        for path in self.allowed_join_paths.values():
            *_, target = path
            for key in target.table.dimensions:
                result[key] = [self.id] + [p.alias for p in path]
        for dimension_id in self.dimensions:
            result[dimension_id] = [self.id]
        return result

    @cached_property
    def allowed_dimensions(self) -> Dict[str, "Dimension"]:
        """Which dimensions are allowed to be used with this table as anchor.
        Only those to which there's a single direct join path. If there isn't,
        dimensions must be declared directly on a table that's available for join.
        """
        dims = {}
        dims.update(self.dimensions)
        counts = defaultdict(lambda: 0)
        for *_, target in self.allowed_join_paths.values():
            for dimension in target.table.dimensions.values():
                counts[dimension] += 1
        dims.update({d.id: d for d, paths in counts.items() if paths == 1})
        return dims

    def __eq__(self, other: "Table"):
        return isinstance(other, Table) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"Table({self.id})"
