import pytest
from lark import Token, Tree

from dictum.engine import Column
from dictum.schema import FormatConfig
from dictum.transforms.scalar import LiteralTransform, ScalarTransform, transforms


@pytest.fixture(scope="module")
def col():
    return Column(
        name="test",
        type="int",
        expr=Tree("expr", [Token("INTEGER", "1")]),
    )


def test_transform():
    transform = ScalarTransform()
    assert transform.get_return_type("test") == "test"
    assert transform.get_format("test") == FormatConfig(kind="string")
    with pytest.raises(NotImplementedError):
        transform.transform_expr(None)


def test_literal_transform(col: Column):
    class LiteralTest(LiteralTransform):
        expr = "@ > value"
        args = ["value"]
        return_type = "bool"

    transform = LiteralTest(0)
    assert transform._expr.children[0] == Tree(
        "gt", [Token("ARG", "@"), Tree("column", ["value"])]
    )
    assert transform.transform_expr(Token("TEST", None)) == Tree(
        "gt", [Token("TEST", None), Token("INTEGER", "0")]
    )
    assert transform(col) == Column(
        name="test",
        type="bool",
        expr=Tree(
            "expr",
            [
                Tree(
                    "gt",
                    [
                        Token("INTEGER", "1"),
                        Token("INTEGER", "0"),
                    ],
                )
            ],
        ),
    )


def test_booleans(col: Column):
    for key in ["eq", "ne", "gt", "ge", "lt", "le"]:
        transform = transforms[key](0)
        result = transform(col)
        assert result.type == "bool"
        assert result.expr.children[0].data == key
        assert result.expr.children[0].children == [
            Token("INTEGER", "1"),
            Token("INTEGER", "0"),
        ]


def test_nulls(col: Column):
    result = transforms["isnull"]()(col)
    assert result.type == "bool"
    assert result.expr == Tree("expr", [Tree("isnull", [Token("INTEGER", "1")])])

    result = transforms["isnotnull"]()(col)
    assert result.type == "bool"
    assert result.expr == Tree(
        "expr", [Tree("NOT", [Tree("isnull", [Token("INTEGER", "1")])])]
    )


def test_inrange(col: Column):
    result = transforms["inrange"](-1, 1)(col)
    assert result.type == "bool"
    assert result.expr == Tree(
        "expr",
        [
            Tree(
                "AND",
                [
                    Tree("ge", [Token("INTEGER", "1"), Token("INTEGER", -1)]),
                    Tree("le", [Token("INTEGER", "1"), Token("INTEGER", "1")]),
                ],
            )
        ],
    )


def test_in(col: Column):
    result = transforms["isin"](0, 1, 2)(col)
    assert result.type == "bool"
    assert result.expr.children[0] == Tree(
        "IN",
        [
            col.expr.children[0],
            Token("INTEGER", "0"),
            Token("INTEGER", "1"),
            Token("INTEGER", "2"),
        ],
    )


def test_datepart(col: Column):
    result = transforms["datepart"]("month")(col)
    assert result.type == "int"
    assert result.expr.children[0] == Tree(
        "call", ["datepart", "month", col.expr.children[0]]
    )

    result = transforms["month"]()(col)
    assert result.type == "int"
    assert result.expr.children[0] == Tree(
        "call", ["datepart", "month", col.expr.children[0]]
    )


def test_datetrunc(col: Column):
    datetrunc = transforms["datetrunc"]("month")
    result = datetrunc(col)
    assert result.type == "datetime"
    assert result.expr.children[0] == Tree(
        "call", ["datetrunc", "month", col.expr.children[0]]
    )

    assert datetrunc.get_format("datetime").pattern is None
    assert datetrunc.get_format("datetime").skeleton == "yMMM"
