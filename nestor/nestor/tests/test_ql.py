from lark import Tree

from nestor.ql import parse_query
from nestor.ql.parser import parse_ql
from nestor.store.schema import Query, QueryTranformRequest


def test_single_metric():
    assert parse_ql("select revenue") == Tree(
        "query", [Tree("select", [Tree("metric", ["revenue"])])]
    )


def test_multiple_metrics():
    assert parse_ql("select revenue, test") == Tree(
        "query",
        [
            Tree(
                "select",
                [
                    Tree("metric", ["revenue"]),
                    Tree("metric", ["test"]),
                ],
            ),
        ],
    )


def test_groupby():
    assert parse_ql("select revenue group by channel") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["revenue"])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "grouping",
                        [
                            Tree("dimension", ["channel"]),
                        ],
                    )
                ],
            ),
        ],
    )


def test_where():
    assert parse_ql("select revenue where amount is atleast(10)") == Tree(
        "query",
        [
            Tree(
                "select",
                [
                    Tree("metric", ["revenue"]),
                ],
            ),
            Tree(
                "where",
                [
                    Tree(
                        "condition",
                        [
                            Tree("dimension", ["amount"]),
                            Tree("call", ["atleast", 10]),
                        ],
                    ),
                ],
            ),
        ],
    )


def test_where_groupby():
    assert parse_ql(
        "select revenue where amount is atleast(10) group by channel"
    ) == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["revenue"])]),
            Tree(
                "where",
                [
                    Tree(
                        "condition",
                        [
                            Tree("dimension", ["amount"]),
                            Tree("call", ["atleast", 10]),
                        ],
                    )
                ],
            ),
            Tree("groupby", [Tree("grouping", [Tree("dimension", ["channel"])])]),
        ],
    )


def test_groupby_transform():
    assert parse_ql("select revenue group by amount with step(10)") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["revenue"])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "grouping",
                        [
                            Tree("dimension", ["amount"]),
                            Tree("call", ["step", 10]),
                        ],
                    )
                ],
            ),
        ],
    )


def test_parse_query():
    assert parse_query("select revenue") == Query(metrics=["revenue"])


def test_parse_groupby():
    assert parse_query("select revenue group by channel") == Query(
        metrics=["revenue"], dimensions=["channel"]
    )


def test_parse_groupby_transform():
    assert parse_query("select revenue, orders group by amount with step(10)") == Query(
        metrics=["revenue", "orders"],
        dimensions=["amount"],
        transforms={"amount": QueryTranformRequest(id="step", args=[10])},
    )


def test_parse_condition():
    assert parse_query("select revenue where amount is atleast(100)") == Query(
        metrics=["revenue"],
        filters={"amount": QueryTranformRequest(id="atleast", args=[100])},
    )


def test_parse_multiple_groupbys():
    parse_query(
        """
    select revenue, orders
    where category is in('A', 'B', 'C'),
        neg is atleast(0)
    group by
        date with datetrunc('day'),
        channel,
        amount with step(10)
    """
    ) == Query(
        metrics=["revenue", "orders"],
        dimensions=["date", "channel", "amount"],
        filters={
            "category": QueryTranformRequest(id="in", args=["A", "B", "C"]),
            "neg": QueryTranformRequest(id="atleast", args=[0]),
        },
        transforms={
            "date": QueryTranformRequest(id="datetrunc", args=["day"]),
            "amount": QueryTranformRequest(id="step", args=[10]),
        },
    )
