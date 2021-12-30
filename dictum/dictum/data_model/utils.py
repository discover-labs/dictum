from copy import deepcopy
from typing import List

from lark import Tree


def merged_expr(name: str):
    return Tree("expr", [Tree("column", [None, name])])


def prefixed_expr(expr: Tree, prefix: List[str]) -> Tree:
    """Prefix the expression with the given join path."""
    result = deepcopy(expr)
    for ref in result.find_data("column"):
        # skip first child: host table's name
        _, *path, field = ref.children
        ref.children = [*prefix, *path, field]
    return result


def prepare_expr(expr: Tree, prefix: List[str]) -> Tree:
    """Prepare the expression for query: turn prefixed path into .-delimited string"""
    expr = prefixed_expr(expr, prefix)
    for ref in expr.find_data("column"):
        *path, field = ref.children
        ref.children = [".".join(path), field]
    return expr


def join_exprs_with_and(exprs: List[Tree]):
    expr, *rest = exprs
    if len(rest) == 0:
        return expr
    if len(rest) > 1:
        return Tree("AND", [expr, join_exprs_with_and(rest)])
    return Tree("AND", [expr, rest[0]])
