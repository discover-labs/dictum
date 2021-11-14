from dictum.store.schema.query import QueryDimensionTransform


def test_parse_query_dimension_transform():
    q = QueryDimensionTransform.parse("inrange(1, 10)")
    assert q.id == "inrange"
    assert q.args == [1, 10]
