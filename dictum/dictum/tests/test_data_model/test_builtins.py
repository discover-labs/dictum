from dictum.data_model import DataModel


def test_ge(chinook: DataModel):
    assert chinook.scalar_transforms["ge"].args == ["value"]
