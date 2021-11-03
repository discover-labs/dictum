from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property, reduce
from typing import Dict, List, Optional, Tuple, Union

from lark import Transformer, Tree

import nestor.store
from nestor.store.calculations import Dimension, Measure


class ResolverError(Exception):
    pass


class ReferenceResolutionError(ResolverError):
    pass


class ReferenceNotFoundError(ReferenceResolutionError):
    pass


class InvalidReferenceTypeError(ReferenceResolutionError):
    pass


class CircularReferenceError(ReferenceResolutionError):
    pass


class CalculationResolver(Transformer):
    """Given a Dict[str, Tree] of dependencies in the constructor and an expression
    in .resolve() method, recursively replaces each reference to a different expression
    with the actual expression. In the end, only references to columns should be left
    in the expression.
    """

    def __init__(self, dependencies: Dict[str, Tree], visit_tokens: bool = True):
        self._deps = dependencies
        super().__init__(visit_tokens=visit_tokens)

    def _check_circular_refs(self, expr: Tree, path=()):
        measures = expr.find_data("measure")
        dimensions = expr.find_data("dimension")
        for ref in list(measures) + list(dimensions):
            key = ref.children[0]
            if key in path:
                path_str = " -> ".join(path + (key,))
                raise CircularReferenceError(
                    f"circular reference in calculation: {path_str}"
                )
            dep = self._deps.get(key)
            if dep is None and key not in self._ignore:
                raise ReferenceNotFoundError(
                    f"'{key}' not found in dependencies. "
                    f"Valid values: {set(self._deps)}"
                )
            if dep is not None:
                self._check_circular_refs(dep, path=path + (key,))

    def resolve(self, expr: Tree):
        self._check_circular_refs(expr)
        return self.transform(expr)

    def _transform(data: str):
        def transform(self, children):
            (key,) = children
            dep = self._deps.get(key)
            if dep is None and key not in self._ignore:
                raise ReferenceNotFoundError(
                    f"'{key}' not found in dependencies. "
                    f"Valid values: {set(self._deps)}"
                )
            return self.resolve(dep).children[0]

        return transform

    measure = _transform("measure")
    dimension = _transform("dimension")


class MeasureResolver(CalculationResolver):
    pass


class DimensionResolver(CalculationResolver):
    def _check_circular_refs(self, expr: Tree, path=()):
        for ref in expr.find_data("dimension"):
            key = ref.children[0]
            if key in path:
                path_str = " -> ".join(path + (key,))
                raise CircularReferenceError(
                    f"circular reference in calculation: {path_str}"
                )
            dep = self._deps.get(key)
            if dep is None and key not in self._ignore:
                raise ReferenceNotFoundError(
                    f"'{key}' not found in dependencies. "
                    f"Valid values: {set(self._deps)}"
                )
            if dep is not None:
                self._check_circular_refs(dep, path=path + (key,))

    def measure(self, children):
        """There will be a related table with subquery as a target, named after the
        measure, e.g. if the measure is $revenue, we need a revenue.revenue column.
        """
        field = children[0]
        return Tree("column", [f"__subquery__{field}", field])


@dataclass
class RelatedTable:
    table: Union["Table", "nestor.store.AggregateQuery"]
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


@dataclass(repr=False)
class Table:
    """Represents a relational data table"""

    id: str
    source: str
    description: Optional[str]
    primary_key: str
    related: Dict[str, RelatedTable] = field(default_factory=dict)
    measures: Dict[str, Measure] = field(default_factory=dict)
    dimensions: Dict[str, Dimension] = field(default_factory=dict)
    measure_backlinks: Dict[str, "Table"] = field(
        default_factory=dict
    )  # measure_id -> table

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

    def resolve_measures(self):
        exprs = {m.id: m.expr for m in self.measures.values()}
        for dimension in self.allowed_dimensions.values():
            if dimension.id not in self.dimensions:
                dimension.table.resolve_dimensions()
            exprs[dimension.id] = dimension.prefixed_expr(
                self.dimension_join_paths[dimension.id][1:]
            )
        resolver = MeasureResolver(exprs)
        for measure in self.measures.values():
            try:
                measure.expr = resolver.resolve(measure.expr)
            except ResolverError as e:
                raise e.__class__(f"Error processing {measure}: {e}")

    def resolve_dimensions(self):
        exprs = {d.id: d.expr for d in self.dimensions.values()}
        for dimension in self.allowed_dimensions.values():
            if dimension.id not in exprs:
                # related dimensions must be resolved first
                dimension.table.resolve_dimensions()
                exprs[dimension.id] = dimension.prefixed_expr(
                    self.dimension_join_paths[dimension.id][1:]
                )
        resolver = DimensionResolver(exprs)
        for dimension in self.dimensions.values():
            try:
                dimension.expr = resolver.resolve(dimension.expr)
            except ResolverError as e:
                raise e.__class__(f"Error processing {dimension}: {e}")

    def resolve_calculations(self):
        self.resolve_measures()
        self.resolve_dimensions()

    def __eq__(self, other: "Table"):
        return isinstance(other, Table) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"Table({self.id})"
