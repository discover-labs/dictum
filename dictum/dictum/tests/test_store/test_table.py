from dictum.store import Store


def test_table_find_all_paths_chinook(chinook: Store):
    paths = chinook.tables["invoice_items"].find_all_paths()
    assert len(paths) == 8


def test_table_allowed_join_paths(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert len(table.allowed_join_paths) == 8


def test_table_allowed_dimensions(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert "artist" in table.allowed_dimensions
    assert "customer_country" in table.allowed_dimensions


def test_table_allowed_dimensions_union(chinook: Store):
    assert "country" not in chinook.tables.get("invoice_items").allowed_dimensions
    assert "country" in chinook.tables.get("customers").allowed_dimensions
