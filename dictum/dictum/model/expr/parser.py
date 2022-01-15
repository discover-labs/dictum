from pathlib import Path

from lark import Lark, Token, Transformer, Tree

from dictum import utils


class Preprocessor(Transformer):
    """First pass transform. Replace // with floor and division, unquote strings etc."""

    def STRING(self, token: Token):
        """Unquotes string values (by default they are captured with '')"""
        return Token("STRING", token.value[1:-1])

    def IDENTIFIER(self, token: Token):
        return token.value

    def isnotnull(self, children):
        return Tree("NOT", [Tree("isnull", children)])

    def not_(self, children):
        return Tree("NOT", children)

    def and_(self, children):
        return Tree("AND", children)

    def or_(self, children):
        return Tree("OR", children)

    def in_(self, children):
        return Tree("IN", children)

    def not_in(self, children):
        return Tree("NOT", Tree("IN", children))

    def fdiv(self, children):
        """Replaces floor division operator (//) with
        normal division and a function call
        """
        left, right = children
        return Tree("call", ["floor", Tree("div", [left, right])])

    def call(self, children):
        """Convert all function calls to lowercase"""
        fn, *args = children
        fn = fn.lower()
        upper_fns = {"if"}  # some functions can only be uppercase methods
        fn = fn.upper() if fn in upper_fns else fn
        return Tree("call", [fn, *args])


grammar = Path(__file__).parent / "expr.lark"
parser = Lark(grammar.read_text(), start="expr", lexer="standard")
preprocessor = Preprocessor()


def parse_expr(expr: str, missing=None):
    result = preprocessor.transform(parser.parse(expr))
    if missing is not None:
        return Tree(
            "expr",
            [
                Tree(
                    "call",
                    ["coalesce", result.children[0], utils.value_to_token(missing)],
                )
            ],
        )
    return result
