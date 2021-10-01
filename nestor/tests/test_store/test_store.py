import pytest
from lark import Tree

from nestor.store.store import Store


@pytest.fixture(scope="module")
def store(store_full):
    return store_full


def test_store_loads(store: Store):
    assert store.measures
    assert store.dimensions
    assert store.tables


def test_store_parses_expr(store: Store):
    assert isinstance(store.measures["n_users"].expr, Tree)
    assert isinstance(store.measures["n_users"].expr, Tree)


def test_table_find_all_paths_chinook(chinook: Store):
    paths = chinook.tables["invoice_items"].find_all_paths()
    assert len(paths) == 8


def test_table_paths_store(store: Store):
    table = store.tables["orders"]
    assert len(table.find_all_paths()) == 3
    assert len(table.allowed_join_paths) == 1


def test_table_get_join_path(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert table.get_join_path("artists") == [
        "invoice_items",
        "tracks",
        "albums",
        "artists",
    ]
    assert table.get_join_path("customers") == [
        "invoice_items",
        "invoices",
        "customers",
    ]
    assert table.get_join_path("employees") == [
        "invoice_items",
        "invoices",
        "customers",
        "employees",
    ]


def test_table_allowed_dimensions(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert "artist" in table.allowed_dimensions
    assert "customer_country" in table.allowed_dimensions


def test_table_get_join_path_self(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert len(table.get_join_path(table.id)) == 1


def test_table_get_dimension(chinook: Store):
    table = chinook.tables["invoice_items"]
    tree, paths = table.get_dimension_expr_and_paths("manager_name")
    assert tree.children[0] == Tree(
        "column", ["invoice_items.invoices.customers.employees.manager", "LastName"]
    )
    assert paths[1] == [
        "invoice_items",
        "invoices",
        "customers",
        "employees",
        "manager",
    ]


def test_table_get_dimension_ambiguous(store: Store):
    table = store.tables["orders"]
    tree, paths = table.get_dimension_expr_and_paths("user_channel")
    assert tree.children[0] == Tree("column", ["orders.users.attributions", "channel"])
    assert paths[1] == ["orders", "users", "attributions"]
