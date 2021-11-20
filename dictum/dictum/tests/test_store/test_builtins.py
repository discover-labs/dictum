from dictum.store import Store


def test_atleast(chinook: Store):
    assert chinook.filters["atleast"].args == ["value"]
