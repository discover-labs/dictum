import lark

from nestor.store.schema import Config
from nestor.store.store import Store
from tests.test_store.test_schema.test_config import config_path

config = Config.from_yaml(config_path)
store = Store(config)


def test_store_loads():
    assert store.measures
    assert store.dimensions
    assert store.tables


def test_store_parses_expr():
    assert isinstance(store.measures["n_users"].expr, lark.Tree)
    assert isinstance(store.measures["n_users"].expr, lark.Tree)


def test_measure_dimensions():
    breakpoint()
