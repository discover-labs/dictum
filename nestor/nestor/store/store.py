from collections import defaultdict
from dataclasses import dataclass, field
from functools import cache, cached_property, reduce
from typing import Dict, List, Optional, Tuple

from lark import Transformer, Tree

from nestor.store import schema
from nestor.store.expr.parser import parse_expr
from nestor.store.schema.types import DimensionType


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


class ColumnReferenceTransformer(Transformer):
    """Replaces a list of tables in a column reference with a '.'-delimited string."""

    def __init__(self, base_path: List[str], visit_tokens: bool = True) -> None:
        self._base = base_path
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children):
        *tables, column = children
        return Tree("column", [".".join([*self._base, *tables]), column])


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
    measures: Dict[str, "Measure"] = field(default_factory=dict)
    dimensions: Dict[str, "Dimension"] = field(default_factory=dict)

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


@dataclass
class Calculation:
    """Parent class for measures and dimensions."""

    id: str
    name: str
    description: Optional[str]
    expr: Tree
    str_expr: str

    @cached_property
    def join_paths(self) -> List[List[str]]:
        result = []
        for column in self.expr.find_data("column"):
            *tables, _ = column.children
            if tables:
                result.append(list(tables))
        return result

    def prepare_expr(self, base_path: List[str]) -> Tree:
        t = ColumnReferenceTransformer(base_path)
        return t.transform(self.expr)

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self):
        return str(self)


@dataclass(repr=False)
class Dimension(Calculation):
    type: DimensionType


@dataclass(repr=False)
class Measure(Calculation):
    pass


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
class Computation:
    """What the backend gets to compile and execute."""

    join_tree: JoinTree
    measures: Dict[str, Tree]
    dimensions: Dict[str, Tree]
    filters: List[Tree] = field(default_factory=lambda: [])


class Store:
    """The actual metrics store. Receives a query object, figures out which computations
    on the source tables are required to be performed in order to fulfil the query.

    The main purpose of this object is to take in the config and prepare all the data
    structures for the incoming queries.
    - It parses the expressions.
    - Resolves references to anchor tables (tables on which a calculation was declared)
      by adding the actual table id. E.g. sum(amount) -> sum(anchor_table.amount)
    - Resolves references to other calculations by replacing the reference with the
      referenced calculation's parse tree.
    - If the referenced calculation uses any columns of it's related tables, prepends
      references to these columns with the anchor table of the referenced calculation,
      e.g. if the calculation on table `orders` is `users.channel`, and
      `channel` dimension on `users` is `attributions.channel`, the resolved reference
      on orders will be `users.attributions.channel`.

    `execute_query` method returns an object that can then be executed on a backend.

    Query processing consists of figuring out which joins need to be performed,
    deduplicating the joins, arranging them in a tree and returning a Calculation object.
    """

    aggregate = {
        "sum",
        "avg",
        "max",
        "min",
        "distinct",
    }
    scalar = {
        "abs",
        "floor",
        "ceil",
        "round",
    }
    builtins = scalar | aggregate

    def __init__(self, config: schema.Config):
        self.tables: Dict[str, Table] = {}
        self.measures: Dict[str, Measure] = {}
        self.dimensions: Dict[str, Dimension] = {}
        for table_id, config_table in config.tables.items():
            table = self.ensure_table(config_table, table_id)
            for related_id, related in config_table.related.items():
                if related.table not in config.tables:
                    raise KeyError(
                        f"Table {related.table} is referenced as a foreign key target "
                        f"for table {table_id}, but it's not defined in the config."
                    )
                table.related[related_id] = RelatedTable(
                    table=self.ensure_table(
                        config.tables[related.table], related.table
                    ),
                    foreign_key=related.foreign_key,
                )
            for measure_id, measure in config_table.measures.items():
                _measure = Measure(
                    id=measure_id,
                    expr=parse_expr(measure.expr),
                    str_expr=measure.expr,
                    **measure.dict(include={"name", "description"}),
                )
                self.measures[measure_id] = _measure
                table.measures[measure_id] = _measure
            for dimension_id, dimension in config_table.dimensions.items():
                _dimension = Dimension(
                    id=dimension_id,
                    expr=parse_expr(dimension.expr),
                    str_expr=dimension.expr,
                    type=dimension.type,
                    **dimension.dict(include={"name", "description"}),
                )
                table.dimensions[dimension_id] = _dimension
                self.dimensions[dimension_id] = _dimension
        for table in self.tables.values():
            table.resolve_calculations()

    @classmethod
    def from_yaml(cls, path: str):
        config = schema.Config.from_yaml(path)
        return cls(config)

    def ensure_table(self, table: schema.Table, table_id: str) -> Table:
        if table_id not in self.tables:
            self.tables[table_id] = Table(
                id=table_id,
                **table.dict(include={"source", "description", "primary_key"}),
            )
        return self.tables[table_id]

    @cached_property
    def measures_tables(self) -> Dict[str, str]:
        result = {}
        for table in self.tables.values():
            for k in table.measures:
                result[k] = table.id
        return result

    def get_anchor(self, query: schema.Query) -> Table:
        """Decide which table for this query is the anchor.

        Check that the query is valid in terms of measures
        - All measures exist
        - All measures are declared on the same table (anchor)

        Returns the anchor table.
        """
        anchor: Optional[str] = None
        for measure_id in query.measures:
            table = self.measures_tables.get(measure_id)
            if table is None:
                raise ValueError(f"Measure {measure_id} does not exist")
            if anchor is not None and table != anchor:
                raise ValueError(
                    f"Anchor table is {anchor}, but {measure_id} anchor "
                    f"is {table}. "
                    "Only measures declared on the same table are allowed."
                )
            anchor = table
        return self.tables[anchor]

    def execute_query(self, query: schema.Query) -> Computation:
        """Returns an object that can then be executed on a backend."""
        anchor = self.get_anchor(query)
        measures = {}
        dimensions = {}
        filters = []

        tree = JoinTree(table=anchor, identity=anchor.id)
        for measure_id in query.measures:
            expr, paths = anchor.get_measure_expr_and_paths(measure_id)
            for path in paths:
                tree.add_path(path[1:])
            measures[measure_id] = expr
        for dimension_id in query.dimensions:
            expr, paths = anchor.get_dimension_expr_and_paths(dimension_id)
            for path in paths:
                tree.add_path(path[1:])
            dimensions[dimension_id] = expr

        for filter in query.filters:
            expr, paths = anchor.get_filter_expr_and_paths(parse_expr(filter))
            filters.append(expr)
            for path in paths:
                tree.add_path(path[1:])

        return Computation(
            join_tree=tree, measures=measures, dimensions=dimensions, filters=filters
        )

    def suggest_measures(self, query: schema.Query) -> List[Measure]:
        """Suggest a list of possible measures based on a query. Returns a list of
        measures from the same anchor table as the first, excluding the ones already
        in the query.
        """
        anchor = self.get_anchor(query)
        return [m for m in anchor.measures.values() if m.id not in query.measures]

    def suggest_dimensions(self, query: schema.Query) -> List[Dimension]:
        anchor = self.get_anchor(query)
        return [
            self.dimensions[d]
            for d in anchor.allowed_dimensions
            if d not in query.dimensions
        ]

    @cached_property
    def _all(self):
        return {**self.measures, **self.dimensions}
