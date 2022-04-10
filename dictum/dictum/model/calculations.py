from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

from lark import Transformer, Tree

import dictum.model
from dictum import schema
from dictum.model import utils
from dictum.model.expr import get_expr_kind, get_expr_total_function, parse_expr
from dictum.utils import value_to_token


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

    @cached_property
    def kind(self) -> str:
        try:
            return get_expr_kind(self.parsed_expr)
        except ValueError as e:
            raise ValueError(
                f"Error in {self} expression {self.str_expr}: {e}"
            ) from None

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

    def prefixed_expr(self, prefix: List[str]) -> Tree:
        return utils.prefixed_expr(self.expr, prefix)

    def prepare_expr(self, prefix: List[str]) -> Tree:
        return utils.prepare_expr(self.expr, prefix)

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
    table: "dictum.model.Table"


class DimensionTransformer(Transformer):
    def __init__(
        self,
        table: "dictum.model.Table",
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
                        [
                            "coalesce",
                            expr.children[0],
                            value_to_token(self.missing),
                        ],
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

    # @cached_property
    # def related(self) -> Dict[str, "dictum.engine.RelationalQuery"]:
    #     """Virtual related tables that need to be added to the user-defined related
    #     tables. Will be joined as a subquery. Aggregate dimensions are implemented
    #     this way.
    #     """
    #     result = {}
    #     for ref in self.expr.find_data("column"):
    #         if len(ref.children) < 3:  # not on a related table
    #             continue
    #         _, *path, measure_id = ref.children
    #         if not path[0].startswith("__subquery__"):  # not a subquery
    #             continue
    #         # figure out the subquery — group the measure by self.table.primary_key
    #         source_table = self.table.measure_backlinks[measure_id]
    #         measure = source_table.measures.get(measure_id)

    #         # a fake dimension representing the pk
    #         pk = Dimension(
    #             id="__pk",
    #             name="__pk",
    #             type=None,
    #             str_expr=source_table.primary_key,
    #             table=source_table,
    #         )

    #         engine = dictum.engine.Engine()
    #         subquery = engine.get_aggregation(
    #             measures=[measure],
    #             dimensions=[
    #                 dictum.model.ResolvedQueryDimensionRequest(
    #                     dimension=pk, transforms=[], name="__pk"
    #                 )
    #             ],
    #         )
    #         result[f"__subquery__{measure_id}"] = dictum.model.RelatedTable.create(
    #             parent=self.table,
    #             table=subquery,
    #             foreign_key=self.table.primary_key,
    #             related_key=self.table.primary_key,
    #             alias=f"__subquery__{measure_id}",
    #         )
    #     return result


@dataclass
class TableFilter:
    table: "dictum.model.Table"
    str_expr: str

    @cached_property
    def expr(self) -> Tree:
        expr = parse_expr(self.str_expr)
        transformer = DimensionTransformer(
            table=self.table,
            measures=self.table.measure_backlinks,
            dimensions=self.table.allowed_dimensions,
        )
        return transformer.transform(expr)


@dataclass
class DimensionsUnion(Displayed):
    pass


class MeasureTransformer(Transformer):
    def __init__(
        self,
        table: "dictum.model.Table",
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
    str_filter: Optional[str] = None
    str_time: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.kind != "aggregate":
            raise ValueError(
                f"Measures must be aggregate, {self} expression is not: {self.str_expr}"
            )

        if (
            self.str_time is not None
            and self.str_time not in self.table.allowed_dimensions
        ):
            raise KeyError(
                f"{self.str_time} is specified as a time dimension for {self}, "
                "but it can't be used with this measure"
            )

    @cached_property
    def expr(self) -> Tree:
        self.check_references()
        transformer = MeasureTransformer(
            self.table, self.table.measures, self.table.allowed_dimensions
        )
        return transformer.transform(self.parsed_expr)

    @cached_property
    def filter(self) -> Tree:
        if self.str_filter is None:
            return None
        self.check_references()
        transformer = DimensionTransformer(
            self.table, self.table.measure_backlinks, self.table.allowed_dimensions
        )
        return transformer.transform(parse_expr(self.str_filter))

    @property
    def time(self) -> Dimension:
        if self.str_time is None:
            raise ValueError(
                f"{self} doesn't have a time dimension specified so it "
                "can't be used with the built-in Time dimension"
            )

        return self.table.allowed_dimensions[self.str_time]

    @cached_property
    def total_function(self) -> Optional[str]:
        return get_expr_total_function(self.expr)

    @cached_property
    def dimensions(self):
        return self.table.allowed_dimensions.values()

    def check_measure_references(self, path=tuple()):
        for ref in self.parsed_expr.find_data("measure"):
            measure = self.table.measures.get(ref.children[0])
            measure.check_references(path)

    def __eq__(self, other: "Metric"):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


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
    model: "dictum.model.Model"
    is_measure: bool = False

    @classmethod
    def from_measure(cls, measure: Measure, model: "dictum.model.Model") -> "Metric":
        return cls(
            model=model,
            id=measure.id,
            name=measure.name,
            description=measure.description,
            str_expr=f"${measure.id}",
            type=measure.type,
            format=measure.format,
            missing=measure.missing,
            is_measure=True,
        )

    @cached_property
    def expr(self) -> Tree:
        metrics = self.model.metrics.copy()
        del metrics[self.id]
        transformer = MetricTransformer(metrics, self.model.measures)
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
                        [
                            "coalesce",
                            expr.children[0],
                            value_to_token(self.missing),
                        ],
                    )
                ],
            )
        return expr

    @cached_property
    def merged_expr(self) -> Tree:
        """Same as expr, but measures are selected as column from the merged table"""
        expr = deepcopy(self.expr)
        for ref in expr.find_data("measure"):
            ref.data = "column"
            ref.children = [None, *ref.children]
        return expr

    @cached_property
    def measures(self) -> List[Measure]:
        result = []
        for ref in self.expr.find_data("measure"):
            result.append(self.model.measures.get(ref.children[0]))
        return result

    @cached_property
    def dimensions(self) -> Dict[str, Dimension]:
        return sorted(
            set.intersection(*(set(m.dimensions) for m in self.measures)),
            key=lambda x: x.name,
        )
