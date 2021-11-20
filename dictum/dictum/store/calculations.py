from copy import deepcopy
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

from lark import Tree

import dictum.store
from dictum.store import schema
from dictum.store.expr.parser import missing_token, parse_expr


@dataclass
class Displayed:
    id: str
    name: str
    description: str
    type: str
    format: Optional[str]
    currency: Optional[str]
    missing: Optional[Any]


@dataclass
class Calculation(Displayed):
    """Parent class for measures and dimensions."""

    expr: Tree

    def __post_init__(self):
        """Parse expr, fill in missing"""
        if isinstance(self.expr, str):
            self._parse_expr()

    def _parse_expr(self):
        self.expr = parse_expr(self.expr, missing=self.missing)

    @cached_property
    def join_paths(self) -> List[List[str]]:
        result = []
        for column in self.expr.find_data("column"):
            *tables, _ = column.children
            if tables:
                result.append(list(tables))
        return result

    def prefixed_expr(self, prefix: List[str]) -> Tree:
        """Prefix the expression with the given join path."""
        result = deepcopy(self.expr)
        for ref in result.find_data("column"):
            # skip first child: host table's name
            _, *path, field = ref.children
            ref.children = [*prefix, *path, field]
        return result

    def prepare_expr(self, prefix: List[str]) -> Tree:
        """Prepare the expression for query: turn prefixed path into .-delimited string"""
        expr = self.prefixed_expr(prefix)
        for ref in expr.find_data("column"):
            *path, field = ref.children
            ref.children = [".".join(path), field]
        return expr

    def prepare_range_expr(self, base_path: List[str]) -> Tuple[Tree, Tree]:
        return (
            Tree("call", ["min", self.prepare_expr(base_path)]),
            Tree("call", ["max", self.prepare_expr(base_path)]),
        )

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


@dataclass(eq=False, repr=False)
class TableCalculation(Calculation):
    table: "dictum.store.Table"

    def __post_init__(self):
        """add prefix column names with table id"""
        if isinstance(self.expr, str):
            self._parse_expr()
            self._prepend_columns()

    def _prepend_columns(self):
        for ref in self.expr.find_data("column"):
            ref.children = [self.table.id, *ref.children]

    @cached_property
    def joins(self) -> List["dictum.store.Join"]:
        query = dictum.store.AggregateQuery(table=self.table)
        for ref in self.expr.find_data("column"):
            _, *path, _ = ref.children
            query.add_path(path)
        return query.joins


@dataclass
class DimensionQueryDefaults:
    filter: Optional[schema.QueryDimensionTransform] = None
    transform: Optional[schema.QueryDimensionTransform] = None


@dataclass(eq=False, repr=False)
class Dimension(TableCalculation):
    # not really a default, schema prevents that
    query_defaults: Optional[DimensionQueryDefaults] = None

    def __post_init__(self):
        if isinstance(self.expr, str):
            self._parse_expr()
            self._replace_measures()
            self._prepend_columns()

    def _replace_measures(self):
        for ref in self.expr.find_data("measure"):
            measure = ref.children[0]
            ref.data = "column"
            ref.children = [f"__subquery__{measure}", measure]

    @cached_property
    def related(self) -> Dict[str, "dictum.store.AggregateQuery"]:
        """Virtual related tables that need to be added to the user-defined related
        tables. Will be joined as a subquery. Aggregate dimensions are implemented this
        way. Run before resolving the expression.
        """
        result = {}
        for ref in self.expr.find_data("column"):
            if len(ref.children) < 3:  # not on a related table
                continue
            _, *path, measure_id = ref.children
            if not path[0].startswith("__subquery__"):  # not a subquery
                continue
            # figure out the subquery — group the measure by self.table.primary_key
            source_table = self.table.measure_backlinks[measure_id]
            subquery = dictum.store.AggregateQuery(
                table=source_table,
                subquery=True,
            )
            subquery.add_measure(measure_id)
            path = [p.alias for p in source_table.allowed_join_paths.get(self.table.id)]
            subquery.add_path(path)
            expr = Tree(
                "expr",
                [
                    Tree(
                        "column",
                        [
                            ".".join([source_table.id, *path]),
                            self.table.primary_key,
                        ],
                    )
                ],
            )
            column = dictum.store.ColumnCalculation(
                expr=expr, name=self.table.primary_key, type="number"
            )
            subquery.groupby.append(column)
            result[f"__subquery__{measure_id}"] = dictum.store.RelatedTable(
                table=subquery,
                foreign_key=self.table.primary_key,
                related_key=self.table.primary_key,
                alias=measure_id,
            )
        return result


@dataclass
class DimensionsUnion(Displayed):
    pass


@dataclass(repr=False)
class Measure(TableCalculation):
    @cached_property
    def dimensions(self):
        return self.table.allowed_dimensions.values()

    def metric(self) -> "Metric":
        expr = Tree("measure", [self.id])
        if self.missing is not None:
            expr = Tree("call", ["coalesce", expr, missing_token(self.missing)])
        expr = Tree("expr", [expr])
        return Metric(
            self.id,
            name=self.name,
            description=self.description,
            expr=expr,
            type=self.type,
            format=self.format,
            currency=self.currency,
            measures=[self],
            missing=self.missing,
        )


@dataclass(repr=False)
class Metric(Calculation):
    measures: List[Measure] = field(default_factory=list)

    @cached_property
    def dimensions(self) -> Dict[str, Dimension]:
        return sorted(
            set.intersection(*(set(m.dimensions) for m in self.measures)),
            key=lambda x: x.name,
        )
