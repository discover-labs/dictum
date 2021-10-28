from nestor.store import Store


def test_table_find_all_paths_chinook(chinook: Store):
    paths = chinook.tables["invoice_items"].find_all_paths()
    assert len(paths) == 8


def test_table_allowed_join_paths(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert len(table.allowed_join_paths) == 8


def test_table_get_join_path(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert table.get_join_path("artists") == [
        "invoice_items",
        "track",
        "album",
        "artist",
    ]
    assert table.get_join_path("customers") == [
        "invoice_items",
        "invoice",
        "customer",
    ]
    assert table.get_join_path("employees") == [
        "invoice_items",
        "invoice",
        "customer",
        "employee",
    ]


def test_table_allowed_dimensions(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert "artist" in table.allowed_dimensions
    assert "customer_country" in table.allowed_dimensions


def test_table_get_join_path_self(chinook: Store):
    table = chinook.tables["invoice_items"]
    assert len(table.get_join_path(table.id)) == 1
