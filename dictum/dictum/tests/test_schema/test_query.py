from dictum.schema.query import (
    QueryDimension,
    QueryDimensionRequest,
    QueryMetric,
    QueryMetricRequest,
    QueryScalarTransform,
    QueryTableTransform,
    QueryTransform,
)


def test_calculation():
    assert (
        QueryDimensionRequest(dimension=QueryDimension(id="test")).calculation.id
        == "test"
    )
    assert QueryMetricRequest(metric=QueryMetric(id="test")).calculation.id == "test"


def test_calculation_name():
    assert QueryDimension(id="x").name == "x"
    assert (
        QueryDimension(id="x", transforms=[QueryScalarTransform(id="a")]).name == "x__a"
    )
    assert (
        QueryDimension(
            id="x", transforms=[QueryScalarTransform(id="y", args=["a", 1])]
        ).name
        == "x__y_a_1"
    )

    assert QueryMetric(id="x").name == "x"
    assert (
        QueryMetric(
            id="x",
            transforms=[
                QueryTableTransform(
                    id="y",
                    args=[1],
                    of=[QueryDimension(id="a")],
                    within=[
                        QueryDimension(
                            id="b",
                            transforms=[QueryScalarTransform(id="s", args=["ab"])],
                        )
                    ],
                )
            ],
        ).name
        == "x__y_1_of_a_within_b__s_ab"
    )


def test_request_name():
    assert QueryMetricRequest(metric=QueryMetric(id="a"), alias="b").name == "b"
    assert (
        QueryDimensionRequest(dimension=QueryDimension(id="a"), alias="b").name == "b"
    )


def test_render_transform():
    assert QueryTransform(id="test").render() == "test()"
    assert QueryTransform(id="test", args=[1, "a"]).render() == "test(1, 'a')"


def test_render_table_transform():
    assert (
        QueryTableTransform(id="test", args=[1], of=[QueryDimension(id="x")]).render()
        == "test(1) of (x)"
    )
    assert (
        QueryTableTransform(
            id="test",
            args=[1],
            of=[QueryDimension(id="x", transforms=[QueryScalarTransform(id="year")])],
        ).render()
        == "test(1) of (x.year())"
    )
    assert (
        QueryTableTransform(
            id="test",
            args=[1],
            of=[
                QueryDimension(id="x", transforms=[QueryScalarTransform(id="year")]),
                QueryDimension(id="y"),
            ],
        ).render()
        == "test(1) of (x.year(), y)"
    )
    assert (
        QueryTableTransform(
            id="test",
            args=[1],
            of=[
                QueryDimension(id="x", transforms=[QueryScalarTransform(id="year")]),
                QueryDimension(id="y"),
            ],
            within=[
                QueryDimension(id="z"),
            ],
        ).render()
        == "test(1) of (x.year(), y) within (z)"
    )


def test_render_request():
    assert (
        QueryMetricRequest(metric=QueryMetric(id="test"), alias="x").render()
        == 'test as "x"'
    )


def test_render_query_metric():
    assert (
        QueryMetric.parse_obj(
            {"id": "test", "transforms": [{"id": "x"}, {"id": "gt", "args": [1]}]}
        ).render()
        == "test.x().gt(1)"
    )
