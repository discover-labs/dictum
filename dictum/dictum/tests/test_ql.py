from lark import Tree

from dictum.ql import compile_query
from dictum.ql.parser import (
    parse_dimension,
    parse_dimension_request,
    parse_metric_request,
    parse_ql,
)
from dictum.ql.transformer import (
    compile_dimension,
    compile_dimension_request,
    compile_metric_request,
)
from dictum.schema.query import (
    Query,
    QueryDimension,
    QueryDimensionRequest,
    QueryMetricRequest,
)


def test_single_metric():
    assert parse_ql("select revenue") == Tree(
        "query",
        [Tree("select", [Tree("metric_request", [Tree("metric", ["revenue"])])])],
    )


def test_metric_transform():
    assert parse_ql("select x.sum(1, 2, 3) of (x) within (y, z)") == Tree(
        "query",
        [
            Tree(
                "select",
                [
                    Tree(
                        "metric_request",
                        [
                            Tree(
                                "metric",
                                [
                                    "x",
                                    Tree(
                                        "table_transform",
                                        [
                                            "sum",
                                            1,
                                            2,
                                            3,
                                            Tree("of", [Tree("dimension", ["x"])]),
                                            Tree(
                                                "within",
                                                [
                                                    Tree("dimension", ["y"]),
                                                    Tree("dimension", ["z"]),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_multiple_metrics():
    assert parse_ql("select revenue, test") == Tree(
        "query",
        [
            Tree(
                "select",
                [
                    Tree("metric_request", [Tree("metric", ["revenue"])]),
                    Tree("metric_request", [Tree("metric", ["test"])]),
                ],
            ),
        ],
    )


def test_where_transform():
    assert parse_ql("select x where y.z(1)") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where", [Tree("dimension", ["y", Tree("scalar_transform", ["z", 1])])]
            ),
        ],
    )


def test_where_transforms():
    assert parse_ql("select x where y.a(1).b('c').d = 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where",
                [
                    Tree(
                        "dimension",
                        [
                            "y",
                            Tree("scalar_transform", ["a", 1]),
                            Tree("scalar_transform", ["b", "c"]),
                            Tree("scalar_transform", ["d"]),
                            Tree("scalar_transform", ["eq", 0]),
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
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where", [Tree("dimension", ["y", Tree("scalar_transform", ["gt", 0])])]
            ),
        ],
    )


def test_where_ge():
    assert parse_ql("select x where y >= 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where", [Tree("dimension", ["y", Tree("scalar_transform", ["ge", 0])])]
            ),
        ],
    )


def test_where_lt():
    assert parse_ql("select x where y < 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where", [Tree("dimension", ["y", Tree("scalar_transform", ["lt", 0])])]
            ),
        ],
    )


def test_where_le():
    assert parse_ql("select x where y <= 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where", [Tree("dimension", ["y", Tree("scalar_transform", ["le", 0])])]
            ),
        ],
    )


def test_where_eq():
    assert parse_ql("select x where y = 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where", [Tree("dimension", ["y", Tree("scalar_transform", ["eq", 0])])]
            ),
        ],
    )


def test_where_ne():
    assert parse_ql("select x where y <> 0") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where", [Tree("dimension", ["y", Tree("scalar_transform", ["ne", 0])])]
            ),
        ],
    )


def test_groupby():
    assert parse_ql("select x by y") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree("groupby", [Tree("dimension_request", [Tree("dimension", ["y"])])]),
        ],
    )


def test_groupby_transform():
    assert parse_ql("select x group by y.z(10)") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "dimension_request",
                        [Tree("dimension", ["y", Tree("scalar_transform", ["z", 10])])],
                    )
                ],
            ),
        ],
    )


def test_quoted_identifier():
    assert parse_ql('select "revenue something"').children[0] == Tree(
        "select", [Tree("metric_request", [Tree("metric", ["revenue something"])])]
    )


def test_dimension_alias():
    assert parse_ql("select metric by dim as dim1") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["metric"])])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "dimension_request",
                        [Tree("dimension", ["dim"]), Tree("alias", ["dim1"])],
                    )
                ],
            ),
        ],
    )


def test_dimension_transform_alias():
    assert parse_ql("select metric by dim.test as dim1") == Tree(
        "query",
        [
            Tree("select", [Tree("metric_request", [Tree("metric", ["metric"])])]),
            Tree(
                "groupby",
                [
                    Tree(
                        "dimension_request",
                        [
                            Tree(
                                "dimension", ["dim", Tree("scalar_transform", ["test"])]
                            ),
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
            Tree("select", [Tree("metric_request", [Tree("metric", ["x"])])]),
            Tree(
                "where",
                [Tree("dimension", ["y", Tree("scalar_transform", ["isin", "a", 1])])],
            ),
        ],
    )


def test_compile_query():
    assert compile_query("select x") == Query.parse_obj(
        {"metrics": [{"metric": {"id": "x"}}]}
    )


def test_compile_groupby():
    q = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "x"}}],
            "dimensions": [{"dimension": {"id": "y"}}],
        }
    )
    assert compile_query("select x group by y") == q
    assert compile_query("select x by y") == q


