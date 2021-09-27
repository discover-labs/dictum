import pytest
from lark import Token, Tree, exceptions

from nestor.store.expr.parser import parse_expr, parser


def test_and_whitespace():
    """Test that whitespace around binary keyword operators (and/or) works the same as
    in Python.
    """
    tree = Tree("and", [Token("NUMBER", "1"), Token("NUMBER", "1")])
    assert parser.parse("1 and 1").children[0] == tree
    assert parser.parse("(1)and(1)").children[0] == tree
    assert parser.parse("1and(1)").children[0] == tree
    with pytest.raises(exceptions.UnexpectedToken):
        parser.parse("1and1")


def test_fields():
    """Field access syntax."""
    assert parse_expr("field").children[0] == Tree("ref", ["field"])
    assert parser.parse("related.field").children[0] == Tree(
        "ref", ["related", "field"]
    )


def test_mul():
    """Test that multiplication is parsed.
    There was a bug where mul wasn't added to the grammar correctly.
    """
    assert parser.parse("2 * 2").children[0] == Tree(
        "mul", [Token("NUMBER", "2"), Token("NUMBER", "2")]
    )


def test_neq():
    """Test that both != and <> is supported."""
    tree = Tree("neq", [Token("NUMBER", "1"), Token("NUMBER", "1")])
    assert parser.parse("1 <> 1").children[0] == tree
    assert parser.parse("1 != 1").children[0] == tree


def test_fdiv():
    """Test that floor division operator (//) is replaced with a function call,
    e.g. 7 // 3 -> floor(7 / 3)
    """
    assert parse_expr("7 // 3").children[0] == Tree(
        "call", ["floor", Tree("div", [Token("NUMBER", "7"), Token("NUMBER", "3")])]
    )


def test_unquote():
    """Test that string values are unquoted."""
    assert parse_expr("'test'").children[0].value == "test"
