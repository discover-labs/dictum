from dataclasses import dataclass, field
from typing import List, Optional

from lark import Transformer, Tree


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
    expr: Tree
    args: List[str] = field(default_factory=list)
    description: Optional[str] = None
    return_type: Optional[str] = None
    format: Optional[str] = None

    def compile(self, arg, args: list):
        if len(args) != len(self.args):
            raise ValueError(
                f"Expected {len(self.args)} arguments for {self.id}, got {len(args)}: {args}."
            )
        transformer = TransformTransformer(arg, dict(zip(self.args, args)))
        return transformer.transform(self.expr)

    def get_compiler(self, args: list):
        def compiler(arg):
            return self.compile(arg, args)

        return compiler


class InFilter:
    """This filter is a special case, because you can't implement variable-argument
    functions with user-defined transforms.
    """

    def __init__(self):
        self.id = "in"
        self.name = "in"
        self.description = "Filter only given values"

    def get_compiler(self, args: list):
        def compiler(arg):
            return Tree("IN", [arg, *args])

        return compiler
