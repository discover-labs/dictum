from lark import Tree

from dictum import engine, schema
from dictum.utils import value_to_token


class BaseTransform:
    def __init__(self, *args):
        self._args = [value_to_token(a) for a in args]

    def get_name(self, name: str) -> str:
        return name

    def get_display_name(self, name: str) -> str:
        return name

    def get_return_type(self, original: schema.Type) -> schema.Type:
        if self.return_type is not None:
            return self.return_type
        return original

    def get_format(self, format: schema.FormatConfig) -> schema.FormatConfig:
        return format

    def get_display_info(
        self, display_info: "engine.DisplayInfo"
    ) -> "engine.DisplayInfo":
        return engine.DisplayInfo(
            name=(
                self.get_display_name(display_info.name)
                if not display_info.keep_name
                else display_info.name
            ),
            format=self.get_format(display_info.format),
            keep_name=display_info.keep_name,
        )

    def transform_expr(self, expr: Tree) -> Tree:
        raise NotImplementedError

    def __call__(self, column: "engine.Column"):
        return engine.Column(
            name=self.get_name(column.name),
            type=self.get_return_type(column.type),
            expr=Tree("expr", [self.transform_expr(column.expr.children[0])]),
            display_info=self.get_display_info(column.display_info),
        )
