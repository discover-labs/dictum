from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

from lark import Transformer, Tree

import dictum.data_model
from dictum import schema
from dictum.data_model.expr.parser import value_to_token, parse_expr


class ResolutionError(Exception):
    pass


@dataclass
class Displayed:
    id: str
    name: str
    description: str
    type: schema.Type
    format: Optional[schema.FormatConfig]
    missing: Optional[Any]

    def __post_init__(self):
        if isinstance(self.format, dict):
            self.format = schema.FormatConfig.parse_obj(self.format)


@dataclass
class Calculation(Displayed):
    """Parent class for measures and dimensions."""

    str_expr: str

    @cached_property
    def expr(self) -> Tree:
        raise NotImplementedError

    @cached_property
    def parsed_expr(self):
        return parse_expr(self.str_expr)

    @cached_property
    def expr_tree(self) -> str:
        return self.expr.pretty()

    def check_references(self, path=tuple()):
        if self.id in path:
            raise RecursionError(f"Circular reference in {self}: {path}")
        self.check_measure_references(path + (self.id,))
        self.check_dimension_references(path + (self.id,))

    def check_measure_references(self, path):
        raise NotImplementedError

    def check_dimension_references(self, path):
        for ref in self.parsed_expr.find_data("dimension"):
            dimension = self.table.allowed_dimensions.get(ref.children[0])
            if dimension is None:
                raise KeyError(
                    f"{self} uses dimension {ref.children[0]}, but there's "
                    f"no unambiguous join path between {self.table} "
                    "and dimension's parent table"
                )
            dimension.check_references(path)

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
    table: "dictum.data_model.Table"

    @cached_property
    def joins(self) -> List["dictum.data_model.Join"]:
        query = dictum.data_model.AggregateQuery(table=self.table)
        for ref in self.expr.find_data("column"):
            _, *path, _ = ref.children
            query.add_path(path)
        return query.joins


class DimensionTransformer(Transformer):
    def __init__(
        self,
        table: "dictum.data_model.Table",
        measures: Dict[str, "Measure"],
        dimensions: Dict[str, "Dimension"],
        visit_tokens: bool = True,
    ) -> None:
        self._table = table
        self._measures = measures
        self._dimensions = dimensions
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children: list):
        return Tree("column", [self._table.id, *children])

    def measure(self, children: list):
        measure_id = children[0]
        return Tree("column", [self._table.id, f"__subquery__{measure_id}", measure_id])

    def dimension(self, children: list):
        dimension_id = children[0]
        dimension = self._dimensions[dimension_id]
        path = self._table.dimension_join_paths.get(dimension_id, [])
        return dimension.prefixed_expr(path).children[0]


@dataclass(eq=False, repr=False)
class Dimension(TableCalculation):
    is_union: bool = False

    @cached_property
    def expr(self) -> Tree:
        self.check_references()
        transformer = DimensionTransformer(
            self.table, self.table.measure_backlinks, self.table.allowed_dimensions
        )
        expr = transformer.transform(self.parsed_expr)
        if self.missing is not None:
            expr = Tree(
                "expr",
                [
                    Tree(
                        "call",
                        ["coalesce", expr.children[0], value_to_token(self.missing)],
                    )
                ],
            )
        return expr

    def check_measure_references(self, path=tuple()):
        for ref in self.parsed_expr.find_data("measure"):
            measure_id = ref.children[0]
            measure = self.table.measure_backlinks.get(measure_id).measures.get(
                measure_id
            )
            measure.check_references(path)

    @cached_property
    def related(self) -> Dict[str, "dictum.data_model.AggregateQuery"]:
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
            subquery = dictum.data_model.AggregateQuery(
                table=source_table,
                subquery=True,
            )
            subquery.add_measure(measure_id)
            path = source_table.allowed_join_paths.get(self.table)
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
            column = dictum.data_model.ColumnCalculation(
                expr=expr, name=self.table.primary_key, type="number"
            )
            subquery.groupby.append(column)
            result[f"__subquery__{measure_id}"] = dictum.data_model.RelatedTable(
                table=subquery,
                foreign_key=self.table.primary_key,
                related_key=self.table.primary_key,
                alias=measure_id,
            )
        return result


@dataclass
class DimensionsUnion(Displayed):
    pass


class MeasureTransformer(Transformer):
    def __init__(
        self,
        table: "dictum.data_model.Table",
        measures: Dict[str, "Measure"],
        dimensions: Dict[str, "Dimension"],
        visit_tokens: bool = True,
    ) -> None:
        self._table = table
        self._measures = measures
        self._dimensions = dimensions
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children: list):
        return Tree("column", [self._table.id, *children])

    def measure(self, children: list):
        measure_id = children[0]
        return self._measures[measure_id].expr.children[0]

    def dimension(self, children: list):
        dimension_id = children[0]
        path = self._table.dimension_join_paths[dimension_id]
        return self._dimensions[dimension_id].prefixed_expr(path).children[0]


@dataclass(repr=False)
class Measure(TableCalculation):
    @cached_property
    def expr(self) -> Tree:
        self.check_references()
        transformer = MeasureTransformer(
            self.table, self.table.measures, self.table.allowed_dimensions
        )
        return transformer.transform(self.parsed_expr)

    @cached_property
    def dimensions(self):
        return self.table.allowed_dimensions.values()

    def check_measure_references(self, path=tuple()):
        for ref in self.parsed_expr.find_data("measure"):
            measure = self.table.measures.get(ref.children[0])
            measure.check_references(path)


class MetricTransformer(Transformer):
    def __init__(
        self,
        metrics: Dict[str, "Metric"],
        measures: Dict[str, "Measure"],
        visit_tokens: bool = True,
    ) -> None:
        self._metrics = metrics
        self._measures = measures
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children: list):
        raise ValueError("Column references are not allowed in metrics")

    def dimension(self, children: list):
        raise ValueError("Dimension references are not allowed in metrics")

    def measure(self, children: list):
        ref_id = children[0]
        if ref_id in self._metrics:
            return self._metrics[ref_id].expr.children[0]
        if ref_id in self._measures:
            return Tree("measure", children)
        raise KeyError(f"reference {ref_id} not found")


@dataclass(repr=False)
class Metric(Calculation):
    store: "dictum.data_model.DataModel"

    @classmethod
    def from_measure(
        cls, measure: Measure, store: "dictum.data_model.DataModel"
    ) -> "Metric":
        return cls(
            store=store,
            id=measure.id,
            name=measure.name,
            description=measure.description,
            str_expr=f"${measure.id}",
            type=measure.type,
            format=measure.format,
            missing=measure.missing,
        )

    @cached_property
    def expr(self) -> Tree:
        metrics = self.store.metrics.copy()
        del metrics[self.id]
        transformer = MetricTransformer(metrics, self.store.measures)
        try:
            expr = transformer.transform(self.parsed_expr)
        except Exception as e:
            raise ResolutionError(f"Error resolving expression of {self}: {e}")
        if self.missing is not None:
            expr = Tree(
                "expr",
                [
                    Tree(
                        "call",
                        ["coalesce", expr.children[0], value_to_token(self.missing)],
                    )
                ],
            )
        return expr

    @cached_property
    def measures(self):
        result = []
        for ref in self.expr.find_data("measure"):
            result.append(self.store.measures.get(ref.children[0]))
        return result

    @cached_property
    def dimensions(self) -> Dict[str, Dimension]:
        return sorted(
            set.intersection(*(set(m.dimensions) for m in self.measures)),
            key=lambda x: x.name,
        )
