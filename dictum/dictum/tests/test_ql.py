from lark import Tree

from dictum.ql import compile_query
from dictum.ql.parser import parse_filter, parse_grouping, parse_ql
from dictum.ql.transformer import compile_filter, compile_grouping
from dictum.schema import Query, QueryDimensionFilter, QueryDimensionRequest


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


def test_where_transform():
    assert parse_ql("select x where y.z(1)") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [Tree("filter", [Tree("dimension", ["y"]), Tree("call", ["z", 1])])],
            ),
        ],
    )


def test_where_transforms():
    assert parse_ql("select x where y.a(1).b('c').d = 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [
                    Tree(
                        "filter",
                        [
                            Tree("dimension", ["y"]),
                            Tree("call", ["a", 1]),
                            Tree("call", ["b", "c"]),
                            Tree("call", ["d"]),
                            Tree("call", ["eq", 0]),
                        ],
                    )
                ],
            ),
        ],
    )


def test_where_gt():
    assert parse_ql("select x where y > 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [Tree("filter", [Tree("dimension", ["y"]), Tree("call", ["gt", 0])])],
            ),
        ],
    )


def test_where_ge():
    assert parse_ql("select x where y >= 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [Tree("filter", [Tree("dimension", ["y"]), Tree("call", ["ge", 0])])],
            ),
        ],
    )


def test_where_lt():
    assert parse_ql("select x where y < 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [Tree("filter", [Tree("dimension", ["y"]), Tree("call", ["lt", 0])])],
            ),
        ],
    )


def test_where_le():
    assert parse_ql("select x where y <= 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [Tree("filter", [Tree("dimension", ["y"]), Tree("call", ["le", 0])])],
            ),
        ],
    )


def test_where_eq():
    assert parse_ql("select x where y = 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [Tree("filter", [Tree("dimension", ["y"]), Tree("call", ["eq", 0])])],
            ),
        ],
    )


def test_where_ne():
    assert parse_ql("select x where y <> 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [Tree("filter", [Tree("dimension", ["y"]), Tree("call", ["ne", 0])])],
            ),
        ],
    )


def test_groupby():
    assert parse_ql("select x by y") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "grouping",
                        [
                            Tree("dimension", ["y"]),
                        ],
                    )
                ],
            ),
        ],
    )


def test_groupby_transform():
    assert parse_ql("select x group by y.z(10)") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "grouping",
                        [Tree("dimension", ["y"]), Tree("call", ["z", 10])],
                    )
                ],
            ),
        ],
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
    assert parse_ql("select metric by dim.test as dim1") == Tree(
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


def test_in():
    assert parse_ql("select x where y in ('a', 1)") == Tree(
        "query",
        [
            Tree("select", [Tree("metric", ["x"])]),
            Tree(
                "where",
                [
                    Tree(
                        "filter",
                        [Tree("dimension", ["y"]), Tree("call", ["isin", "a", 1])],
                    )
                ],
            ),
        ],
    )


def test_compile_query():
    assert compile_query("select x") == Query.parse_obj({"metrics": [{"metric": "x"}]})


def test_compile_groupby():
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "x"}],
            "dimensions": [{"dimension": "y"}],
        }
    )
    assert compile_query("select x group by y") == q
    assert compile_query("select x by y") == q


def test_compile_groupby_transforms():
    assert compile_query("select x, y by z.p(10)") == Query.parse_obj(
        {
            "metrics": [{"metric": "x"}, {"metric": "y"}],
            "dimensions": [
                {"dimension": "z", "transforms": [{"id": "p", "args": [10]}]}
            ],
        }
    )


def test_compile_where():
    assert compile_query("select x where y.z(10)") == Query.parse_obj(
        {
            "metrics": [{"metric": "x"}],
            "filters": [{"dimension": "y", "transforms": [{"id": "z", "args": [10]}]}],
        }
    )


def test_compile_multiple_groupbys():
    compile_query(
        """
    select x, y
    where z.z(1, 2, 3),
        a.b('a')
    by d.d('d'),
       c,
       f.h(11)
    """
    ) == Query.parse_obj(
        {
            "metrics": [{"metric": "x"}, {"metric": "y"}],
            "dimensions": [
                {
                    "dimension": "d",
                    "transforms": [{"id": "d", "args": ["d"]}],
                },
                {"dimension": "c"},
                {"dimension": "f", "tranforms": [{"id": "h", "args": [11]}]},
            ],
            "filters": [
                {
                    "dimension": "z",
                    "transforms": [{"id": "z", "args": [1, 2, 3]}],
                },
                {"dimension": "a", "transforms": [{"id": "b", "args": ["a"]}]},
            ],
        }
    )


def test_compile_dimension_alias():
    assert compile_query("select metric by dim as dim1") == Query.parse_obj(
        {
            "metrics": [{"metric": "metric"}],
            "dimensions": [{"dimension": "dim", "alias": "dim1"}],
        }
    )


def test_compile_dimension_transform_alias():
    assert compile_query("select x by y.a.b(10) as z") == Query.parse_obj(
        {
            "metrics": [{"metric": "x"}],
            "dimensions": [
                {
                    "dimension": "y",
                    "transforms": [{"id": "a"}, {"id": "b", "args": [10]}],
                    "alias": "z",
                }
            ],
        }
    )


def test_parse_filter():
    assert parse_filter("x.y('z')") == Tree(
        "filter", [Tree("dimension", ["x"]), Tree("call", ["y", "z"])]
    )


def test_compile_filter():
    assert compile_filter("x.y('z')") == QueryDimensionFilter.parse_obj(
        {"dimension": "x", "transforms": [{"id": "y", "args": ["z"]}]}
    )


def test_filter_null():
    assert parse_filter("x is null") == Tree(
        "filter", [Tree("dimension", ["x"]), Tree("call", ["isnull"])]
    )
    assert parse_filter("x is not null") == Tree(
        "filter", [Tree("dimension", ["x"]), Tree("call", ["isnotnull"])]
    )


def test_compile_filter_null():
    assert compile_filter("x is null") == QueryDimensionFilter.parse_obj(
        {"dimension": "x", "transforms": [{"id": "isnull", "args": []}]}
    )


def test_parse_grouping():
    assert parse_grouping("x.y(1)") == Tree(
        "grouping", [Tree("dimension", ["x"]), Tree("call", ["y", 1])]
    )
    assert parse_grouping("x") == Tree("grouping", [Tree("dimension", ["x"])])


def test_compile_grouping():
    assert compile_grouping("x") == QueryDimensionRequest(dimension="x")
    assert compile_grouping("x.y") == QueryDimensionRequest.parse_obj(
        {"dimension": "x", "transforms": [{"id": "y"}]}
    )
    assert compile_grouping("x.y('z', 1)") == QueryDimensionRequest.parse_obj(
        {"dimension": "x", "transforms": [{"id": "y", "args": ["z", 1]}]}
    )
