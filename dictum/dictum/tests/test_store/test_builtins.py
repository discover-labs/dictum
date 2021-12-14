from dictum.data_model import DataModel


def test_ge(chinook: DataModel):
    assert chinook.transforms["ge"].args == ["value"]
