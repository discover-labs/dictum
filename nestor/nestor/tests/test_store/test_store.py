import pytest
from lark import Tree

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


def test_store_measure_related_column(chinook: Store, connection):
    comp = chinook.execute_query(Query(measures=["unique_paying_customers"]))
    assert len(comp.queries[0].join_tree.joins) == 1
    df = connection.execute(comp)
    assert df.iloc[0, 0] == 59


def test_get_fact_tables(chinook: Store):
    facts = chinook.get_fact_tables(Query(measures=["track_count"]))
    assert len(facts) == 1
    assert facts[0].join_tree.table.id == "tracks"

    facts = chinook.get_fact_tables(Query(measures=["track_count", "revenue"]))
    assert len(facts) == 2
    assert facts[1].join_tree.table.id == "invoice_items"


def test_get_fact_tables_with_dimensions(chinook: Store):
    facts = chinook.get_fact_tables(
        Query(measures=["track_count"], dimensions=["artist"])
    )
    assert len(facts) == 1
    assert len(facts[0].groupby) == 1
    assert len(list(facts[0].join_tree.unnested_joins)) == 2

    facts = chinook.get_fact_tables(
        Query(measures=["track_count", "revenue"], dimensions=["artist"])
    )
    assert len(facts) == 2
    assert len(facts[0].groupby) == 1
    assert len(list(facts[0].join_tree.unnested_joins)) == 2
    assert len(list(facts[1].join_tree.unnested_joins)) == 3


def test_get_fact_tables_with_filters(chinook: Store):
    facts = chinook.get_fact_tables(
        Query(
            measures=["track_count", "revenue"],
            dimensions=["artist"],
            filters=[":genre = 'Rock'"],
        )
    )
    for fact in facts:
        assert len(fact.filters) == 1


def test_suggest_measures_no_dims(chinook: Store):
    measures = chinook.suggest_measures(Query(measures=["track_count"]))
    assert len(measures) == 8

    measures = chinook.suggest_measures(Query(measures=["track_count", "revenue"]))
    assert len(measures) == 7


def test_suggest_measures_with_dims(chinook: Store):
    measures = chinook.suggest_measures(
        Query(measures=["revenue"], dimensions=["customer_country"])
    )
    assert set(m.id for m in measures) == {
        "arppu",
        "unique_paying_customers",
        "items_sold",
        "avg_sold_unit_price",
    }

    measures = chinook.suggest_measures(
        Query(measures=["revenue"], dimensions=["genre"])
    )
    assert len(measures) == 8


def test_suggest_dimensions(chinook: Store):
    dimensions = chinook.suggest_dimensions(
        Query(
            measures=["track_count", "revenue"],
            dimensions=["album"],
        )
    )
    assert set(d.id for d in dimensions) == {
        "genre",
        "artist",
        "track_length_10s_bins",
        "media_type",
    }


def test_dimension_same_table_as_measures(chinook: Store, connection):
    """There was a bug where the table couldn't find a join path from a self to
    a dimension declared on self :-/
    """
    assert (
        chinook.tables["tracks"].dimension_join_paths.get("track_length_10s_bins")
        is not None
    )
