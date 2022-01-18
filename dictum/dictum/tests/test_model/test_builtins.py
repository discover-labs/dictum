from dictum.model import Model


def test_ge(chinook: Model):
    assert chinook.scalar_transforms["ge"].args == ["value"]
