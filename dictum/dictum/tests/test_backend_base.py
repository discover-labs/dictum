from unittest import mock

import pytest

from dictum.backends.base import ExpressionTransformer
from dictum.backends.sql_alchemy import SQLAlchemyBackend


@pytest.fixture(scope="module", autouse=True)
def patch_sqlalchemy_url():
    with mock.patch("dictum.backends.sql_alchemy.SQLAlchemyBackend.url", "sqlite://"):
        yield


def test_compiler_case():
    compiler = mock.MagicMock()
    transformer = ExpressionTransformer(compiler)
    transformer.case([1, 2, 3, 4])
    compiler.case.assert_called_once_with([[1, 2], [3, 4]], else_=None)

    transformer.case([1, 2, 3, 4, 5])
    compiler.case.assert_called_with([[1, 2], [3, 4]], else_=5)


def test_sqlalchemy_no_default_schema():
    backend = SQLAlchemyBackend()
    with mock.patch("dictum.backends.sql_alchemy.Table") as Table:
        backend.table("table")
        assert Table.call_args[1]["schema"] is None


def test_sqlalchemy_default_schema():
    backend = SQLAlchemyBackend(default_schema="test")
    with mock.patch("dictum.backends.sql_alchemy.Table") as Table:
        backend.table("table")
        assert Table.call_args[1]["schema"] == "test"


def test_sqlalchemy_override_default_schema():
    backend = SQLAlchemyBackend(default_schema="test")
    with mock.patch("dictum.backends.sql_alchemy.Table") as Table:
        backend.table("table", schema="override")
        assert Table.call_args[1]["schema"] == "override"
