from nestor.store.schema.query import QueryTranformRequest


def test_parse_query_dimension_transform():
    q = QueryTranformRequest.parse("inrange(1, 10)")
    assert q.id == "inrange"
    assert q.args == [1, 10]
