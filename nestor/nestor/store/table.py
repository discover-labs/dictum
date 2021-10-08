from collections import defaultdict
from dataclasses import dataclass, field
from functools import cache, cached_property, reduce
from typing import Dict, List, Optional, Tuple

from lark import Transformer, Tree

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

    def __init__(
        self,
        dependencies: Dict[str, Tree],
        visit_tokens: bool = True,
    ):
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
            if dep is None:
                raise ReferenceNotFoundError(
                    f"'{key}' not found in dependencies.  "
                    f"Valid values: {set(self._deps)}"
                )
            self._check_circular_refs(dep, path=path + (key,))

    def resolve(self, expr: Tree):
        self._check_circular_refs(expr)
        return self.transform(expr)

    def _transform(self, children):
        (ref,) = children
        dep = self._deps[ref]
        return self.resolve(dep).children[0]

    measure = _transform
    dimension = _transform


class MeasureResolver(CalculationResolver):
    def dimension(self, children):
        (ref,) = children
        raise InvalidReferenceTypeError(
            f"measure references '{ref}', which is a dimension. "
            "Only calculations of the same type can reference each other."
        )


class DimensionResolver(CalculationResolver):
    def measure(self, children):
        (ref,) = children
        raise InvalidReferenceTypeError(
            f"dimension references '{ref}', which is a measure. "
            "Only calculations of the same type can reference each other."
        )


class FilterResolver(CalculationResolver):
    def measure(self, children):
        (ref,) = children
        raise InvalidReferenceTypeError(
            f"A filter references '{ref}', which is a measure. "
            "Filters can only reference dimensions."
        )


@dataclass
class RelatedTable:
    table: "Table"
    foreign_key: str


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


def _acc_paths(acc: dict, path: JoinPath):
    acc[path[-1]].append(path)
    return acc


@dataclass(repr=False)
class Table:
    id: str
    source: str
    description: Optional[str]
    primary_key: str
    related: Dict[str, RelatedTable] = field(default_factory=dict)
    measures: Dict[str, Measure] = field(default_factory=dict)
    dimensions: Dict[str, Dimension] = field(default_factory=dict)

    @cache
    def find_all_paths(self, path: JoinPath = ()) -> List[JoinPath]:
        """Find all join paths from this table to other tables."""
        result = []
        if path:
            result.append(path)
        for alias, rel in self.related.items():
            item = JoinPathItem(rel.table, alias)
            if item in path:
                continue  # skip on cycle
            result.extend(rel.table.find_all_paths(path + (item,)))
        return result

    @cached_property
    def allowed_join_paths(self) -> Dict[str, JoinPath]:
        """A dict of table id -> tuple of JoinPathItem. Join targets for which there
        exists only a single join path.
        """
        paths = reduce(_acc_paths, self.find_all_paths(), defaultdict(lambda: []))
        return {k.table.id: v[0] for k, v in paths.items() if len(v) == 1}

    @cached_property
    def dimension_join_paths(self) -> Dict[str, List[str]]:
        result = {}
        for path in self.allowed_join_paths.values():
            *_, target = path
            for key in target.table.dimensions:
                result[key] = [self.id] + [p.alias for p in path]
        return result

    @cached_property
    def allowed_dimensions(self) -> Dict[str, "Dimension"]:
        """Which dimensions are allowed to be used with this table as anchor.
        Only those to which there's a single direct join path. If there isn't,
        dimensions must be declared directly on a table that's available for join.
        """
        dims = {}
        dims.update(self.dimensions)
        for *_, target in self.allowed_join_paths.values():
            dims.update(target.table.dimensions)
        return dims

    def get_join_path(self, target: str) -> List[str]:
        """Get an aliased join path from this table to target table. Includes current
        table."""
        if target == self.id:  # same table
            return [self.id]
        result = self.allowed_join_paths.get(target)
        if result is None:
            raise ValueError(
                f"There's no unambiguous join path from {self} to Table({target})"
            )
        return [self.id] + [i.alias for i in result]

    def get_measure_expr_and_paths(self, measure_id: str) -> Tuple[Tree, List[str]]:
        measure = self.measures[measure_id]
        join_path = [self.id]
        return measure.prepare_expr([self.id]), [
            join_path,
            *(join_path + p for p in measure.join_paths),
        ]

    def get_dimension_expr_and_paths(self, dimension_id: str) -> Tuple[Tree, List[str]]:
        dimension = self.allowed_dimensions.get(dimension_id)
        if dimension is None:
            raise ValueError(f"Dimension {dimension_id} can't be used with {self}")
        join_path = self.dimension_join_paths.get(dimension_id)
        return dimension.prepare_expr(join_path), [
            join_path,
            *(join_path + p for p in dimension.join_paths),
        ]

    def get_filter_expr_and_paths(self, filter_expr: Tree):
        dimensions = filter_expr.find_data("dimension")
        paths = []
        exprs = {}
        for tree in dimensions:
            (ref,) = tree.children
            expr, p = self.get_dimension_expr_and_paths(ref)
            exprs[ref] = expr
            paths.extend(p)
        resolver = FilterResolver(exprs)
        expr = resolver.resolve(filter_expr)
        return expr, paths

    def _resolve_calculations(self, calcs, resolver_cls):
        resolver = resolver_cls({k: v.expr for k, v in calcs.items()})
        for calc in calcs.values():
            try:
                calc.expr = resolver.resolve(calc.expr)
            except ResolverError as e:
                raise e.__class__(f"Error processing {calc}: {e}")

    def resolve_calculations(self):
        self._resolve_calculations(self.measures, MeasureResolver)
        self._resolve_calculations(self.dimensions, DimensionResolver)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"Table({self.id})"
