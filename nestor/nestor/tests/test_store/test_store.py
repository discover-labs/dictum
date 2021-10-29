import pytest
from lark import Tree

from nestor.store.schema import Query
from nestor.store.store import Store


@pytest.fixture(scope="module")
def store(store_full):
    return store_full


def test_store_loads(chinook: Store):
    assert chinook.metrics
    assert chinook.measures
    assert chinook.dimensions
    assert chinook.tables


def test_store_parses_expr(chinook: Store):
    assert isinstance(chinook.measures["revenue"].expr, Tree)
    assert isinstance(chinook.dimensions["leap_year"].expr, Tree)
    assert isinstance(chinook.metrics["revenue_per_track"].expr, Tree)


def test_store_measure_related_column(chinook: Store):
    comp = chinook.get_computation(Query(metrics=["unique_paying_customers"]))
    assert len(comp.queries[0].joins) == 1


def test_suggest_metrics_no_dims(chinook: Store):
    metrics = chinook.suggest_metrics(Query(metrics=["track_count"]))
    assert len(metrics) == 11

    metrics = chinook.suggest_metrics(Query(metrics=["track_count", "revenue"]))
    assert len(metrics) == 10


def test_suggest_metrics_with_dims(chinook: Store):
    metrics = chinook.suggest_metrics(
        Query(metrics=["revenue"], dimensions=["customer_country"])
    )
    assert set(m.id for m in metrics) == {
        "arppu",
        "unique_paying_customers",
        "items_sold",
        "avg_sold_unit_price",
        "n_customers",
    }

    metrics = chinook.suggest_metrics(Query(metrics=["revenue"], dimensions=["genre"]))
    assert len(metrics) == 9


def test_suggest_dimensions(chinook: Store):
    dimensions = chinook.suggest_dimensions(
        Query(
            metrics=["track_count", "revenue"],
            dimensions=["album"],
        )
    )
    assert set(d.id for d in dimensions) == {
        "genre",
        "artist",
        "track_length_10s_bins",
        "media_type",
    }


def test_suggest_metrics_with_union(chinook: Store):
    metrics = chinook.suggest_metrics(
        Query(metrics=["n_customers"], dimensions=["country"])
    )
    assert metrics[0].id == "n_employees"


def test_suggest_dimensions_with_union(chinook: Store):
    dimensions = chinook.suggest_dimensions(
        Query(metrics=["n_customers"], dimensions=["country"])
    )
    assert len(dimensions) == 9


def test_dimension_same_table_as_measures(chinook: Store):
    """There was a bug where the table couldn't find a join path from a self to
    a dimension declared on self :-/
    """
    assert (
        chinook.tables["tracks"].dimension_join_paths.get("track_length_10s_bins")
        is not None
    )


def test_resolve_metrics(chinook: Store):
    assert chinook.metrics.get("revenue_per_track").expr.children[0] == Tree(
        "div",
        [
            Tree("measure", ["revenue"]),
            Tree("measure", ["track_count"]),
        ],
    )


def test_compute_union(chinook: Store):
    q = Query(metrics=["n_customers", "n_employees"], dimensions=["country"])
    comp = chinook.get_computation(q)
    for query in comp.queries:
        assert list(query.groupby)[0] == "country"


def test_union_allowed_dimensions(chinook: Store):
    table = chinook.tables.get("invoice_items")
    assert "country" not in table.allowed_dimensions
    assert "customer_country" in table.allowed_dimensions
    assert "employee_country" in table.allowed_dimensions
