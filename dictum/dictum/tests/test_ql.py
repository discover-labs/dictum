from lark import Tree

from dictum.ql import parse_query
from dictum.ql.parser import parse_ql
from dictum.store.schema import Query


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
    assert parse_query("select revenue") == Query.parse_obj(
        {"metrics": [{"metric": "revenue"}]}
    )


def test_parse_groupby():
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}],
            "dimensions": [{"dimension": "channel"}],
        }
    )
    assert parse_query("select revenue group by channel") == q
    assert parse_query("select revenue by channel") == q


def test_parse_groupby_transform():
    assert parse_query(
        "select revenue, orders group by amount with step(10)"
    ) == Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}, {"metric": "orders"}],
            "dimensions": [
                {"dimension": "amount", "transform": {"id": "step", "args": [10]}}
            ],
        }
    )


def test_parse_condition():
    assert parse_query(
        "select revenue where amount is atleast(100)"
    ) == Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}],
            "filters": [
                {"dimension": "amount", "filter": {"id": "atleast", "args": [100]}}
            ],
        }
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
    ) == Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}, {"metric": "orders"}],
            "dimensions": [
                {
                    "dimension": "date",
                    "transform": {"id": "datetrunc", "args": ["day"]},
                },
                {"dimension": "channel"},
                {"dimension": "amount", "tranform": {"id": "step", "args": [10]}},
            ],
            "filters": [
                {
                    "dimension": "category",
                    "filter": {"id": "in", "args": ["A", "B", "C"]},
                },
                {"dimension": "neg", "filter": {"id": "atleast", "args": [0]}},
            ],
        }
    )


def test_quoted_identifier():
    assert parse_ql('select "revenue something"').children[0] == Tree(
        "select", [Tree("metric", ["revenue something"])]
    )


def test_dimension_alias():
    assert parse_ql("select metric by dim as dim1") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["metric"])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "grouping",
                        [
                            Tree("dimension", ["dim"]),
                            Tree("alias", ["dim1"]),
                        ],
                    )
                ],
            ),
        ],
    )


def test_dimension_transform_alias():
    assert parse_ql("select metric by dim with test as dim1") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["metric"])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "grouping",
                        [
                            Tree("dimension", ["dim"]),
                            Tree("call", ["test"]),
                            Tree("alias", ["dim1"]),
                        ],
                    )
                ],
            ),
        ],
    )


def test_parse_dimension_alias():
    assert parse_query("select metric by dim with test as dim1") == Query.parse_obj(
        {
            "metrics": [{"metric": "metric"}],
            "dimensions": [
                {
                    "dimension": "dim",
                    "transform": {"id": "test", "args": []},
                    "alias": "dim1",
                }
            ],
        }
    )
