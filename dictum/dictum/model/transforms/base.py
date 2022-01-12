from lark import Tree

from dictum import schema
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

    def __call__(self, column):
        return column.__class__(
            name=self.get_name(column.name),
            type=self.get_return_type(column.type),
            expr=Tree("expr", [self.transform_expr(column.expr.children[0])]),
        )
