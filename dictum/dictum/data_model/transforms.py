from dataclasses import dataclass, field
from functools import cached_property
from typing import List, Optional

from lark import Transformer, Tree

from dictum import schema
from dictum.data_model.expr.parser import parse_expr


class TransformTransformer(Transformer):
    def __init__(self, arg, args: dict, visit_tokens: bool = True) -> None:
        self._arg = arg
        self._args = args
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children: list):
        return self._args[children[0]]

    def ARG(self, _):
        return self._arg

    def expr(self, children: list):
        return children[0]


@dataclass
class Transform:
    id: str
    name: str
    str_expr: str
    args: List[str] = field(default_factory=list)
    description: Optional[str] = None
    return_type: Optional[schema.Type] = None
    format: Optional[schema.FormatConfig] = None

    @cached_property
    def expr(self):
        return parse_expr(self.str_expr)

    def compile(self, arg, args: dict):
        if len(args) != len(self.args):
            raise ValueError(
                f"Expected {len(self.args)} arguments for {self.id}, got {len(args)}: {args}."
            )
        transformer = TransformTransformer(arg, dict(zip(self.args, args)))
        return transformer.transform(self.expr)

    def get_compiler(self, args: dict):
        def compiler(arg):
            return self.compile(arg, args)

        return compiler


class IsInTransform:
    """This filter is a special case, because you can't implement variable-argument
    functions with user-defined transforms.
    """

    return_type: schema.Type = "bool"

    def __init__(self):
        self.id = "in"
        self.name = "in"
        self.description = "Filter only given values"

    def get_compiler(self, args: list):
        def compiler(arg):
            return Tree("IN", [arg, *args])

        return compiler
