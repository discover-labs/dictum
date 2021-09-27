from dataclasses import dataclass, field
from functools import cached_property
from typing import ClassVar, Dict, List, Optional

from lark import Transformer, Tree, Visitor

from nestor.store import schema
from nestor.store.computation import Computation
from nestor.store.expr.parser import parse_expr


class ExpressionResolver(Transformer):
    """Replaces references to other expression with the actual expression, so that
    there are only references to tables left in all expressions.
    """

    def __init__(self, calculation: "Calculation", visit_tokens: bool = True):
        self._calc = calculation
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
            # always prepend with calc table name
            return Tree("column", [self._calc.table.id, *children])

        # check that a measure doesn't reference dimension and vice versa
        if not isinstance(dep, self._calc.__class__):
            raise ValueError(
                f"{self._calc} references {dep}. Only calculations of the "
                "same type can reference each other"
            )

        resolver = ExpressionResolver(dep)
        return resolver.transform().children[0]

    def transform(self):
        return super().transform(self._calc.expr)


class RelatedPathsBuilder(Visitor):
    """Given a calculation, and an anchor returns a list of relevant required join paths."""

    def __init__(self, anchor: "Table", calculation: "Calculation"):
        self._calc = calculation
        self._anchor = anchor
        self._paths: List[List[str]] = []
        super().__init__()

    def column(self, tree: Tree):
        *tables, _ = tree.children
        if tables[0] != self._anchor.id:  # if the same table, no join
            self._paths.append(tables)

    def build(self) -> List[List["Table"]]:
        self.visit(self._calc.expr)
        return self._paths


class ColumnExpressionBuilder(Transformer):
    """Given a calculation, replaces references to columns with table identity as is
    specified in JoinTree.
    """

    def __init__(self, calculation: "Calculation", visit_tokens: bool = True) -> None:
        self._calc = calculation
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children):
        *tables, field = children
        return Tree("column", [".".join(tables), field])

    def build(self):
        return self.transform(self._calc.expr)


@dataclass
class RelatedTable:
    table: "Table"
    alias: str
    foreign_key: str


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
        """Checks that there's exactly one foreign key to the supplied table."""
        if table not in self.related:
            raise ValueError(
                f"No primary key for table {table} in the config, "
                "other tables can't reference it in calculations."
            )

    @cached_property
    def allowed_dimensions(self) -> Dict[str, "Dimension"]:
        """Which dimensions are allowed to use with this table as anchor.
        Only those declared on tables to which the anchor table has foreign keys.
        """
        dims = {}
        dims.update(self.dimensions)
        for _, rel in self.related.items():
            dims.update(rel.table.dimensions)
        return dims

    def get_foreign_key(self, table_or_alias: str):
        """Return foreign key for a related table."""
        return self.related[table_or_alias].foreign_key

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
    pass


@dataclass(repr=False)
class Measure(Calculation):
    pass


@dataclass
class Join:
    """A single join"""

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
        fk = self.table.get_foreign_key(table_or_alias)
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
            for related in config_table.related:
                if related.table not in config.tables:
                    raise KeyError(
                        f"Table {related.table} is referenced as a foreign key target "
                        f"for table {table_id}, but it's not defined in the config."
                    )
                table.related[related.ref] = RelatedTable(
                    table=self.ensure_table(
                        config.tables[related.table], related.table
                    ),
                    **related.dict(include={"foreign_key", "alias"}),
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
                    f"Anchor table is {anchor}, but measure {measure}'s anchor "
                    "is {measure.table}. "
                    "Only measures declared on the same table are allowed."
                )
            anchor = measure.table
        return anchor

    def get_dimension(self, anchor: Table, dimension_id: str) -> Dimension:
        """Check that the dimension exists and is allowed for the given anchor.

        Returns the dimension.
        """
        dimension = self.dimensions.get(dimension_id)
        if dimension is None:
            raise ValueError(f"Dimension {dimension_id} does not exist")
        if dimension_id not in anchor.allowed_dimensions:
            raise ValueError(
                f"Dimension {dimension_id} can't be used in this query. "
                f"Only dimensions declared directly on table {anchor} and "
                "it's related tables are allowed."
            )
        return dimension

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
            for path in builder.build():
                tree.add_path(path)
            measures[measure_id] = measure
        for dimension_id in query.dimensions:
            dimension = self.get_dimension(anchor, dimension_id)
            builder = RelatedPathsBuilder(anchor, dimension)
            for path in builder.build():
                tree.add_path(path)
            dimensions[dimension_id] = dimension
        breakpoint()
        # prepare expressions
