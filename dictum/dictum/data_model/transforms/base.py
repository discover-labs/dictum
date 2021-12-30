from lark import Tree

from dictum import schema
from dictum.data_model.computation import ColumnCalculation
from dictum.utils import value_to_token


class BaseTransform:
    def __init__(self, *args):
        self._args = [value_to_token(a) for a in args]

    def get_name(self, name: str) -> str:
        return name

    def get_return_type(self, original: schema.Type) -> schema.Type:
        if self.return_type is not None:
            return self.return_type
        return original

    def get_format(self, type_: schema.Type) -> schema.FormatConfig:
        type_ = self.get_return_type(type_)
        kind = "string"
        if type_ in {"date", "datetime"}:
            kind = type_
        elif type_ in {"int", "float"}:
            kind = "decimal"
        return schema.FormatConfig(kind=kind)

    def transform_expr(self, expr: Tree) -> Tree:
        raise NotImplementedError

    def __call__(self, col: ColumnCalculation) -> ColumnCalculation:
        return ColumnCalculation(
            name=self.get_name(col.name),
            type=self.get_return_type(col.type),
            expr=Tree("expr", [self.transform_expr(col.expr.children[0])]),
        )
