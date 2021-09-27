import lark
import pytest

from nestor.store.schema import Query
from nestor.store.store import Store


@pytest.fixture(scope="module")
def store(store_full):
    return store_full


def test_store_loads(store: Store):
    assert store.measures
    assert store.dimensions
    assert store.tables


def test_store_parses_expr(store: Store):
    assert isinstance(store.measures["n_users"].expr, lark.Tree)
    assert isinstance(store.measures["n_users"].expr, lark.Tree)


def test_execute_query(store: Store):
    q = Query(
        measures=["arppu"],
        dimensions=[
            "user_channel",
            "user_referrer_channel",
            "user_creator_channel",
            "order_channel",
        ],
    )
    store.execute_query(q)
