import pytest

from dictum.engine import Engine
from dictum.schema import Query


def test_query_validation_metrics(engine: Engine):
    with pytest.raises(ValueError, match="at least one metric"):
        engine.validate_query(Query())


def test_query_validation_duplicate_columns(engine: Engine):
    check = pytest.raises(ValueError, match="Duplicate column name in query")
    with check:
        engine.validate_query(
            Query.parse_obj(
                {"metrics": [{"metric": {"id": "a"}}, {"metric": {"id": "a"}}]}
            )
        )
    with check:
        engine.validate_query(
            Query.parse_obj(
                {
                    "metrics": [
                        {"metric": {"id": "a"}},
                        {"metric": {"id": "b"}, "alias": "a"},
                    ]
                }
            )
        )
    with check:
        engine.validate_query(
            Query.parse_obj(
                {
                    "metrics": [{"metric": {"id": "a"}}],
                    "dimensions": [{"dimension": {"id": "d"}, "alias": "a"}],
                }
            )
        )


def test_query_validation_missing_of_within_dimensions(engine: Engine):
    with pytest.raises(
        ValueError, match="All dimensions used in OF/WITHIN must also be present"
    ):
        engine.validate_query(
            Query.parse_obj(
                {
                    "metrics": [
                        {
                            "metric": {
                                "id": "m",
                                "transforms": [{"id": "t", "of": [{"id": "d"}]}],
                            }
                        }
                    ]
                }
            )
        )
    # correct query is correct
    engine.validate_query(
        Query.parse_obj(
            {
                "metrics": [
                    {
                        "metric": {
                            "id": "m",
                            "transforms": [{"id": "t", "of": [{"id": "d"}]}],
                        }
                    }
                ],
                "dimensions": [{"dimension": {"id": "d"}, "alias": "a"}],
            }
        )
    )
