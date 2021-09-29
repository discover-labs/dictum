import itertools
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cache, cached_property, reduce
from typing import ClassVar, Dict, Generator, List, Optional, Tuple

from lark import Transformer, Tree, Visitor

from nestor.store import schema
from nestor.store.expr.parser import parse_expr


class ExpressionResolver(Transformer):
    """Replaces references to other expressions with the actual expression, so that
    there are only references to table columns left in all expressions.
    """

    def __init__(
        self,
        calculation: "Calculation",
        parents: List[str] = None,
        visit_tokens: bool = True,
    ):
        self._calc = calculation
        if parents is None:
            parents = []
        if calculation.id in parents:
            parents.append(calculation.id)
            path = " <- ".join(parents)
            raise RecursionError(f"{calculation.id} references itself: {path}")
        self._parents = parents + [calculation.id]
        super().__init__(visit_tokens=visit_tokens)

    def ref(self, children):
        *tables, field = children
        dep = self._calc.store._all.get(field)

        # check that there's a foreign key if needed
        # prefix = tables[0] if tables else self._calc.table.id
        if len(tables) > 0:
            try:
                self._calc.table._check_foreign_key(tables[0])
            except ValueError as e:  # TODO: better errors
                raise ValueError(f"Error processing dependencies for {self._calc}: {e}")

        # dependency wasn't found in the registry, means it's a column
        if dep is None:
            return Tree("column", children)

        # check that a measure doesn't reference dimension and vice versa
        if not isinstance(dep, self._calc.__class__):
            raise ValueError(
                f"{self._calc} references {dep}. Only calculations of the "
                "same type can reference each other"
            )

        resolver = ExpressionResolver(dep, parents=self._parents)
        return resolver.transform().children[0]

    def transform(self):
        return super().transform(self._calc.expr)


class RelatedPathsBuilder(Transformer):
    """Given a calculation and an anchor, returns a list of required join paths."""

    def __init__(self, anchor: "Table", calculation: "Calculation"):
        self._calc = calculation
        self._anchor = anchor
        # remove last part of the join path because all fields in the
        # target table are already prepended with table name
        self._base_path = anchor.get_join_path(calculation.table.id)
        self._paths: List[List[str]] = []
        super().__init__()

    def column(self, children: list):
        *tables, field = children
        self._paths.append(self._base_path + tables)
        return Tree("column", [".".join(self._paths[-1]), field])

    def build(self) -> Tuple[Tree, List[str]]:
        expr = self.transform(self._calc.expr)
        return expr, self._paths


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

    @cached_property
    def _all(self):
        return {**self.measures, **self.dimensions}

    def _check_foreign_key(self, table: str):
        """Checks that a foreign key to the table exists."""
        if table not in self.related:
            raise ValueError(
                f"No primary key for table {table} in the config, "
                "other tables can't reference it in calculations."
            )

    @cached_property
    def allowed_join_paths(self) -> Dict[str, JoinPath]:
        """A dict of table id -> tuple of JoinPathItem"""
        paths = reduce(_acc_paths, self.find_all_paths(), defaultdict(lambda: []))
        return {k.table.id: v[0] for k, v in paths.items() if len(v) == 1}

    @cached_property
    def allowed_dimensions(self) -> Dict[str, "Dimension"]:
        """Which dimensions are allowed to be used with this table as anchor.
        Only those to which there's a single direct join path. If there isn't,
        dimensions must be declared directly on a table that's available for join.
        """
        dims = {}
        dims.update(self.dimensions)
        for _, (*_, target) in self.allowed_join_paths.items():
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
    def dimension_tables(self) -> Dict[str, str]:
        """A mapping of allowed dimension IDs to table IDs."""
        return {k: v.table.id for k, v in self.allowed_dimensions.items}

    def get_dimension(self, dimension_id: str) -> Tuple[Tree, List[str]]:
        """Request a dimension relative to this table. Returns an expression with
        embedded table identity and a join path.
        """
        dimension = self.allowed_dimensions.get(dimension_id)
        if dimension is None:
            raise ValueError(f"Dimension {dimension_id} can't be used with {self}")
        builder = RelatedPathsBuilder(self, dimension)
        return builder.build()

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

    type: ClassVar[str]
    store: "Store"
    id: str
    name: str
    description: Optional[str]
    expr: Tree
    table: Table

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self):
        return str(self)

    def resolve_dependencies(self):
        resolver = ExpressionResolver(self)
        self.expr = resolver.transform()


@dataclass(repr=False)
class Dimension(Calculation):
    @cached_property
    def join_paths(self) -> List[List[str]]:
        builder = RelatedPathsBuilder(self.table, self)
        result = []
        for path in builder.build():
            result.append(path)
        return result


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
        fk = self.table.related[table_or_alias].foreign_key
        table = self.table.related[table_or_alias].table
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
        """Unnested joins in the correct orders."""
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
                    store=self,
                    id=measure_id,
                    expr=parse_expr(measure.expr),
                    table=table,
                    **measure.dict(include={"name", "description"}),
                )
                self.measures[measure_id] = _measure
                table.measures[measure_id] = _measure
            for dimension_id, dimension in config_table.dimensions.items():
                _dimension = Dimension(
                    store=self,
                    id=dimension_id,
                    expr=parse_expr(dimension.expr),
                    table=table,
                    **dimension.dict(include={"name", "description"}),
                )
                table.dimensions[dimension_id] = _dimension
                self.dimensions[dimension_id] = _dimension
        for _, measure in self.measures.items():
            measure.resolve_dependencies()
        for _, dimension in self.dimensions.items():
            dimension.resolve_dependencies()

    @classmethod
    def from_yaml(cls, path: str):
        config = schema.Config.from_yaml(path)
        return cls(config)

    @cached_property
    def _all(self):
        return {**self.measures, **self.dimensions}

    def ensure_table(self, table: schema.Table, table_id: str) -> Table:
        if table_id not in self.tables:
            self.tables[table_id] = Table(
                id=table_id,
                **table.dict(include={"source", "description", "primary_key"}),
            )
        return self.tables[table_id]

    def get_anchor(self, query: schema.Query) -> Table:
        """Decide which table for this query is the anchor.

        Check that the query is valid in terms of measures
        - All measures exist
        - All measures are declared on the same table (anchor)

        Returns the anchor table.
        """
        anchor = None
        for measure_id in query.measures:
            measure = self.measures.get(measure_id)
            if measure is None:
                raise ValueError(f"Measure {measure_id} does not exist")
            if anchor is not None and measure.table != anchor:
                raise ValueError(
                    f"Anchor table is {anchor}, but {measure} anchor "
                    f"is {measure.table}. "
                    "Only measures declared on the same table are allowed."
                )
            anchor = measure.table
        return anchor

    def execute_query(self, query: schema.Query) -> Computation:
        """Returns an object that can then be executed on a backend."""
        anchor = self.get_anchor(query)
        measures = {}
        dimensions = {}

        # build the join tree
        tree = JoinTree(table=anchor, identity=anchor.id)
        for measure_id in query.measures:
            measure = self.measures.get(measure_id)
            builder = RelatedPathsBuilder(anchor, measure)
            expr, paths = builder.build()
            for path in paths:
                tree.add_path(path[1:])
            measures[measure_id] = expr
        for dimension_id in query.dimensions:
            expr, paths = anchor.get_dimension(dimension_id)
            for path in paths:
                tree.add_path(path[1:])
            dimensions[dimension_id] = expr
        return Computation(
            join_tree=tree,
            measures=measures,
            dimensions=dimensions,
        )
