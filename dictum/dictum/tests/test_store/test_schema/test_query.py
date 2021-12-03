import pytest
from pydantic import ValidationError

from dictum.query import Query, QueryDimensionRequest


def test_query_duplicate_dimensions():
    Query.parse_obj(
        {
            "metrics": [{"metric": "x"}, {"metric": "y"}],
            "dimensions": [
                {"dimension": "z", "alias": "a"},
                {"dimension": "z", "alias": "b"},
            ],
        }
    )
    with pytest.raises(ValidationError):
        Query.parse_obj(
            {
                "metrics": [{"metric": "x"}, {"metric": "y"}],
                "dimensions": [
                    {"dimension": "z", "alias": "a"},
                    {"dimension": "f", "alias": "a"},
                ],
            }
        )


def test_dimension_request_column_name():
    assert QueryDimensionRequest.parse_obj({"dimension": "x"}).name == "x"
    assert (
        QueryDimensionRequest.parse_obj(
            {"dimension": "x", "transform": {"id": "y"}}
        ).name
        == "x__y"
    )
    assert (
        QueryDimensionRequest.parse_obj(
            {"dimension": "x", "transform": {"id": "y", "args": [1, "n", 2]}}
        ).name
        == "x__y_1_n_2"
    )
