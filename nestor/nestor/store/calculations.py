from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional, Union

from lark import Transformer, Tree

from nestor.store import schema
from nestor.store.schema.types import DimensionType


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
    format: Optional[Union[str, schema.CalculationFormat]]

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

    @cached_property
    def metadata(self) -> schema.CalculationMetadata:
        format = (
            self.format.spec
            if isinstance(self.format, schema.CalculationFormat)
            else self.format
        )
        patch = {}
        if isinstance(self.format, schema.CalculationFormat) and (
            self.format.prefix or self.format.suffix
        ):
            patch = {"currency": [self.format.prefix, self.format.sufix]}
        return schema.CalculationMetadata(
            name=self.name,
            format=format,
            locale_patch=patch,
        )

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
