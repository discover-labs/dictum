from pathlib import Path

from lark import Lark, Token, Transformer, Tree

grammar = (Path(__file__).parent / "ql.lark").read_text()
ql = Lark(grammar, start="query")


def filter_tree(name: str, dimension: Tree, value):
    return Tree("filter", [dimension, Tree("call", [name, value])])


class Preprocessor(Transformer):
    def identifier(self, children: list):
        return children[0]

    def IDENTIFIER(self, token: Token):
        return token.value

    def QUOTED_IDENTIFIER(self, token: Token):
        return token.value[1:-1]  # unquote

    def STRING(self, value: str):
        return value[1:-1]  # unquote

    def INTEGER(self, value: str):
        return int(value)

    def FLOAT(self, value: str):
        return float(value)

    def op(self, children: list):
        return children[0]

    def gt(self, children: list):
        return filter_tree("gt", *children)

    def ge(self, children: list):
        return filter_tree("ge", *children)

    def lt(self, children: list):
        return filter_tree("lt", *children)

    def le(self, children: list):
        return filter_tree("le", *children)

    def eq(self, children: list):
        return filter_tree("eq", *children)

    def ne(self, children: list):
        return filter_tree("ne", *children)

    def isnull(self, children: list):
        return Tree("filter", [children[0], Tree("call", ["isnull"])])

    def isnotnull(self, children: list):
        return Tree("filter", [children[0], Tree("call", ["isnotnull"])])

    def isin(self, children: list):
        dimension, *values = children
        return Tree("filter", [dimension, Tree("call", ["isin", *values])])


pre = Preprocessor()


def parse_ql(query: str):
    return pre.transform(ql.parse(query))


filter = Lark(grammar, start="filter")


def parse_filter(expr: str):
    """A separate function to parse string transform definitions during interactive use"""
    return pre.transform(filter.parse(expr))


grouping = Lark(grammar, start="grouping")


def parse_grouping(expr: str):
    return pre.transform(grouping.parse(expr))
