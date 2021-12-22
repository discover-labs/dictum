from dictum.schema.query import (
    QueryDimension,
    QueryDimensionRequest,
    QueryScalarTransform,
    QueryMetric,
    QueryMetricRequest,
    QueryTableTransform,
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
