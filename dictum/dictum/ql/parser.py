from pathlib import Path

from lark import Lark, Token, Transformer, Tree

grammar = (Path(__file__).parent / "ql.lark").read_text()
ql = Lark(grammar, start="query")


def filter_tree(name: str, dimension: Tree, value):
    return Tree("filter", [dimension, Tree("call", [name, value])])


def call_children(name: str):
    def method(self, children: list):
        return Tree("call", [name, *children])

    return method


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

    gt = call_children("gt")
    ge = call_children("ge")
    lt = call_children("lt")
    le = call_children("le")
    eq = call_children("eq")
    ne = call_children("ne")
    isnull = call_children("isnull")
    isnotnull = call_children("isnotnull")
    isin = call_children("isin")


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
