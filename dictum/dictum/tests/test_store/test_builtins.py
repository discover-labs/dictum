from dictum.store import Store


def test_ge(chinook: Store):
    assert chinook.filters["ge"].args == ["value"]