def test_compile_groupby_transforms():
    assert compile_query("select x, y by z.p(10)") == Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "x"}}, {"metric": {"id": "y"}}],
            "dimensions": [
                {"dimension": {"id": "z", "transforms": [{"id": "p", "args": [10]}]}}
            ],
        }
    )


def test_compile_where():
    assert compile_query("select x where y.z(10)") == Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "x"}}],
            "filters": [{"id": "y", "transforms": [{"id": "z", "args": [10]}]}],
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
            "metrics": [{"metric": {"id": "x"}}, {"metric": {"id": "y"}}],
            "dimensions": [
                {
                    "dimension": {
                        "id": "d",
                        "transforms": [{"id": "d", "args": ["d"]}],
                    },
                },
                {"dimension": {"id": "c"}},
                {"dimension": {"id": "f", "tranforms": [{"id": "h", "args": [11]}]}},
            ],
            "filters": [
                {
                    "id": "z",
                    "transforms": [{"id": "z", "args": [1, 2, 3]}],
                },
                {"id": "a", "transforms": [{"id": "b", "args": ["a"]}]},
            ],
        }
    )


def test_compile_dimension_alias():
    assert compile_query("select metric by dim as dim1") == Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "metric"}}],
            "dimensions": [{"dimension": {"id": "dim"}, "alias": "dim1"}],
        }
    )


def test_compile_dimension_transform_alias():
    assert compile_query("select x by y.a.b(10) as z") == Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "x"}}],
            "dimensions": [
                {
                    "dimension": {
                        "id": "y",
                        "transforms": [{"id": "a"}, {"id": "b", "args": [10]}],
                    },
                    "alias": "z",
                }
            ],
        }
    )


def test_parse_filter():
    assert parse_dimension("x.y('z')") == Tree(
        "dimension", ["x", Tree("scalar_transform", ["y", "z"])]
    )


def test_compile_filter():
    assert compile_dimension("x.y('z')") == QueryDimension.parse_obj(
        {"id": "x", "transforms": [{"id": "y", "args": ["z"]}]}
    )


def test_filter_null():
    assert parse_dimension("x is null") == Tree(
        "dimension", ["x", Tree("scalar_transform", ["isnull"])]
    )
    assert parse_dimension("x is not null") == Tree(
        "dimension", ["x", Tree("scalar_transform", ["isnotnull"])]
    )


def test_compile_filter_null():
    assert compile_dimension("x is null") == QueryDimension.parse_obj(
        {"id": "x", "transforms": [{"id": "isnull", "args": []}]}
    )


def test_parse_dimension_request():
    assert parse_dimension_request("x.y(1)") == Tree(
        "dimension_request",
        [Tree("dimension", ["x", Tree("scalar_transform", ["y", 1])])],
    )
    assert parse_dimension_request("x") == Tree(
        "dimension_request", [Tree("dimension", ["x"])]
    )


def test_compile_dimension_request():
    assert compile_dimension_request("x") == QueryDimensionRequest.parse_obj(
        {"dimension": {"id": "x"}}
    )
    assert compile_dimension_request("x.y") == QueryDimensionRequest.parse_obj(
        {"dimension": {"id": "x", "transforms": [{"id": "y"}]}}
    )
    assert compile_dimension_request(
        "x.y('z', 1) as a"
    ) == QueryDimensionRequest.parse_obj(
        {
            "dimension": {"id": "x", "transforms": [{"id": "y", "args": ["z", 1]}]},
            "alias": "a",
        }
    )


def test_parse_metric_request():
    assert parse_metric_request("x.y(1, 'f') of (a) within (b, c) as al") == Tree(
        "metric_request",
        [
            Tree(
                "metric",
                [
                    "x",
                    Tree(
                        "table_transform",
                        [
                            "y",
                            1,
                            "f",
                            Tree("of", [Tree("dimension", ["a"])]),
                            Tree(
                                "within",
                                [Tree("dimension", ["b"]), Tree("dimension", ["c"])],
                            ),
                        ],
                    ),
                ],
            ),
            Tree("alias", ["al"]),
        ],
    )


def test_compile_metric_request():
    assert compile_metric_request(
        "x.y(1, 'f') of (a) within (b, c.n(1)) as al"
    ) == QueryMetricRequest.parse_obj(
        {
            "metric": {
                "id": "x",
                "transforms": [
                    {
                        "id": "y",
                        "args": [1, "f"],
                        "of": [{"id": "a"}],
                        "within": [
                            {"id": "b"},
                            {"id": "c", "transforms": [{"id": "n", "args": [1]}]},
                        ],
                    }
                ],
            },
            "alias": "al",
        }
    )


def test_parse_unary_not():
    assert parse_dimension("x.y(1).not") == Tree(
        "dimension",
        [
            "x",
            Tree("scalar_transform", ["y", 1]),
            Tree("scalar_transform", ["invert"]),
        ],
    )
