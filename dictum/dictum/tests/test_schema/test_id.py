import pytest
from pydantic import BaseModel, ValidationError

from dictum.schema.id import ID


class ModelTest(BaseModel):
    id: ID


def test_id_type():
    with pytest.raises(ValidationError, match="must be a string"):
        ModelTest(id=0)


def test_id_identifier():
    with pytest.raises(ValidationError, match="must be a valid Python identifier"):
        ModelTest(id="blah blah")


def test_id_double_underscore():
    with pytest.raises(ValidationError, match="double underscore"):
        ModelTest(id="__blah")


def test_id_uppercase():
    with pytest.raises(ValidationError, match="are reserved"):
        ModelTest(id="Month")


def test_id_ok():
    ModelTest(id="valid_id")
