from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from typing import ClassVar, Dict, List, Optional

from lark import Token, Transformer, Tree, Visitor

from nestor.store import schema
from nestor.store.computation import Computation
from nestor.store.expr.parser import parse_expr


class AnchorResolver(Transformer):
    """Replaces implicit access to an anchor table field with an explicit one,
    e.g. `sum(field) / 10` -> `sum(anchor.field) / 10`

    Figures out which references are to columns and which are to other calculations.
    """

    def __init__(
        self,
        anchor: str,
        visit_tokens: bool = True,
    ) -> None:
        self._anchor = anchor
        super().__init__(visit_tokens=visit_tokens)

    def anchor(self, children):
        return Tree("anchor", [Token("IDENTIFIER", self._anchor), children[0]])


class DependencyBuilder(Visitor):
    """Inspects the AST and returns a list of measures and dimensions that this one
    references. Makes sure that measures and dimensions don't reference each other.
    Makes sure that there's exactly one foreign key to the target table if it's related.
    """

    def __init__(self, calculation: "Calculation") -> None:
        self._calc = calculation
        self._deps = []
        super().__init__()

    def build(self):
        self.visit(self._calc.expr)
        return self._deps

    def _table(self, tree: Tree):
        table, field = tree.children
        table: Table = self._calc.store.tables[table]
        obj = table._all.get(field.value)
        if obj is not None:
            if obj.id == self._calc.id:
                raise ValueError(f"{self.calc} references itself")
            if obj.__class__ != self._calc.__class__:
                raise ValueError(f"{self._calc} is not " f"allowed to reference {obj}")
        if (obj := getattr(table, self._calc.type).get(field.value)) is not None:
            self._deps.append(obj)

    anchor = _table

    def related(self, tree: Tree):
        """First, check that there's a foreign key to the table, then call _table."""
        table: Table = self._calc.store.tables[tree.children[0].value]
        try:
            self._calc.table._check_foreign_key(table)
        except ValueError as e:  # TODO: better error types
            raise ValueError(
                f"Error processing table dependencies for {self._calc}: {e}"
            )
        return self._table(tree)


class ColumnBuilder(Visitor):
    """Traverses the AST and returns a list of columns in related tables that this
    calculation references as a tuple (table_id, column).
    Only run after all dependencies have been resolved.
    """

    def __init__(self, calculation: "Calculation"):
        self._calc = calculation
        self._cols = []
        super().__init__()

    def related(self, tree: Tree):
        self._cols.append(tuple(c.value for c in tree.children))

    def build(self):
        self.visit(self._calc.expr)
        return self._cols


class RelatedTableResolver(Transformer):
    """Prepends references to a related table field with table id."""

    def __init__(self, related_id: str, visit_tokens: bool = True):
        self._ref = related_id
        super().__init__(visit_tokens=visit_tokens)

    def related(self, children):
        *tables, field = children
        return Tree("related", [Token("IDENTIFIER", self._ref), *tables, field])


class DependencyResolver(Transformer):
    """Replaces references to other measures and dimensions with their
    actual expression. Prepends references to a related table with that table's id.
    """

    def __init__(self, dependencies: List["Calculation"], visit_tokens: bool = True):
        self.dependencies = {(d.table.id, d.id): d for d in dependencies}
        super().__init__(visit_tokens=visit_tokens)

    def anchor(self, children):
        table, field = children
        key = (table.value, field.value)
        if key not in self.dependencies:  # a column, TODO: force to declare columns
            return Tree("anchor", children)
        dep = self.dependencies[key]
        return dep.get_resolved_expr()

    def related(self, children):
        table, field = children
        key = (table.value, field.value)
        if key not in self.dependencies:
            return Tree("related", children)
        dep = self.dependencies[key]
        expr = dep.get_resolved_expr()
        resolver = RelatedTableResolver(dep.table.id)
        return resolver.transform(expr)


@dataclass
class ForeignKey:
    column: str
    to: "Table"


@dataclass(repr=False)
class Table:
    id: str
    source: str
    description: Optional[str]
    primary_key: str
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    measures: Dict[str, "Measure"] = field(default_factory=dict)
    dimensions: Dict[str, "Dimension"] = field(default_factory=dict)

    @cached_property
    def _all(self):
        return {**self.measures, **self.dimensions}

    def _check_foreign_key(self, table: "Table"):
        """Checks that there's exactly one foreign key to the supplied table."""
        fks = {}
        for fk in self.foreign_keys:
            if fk.to is table:
                fks[fk.column] = table
        if len(fks) > 1:
            raise ValueError(
                f"{self} has multiple foreign keys to {table}, "
                f"please declare your dimensions or measures directly on {self}"
            )
        if len(fks) == 0:
            raise ValueError(f"{self} has no foreign key to {table}")

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
    _resolved: bool = False

    def __post_init__(self):
        self.resolve_anchor()

    def resolve_anchor(self):
        resolver = AnchorResolver(self.table.id)
        self.expr = resolver.transform(self.expr)
        return self

    def get_resolved_expr(self):
        if self._resolved:
            return self.expr.children[0]
        resolver = DependencyResolver(self.dependencies)
        self.expr = resolver.transform(self.expr)
        self._resolved = True
        return self.expr.children[0]

    def resolve_dependencies(self):
        self.get_resolved_expr()

    @cached_property
    def dependencies(self) -> List["Calculation"]:
        builder = DependencyBuilder(self)
        return builder.build()

    @cached_property
    def columns(self) -> List["Calculation"]:
        builder = ColumnBuilder(self)
        return builder.build()

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self):
        return str(self)


@dataclass(repr=False)
class Dimension(Calculation):
    type: ClassVar[str] = "dimensions"


@dataclass(repr=False)
class Measure(Calculation):
    type: ClassVar[str] = "measures"

    @cached_property
    def dimensions(self) -> Dict[str, Dimension]:
        """Which dimensions are allowed for this measure.
        Only those declared on tables to which the anchor table has foreign keys.
        """
        dims = {}
        for fk in self.table.foreign_keys:
            dims.update(fk.to.dimensions)
        return dims


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
        self.tables = {}
        self.measures = {}
        self.dimensions = {}
        for table_id, config_table in config.tables.items():
            table = self.ensure_table(config_table, table_id)
            for fk in config_table.foreign_keys:
                if fk.to not in config.tables:
                    raise KeyError(
                        f"Table {fk.to} is referenced as a foreign key target for "
                        "table {alias}, but it's not defined in the config."
                    )
                table.foreign_keys.append(
                    ForeignKey(
                        column=fk.column,
                        to=self.ensure_table(config.tables[fk.to], fk.to),
                    )
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

    def ensure_table(self, table: schema.Table, table_id: str) -> Table:
        if table_id not in self.tables:
            self.tables[table_id] = Table(
                id=table_id,
                **table.dict(include={"source", "description", "primary_key"}),
            )
        return self.tables[table_id]

    def execute_query(self, query: schema.Query) -> Computation:
        """Returns an object that can then be executed on a backend."""
