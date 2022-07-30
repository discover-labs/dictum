from pathlib import Path

from lark import Lark, Token, Transformer, Tree

grammar = (Path(__file__).parent / "ql.lark").read_text()
ql = Lark(grammar, start="query")


def filter_tree(name: str, dimension: Tree, value):
    return Tree("filter", [dimension, Tree("call", [name, value])])


def call_scalar_children(name: str):
    def method(self, children: list):
        return Tree("scalar_transform", [name, *children])

    return method


class Preprocessor(Transformer):
    transform_aliases = {
        "not": "invert",
    }

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

    def op(self, children: str):
        return children[0]

    def scalar_transform(self, children: list):
        id, *args = children
        id = self.transform_aliases.get(id, id)
        return Tree("scalar_transform", [id, *args])

    gt = call_scalar_children("gt")
    ge = call_scalar_children("ge")
    lt = call_scalar_children("lt")
    le = call_scalar_children("le")
    eq = call_scalar_children("eq")
    ne = call_scalar_children("ne")
    isnull = call_scalar_children("isnull")
    isnotnull = call_scalar_children("isnotnull")
    isin = call_scalar_children("isin")


pre = Preprocessor()


def parse_ql(query: str):
    return pre.transform(ql.parse(query))


dimension = Lark(grammar, start="dimension")


def parse_dimension(expr: str):
    """
    A separate function to parse string transform definitions during interactive use
    """
    return pre.transform(dimension.parse(expr))


dimension_request = Lark(grammar, start="dimension_request")


def parse_dimension_request(expr: str):
    return pre.transform(dimension_request.parse(expr))


metric = Lark(grammar, start="metric")


def parse_metric(expr: str):
    return pre.transform(metric.parse(expr))


metric_request = Lark(grammar, start="metric_request")


def parse_metric_request(expr: str):
    return pre.transform(metric_request.parse(expr))
