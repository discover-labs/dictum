from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional, Tuple

from lark import Transformer, Tree

from nestor.store import schema
from nestor.store.schema.types import CalculationType


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
    format: Optional[schema.CalculationFormat]
    key: bool = False

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


@dataclass(repr=False)
class Dimension(Calculation):
    # not really a default, schema prevents that
    type: CalculationType = CalculationType.continuous


@dataclass(repr=False)
class Measure(Calculation):
    def metric(self) -> "Metric":
        return Metric(
            self.id,
            name=self.name,
            description=self.description,
            expr=Tree("expr", [Tree("measure", [self.id])]),
            str_expr=self.str_expr,
            format=self.format,
            key=self.key,
        )


@dataclass(repr=False)
class Metric(Measure):
    """Metric"""

    @cached_property
    def measures(self) -> List[str]:
        result = []
        for tree in self.expr.find_data("measure"):
            result.append(tree.children[0])
        return result
