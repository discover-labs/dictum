import pytest
from lark import ParseError, Token, Tree, UnexpectedToken

from nestor.store.expr.parser import parse_expr, parser


def test_integer_number():
    assert parse_expr("42").children[0] == Token("INTEGER", "42")
    assert parse_expr("3.14").children[0] == Token("FLOAT", "3.14")


def test_boolean():
    assert parse_expr("TrUe").children[0] == Token("TRUE", "TrUe")
    assert parse_expr("fAlSe").children[0] == Token("FALSE", "fAlSe")


def test_and_whitespace():
    """Test that whitespace around binary keyword operators (and/or) works the same as
    in Python.
    """
    tree = Tree("AND", [Token("INTEGER", "1"), Token("INTEGER", "1")])
    assert parse_expr("1 and 1").children[0] == tree
    assert parse_expr("(1)and(1)").children[0] == tree
    assert parse_expr("1and(1)").children[0] == tree
    with pytest.raises(UnexpectedToken):
        parse_expr("1and1")


def test_column():
    """Column syntax."""
    assert parse_expr("col").children[0] == Tree("column", ["col"])
    assert parser.parse("related.col").children[0] == Tree("column", ["related", "col"])
    assert parser.parse("related.other.col").children[0] == Tree(
        "column", ["related", "other", "col"]
    )


def test_measure():
    """Referencing other calculation"""
    assert parse_expr("$calc").children[0] == Tree("measure", ["calc"])
    with pytest.raises(ParseError):
        parse_expr("$table.calc")


def test_dimension():
    """Referencing other dimensions."""
    assert parse_expr(":dim").children[0] == Tree("dimension", ["dim"])
    with pytest.raises(ParseError):
        parse_expr(":table.dim")


def test_mul():
    """Test that multiplication is parsed.
    There was a bug where mul wasn't added to the grammar correctly.
    """
    assert parser.parse("2 * 2").children[0] == Tree(
        "mul", [Token("INTEGER", "2"), Token("INTEGER", "2")]
    )


def test_neq():
    """Test that both != and <> is supported."""
    tree = Tree("neq", [Token("INTEGER", "1"), Token("INTEGER", "1")])
    assert parser.parse("1 <> 1").children[0] == tree
    assert parser.parse("1 != 1").children[0] == tree


def test_fdiv():
    """Test that floor division operator (//) is replaced with a function call,
    e.g. 7 // 3 -> floor(7 / 3)
    """
    assert parse_expr("7 // 3").children[0] == Tree(
        "call", ["floor", Tree("div", [Token("INTEGER", "7"), Token("INTEGER", "3")])]
    )


def test_unquote():
    """Test that string values are unquoted."""
    assert parse_expr("'test'").children[0].value == "test"


def test_in():
    assert parse_expr("x in (1, 2, 3)").children[0] == Tree(
        "IN",
        [
            Tree("column", ["x"]),
            Token("INTEGER", "1"),
            Token("INTEGER", "2"),
            Token("INTEGER", "3"),
        ],
    )
    assert parse_expr("x in (0)").children[0] == Tree(
        "IN", [Tree("column", ["x"]), Token("INTEGER", "0")]
    )
    assert parse_expr("x > 0 and y in (0)").children[0] == Tree(
        "AND",
        [
            Tree("gt", [Tree("column", ["x"]), Token("INTEGER", "0")]),
            Tree("IN", [Tree("column", ["y"]), Token("INTEGER", "0")]),
        ],
    )
    assert parse_expr("y in (0) and x > 0").children[0] == Tree(
        "AND",
        [
            Tree("IN", [Tree("column", ["y"]), Token("INTEGER", "0")]),
            Tree("gt", [Tree("column", ["x"]), Token("INTEGER", "0")]),
        ],
    )
    assert parse_expr("x or 2 + 2 in (4)").children[0] == Tree(
        "OR",
        [
            Tree("column", ["x"]),
            Tree(
                "IN",
                [
                    Tree("add", [Token("INTEGER", "2"), Token("INTEGER", "2")]),
                    Token("INTEGER", "4"),
                ],
            ),
        ],
    )


def test_case_abbr():
    assert parse_expr("case when x > 0 then 1 end").children[0] == Tree(
        "case",
        [
            Tree("gt", [Tree("column", ["x"]), Token("INTEGER", "0")]),
            Token("INTEGER", "1"),
        ],
    )


def test_case_full():
    assert parse_expr("case when x > 0 then 1 else -1 end").children[0] == Tree(
        "case",
        [
            Tree(
                "gt",
                [
                    Tree("column", ["x"]),
                    Token("INTEGER", "0"),
                ],
            ),
            Token("INTEGER", "1"),
            Token("INTEGER", "-1"),
        ],
    )


def test_case_multi():
    assert parse_expr("case when x > 0 then 1 when x < 0 then -1 else 0 end").children[
        0
    ] == Tree(
        "case",
        [
            Tree("gt", [Tree("column", ["x"]), Token("INTEGER", "0")]),
            Token("INTEGER", "1"),
            Tree("lt", [Tree("column", ["x"]), Token("INTEGER", "0")]),
            Token("INTEGER", "-1"),
            Token("INTEGER", "0"),
        ],
    )


def test_arg():
    assert parse_expr("@ >= 10").children[0] == Tree(
        "gte", [Token("ARG", "@"), Token("INTEGER", "10")]
    )


def test_coalesce():
    assert parse_expr("test", missing=0).children[0] == Tree(
        "call", ["coalesce", Tree("column", ["test"]), Token("INTEGER", "0")]
    )
