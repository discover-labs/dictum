from copy import deepcopy
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

from lark import Transformer, Tree

import nestor.store
from nestor.store import schema
from nestor.store.expr.parser import missing_token


class ColumnReferenceTransformer(Transformer):
    """Replaces a list of tables in a column reference with a '.'-delimited string."""

    def __init__(self, base_path: List[str], visit_tokens: bool = True) -> None:
        self._base = base_path
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children):
        *tables, column = children
        return Tree("column", [".".join([*self._base, *tables]), column])


@dataclass
class Calculation:
    """Parent class for measures and dimensions."""

    id: str
    name: str
    description: Optional[str]
    expr: Tree
    str_expr: str
    type: str
    format: Optional[str]
    currency: Optional[str]
    missing: Optional[Any]

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

    def prepare_range_expr(self, base_path: List[str]) -> Tuple[Tree, Tree]:
        return (
            Tree("call", ["min", self.prepare_expr(base_path)]),
            Tree("call", ["max", self.prepare_expr(base_path)]),
        )

    @cached_property
    def metadata(self) -> schema.CalculationMetadata:
        return schema.CalculationMetadata(
            name=self.name,
            format=self.format,
            kind="dimension" if isinstance(self, Dimension) else "measure",
            type=getattr(self, "type", None),
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
    table: "nestor.store.Table"

    @cached_property
    def joins(self) -> List["nestor.store.Join"]:
        query = nestor.store.AggregateQuery(table=self.table)
        for ref in self.expr.find_data("column"):
            *tables, _ = ref.children
            query.add_path(tables)
        return query.joins


@dataclass
class DimensionQueryDefaults:
    filter: Optional[schema.QueryDimensionTransform] = None
    transform: Optional[schema.QueryDimensionTransform] = None


@dataclass(eq=False, repr=False)
class Dimension(TableCalculation):
    # not really a default, schema prevents that
    query_defaults: Optional[DimensionQueryDefaults] = None

    @cached_property
    def related(self) -> Dict[str, "nestor.store.AggregateQuery"]:
        """Virtual related tables that need to be added to the user-defined related
        tables. Will be joined as a subquery. Aggregate dimensions are implemented this
        way.
        Run before resolving the expression.
        """
        result = {}
        for ref in self.expr.find_data("measure"):
            # figure out the subquery — group the measure by self.table.primary_key
            measure_id = ref.children[0]
            source_table = self.table.measure_backlinks[measure_id]
            subquery = nestor.store.AggregateQuery(
                table=source_table,
                subquery=True,
            )
            subquery.add_measure(measure_id)
            path = [p.alias for p in source_table.allowed_join_paths.get(self.table.id)]
            subquery.add_path(path)
            subquery.groupby[self.table.primary_key] = Tree(
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
            result[f"__subquery__{measure_id}"] = nestor.store.RelatedTable(
                table=subquery,
                foreign_key=self.table.primary_key,
                related_key=self.table.primary_key,
                alias=measure_id,
            )
        return result

    def prefixed_expr(self, path: List[str]) -> Tree:
        result = deepcopy(self.expr)
        for ref in result.find_data("column"):
            *tables, field = ref.children
            ref.children = [*path, *tables, field]
        return result


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
            str_expr=self.str_expr,
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
