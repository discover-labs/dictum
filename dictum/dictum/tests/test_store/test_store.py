import pytest
from lark import Token, Tree

from dictum.store.schema import Query
from dictum.store.store import AggregateQuery, Store


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
    q = Query.parse_obj({"metrics": [{"metric": "unique_paying_customers"}]})
    comp = chinook.get_computation(q)
    assert len(comp.queries[0].joins) == 1


def test_suggest_metrics_no_dims(chinook: Store):
    q = Query.parse_obj({"metrics": [{"metric": "track_count"}]})
    metrics = chinook.suggest_metrics(q)
    assert len(metrics) == 12

    q = Query.parse_obj({"metrics": [{"metric": "track_count"}, {"metric": "revenue"}]})
    metrics = chinook.suggest_metrics(q)
    assert len(metrics) == 12


def test_suggest_metrics_with_dims(chinook: Store):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}],
            "dimensions": [{"dimension": "customer_country"}],
        }
    )
    metrics = chinook.suggest_metrics(q)
    assert set(m.id for m in metrics) == {
        "revenue",
        "arppu",
        "unique_paying_customers",
        "items_sold",
        "avg_sold_unit_price",
        "n_customers",
    }

    q = Query.parse_obj(
        {"metrics": [{"metric": "revenue"}], "dimensions": [{"dimension": "genre"}]}
    )
    metrics = chinook.suggest_metrics(q)
    assert len(metrics) == 10


def test_suggest_dimensions(chinook: Store):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "track_count"}, {"metric": "revenue"}],
            "dimensions": [{"dimension": "album"}],
        }
    )
    dimensions = chinook.suggest_dimensions(q)
    assert set(d.id for d in dimensions) == {
        "genre",
        "artist",
        "track_length_10s_bins",
        "media_type",
    }


def test_suggest_metrics_with_union(chinook: Store):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "n_customers"}],
            "dimensions": [{"dimension": "country"}],
        }
    )
    metrics = chinook.suggest_metrics(q)
    assert metrics[0].id == "n_customers"
    assert metrics[1].id == "n_employees"


def test_suggest_dimensions_with_union(chinook: Store):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "n_customers"}],
            "dimensions": [{"dimension": "country"}],
        }
    )
    dimensions = chinook.suggest_dimensions(q)
    assert len(dimensions) == 10


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
        "div", [Tree("measure", ["revenue"]), Tree("measure", ["track_count"])]
    )


def test_compute_union(chinook: Store):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "n_customers"}, {"metric": "n_employees"}],
            "dimensions": [{"dimension": "country"}],
        }
    )
    comp = chinook.get_computation(q)
    for query in comp.queries:
        assert query.groupby[0].name == "country"


def test_union_allowed_dimensions(chinook: Store):
    table = chinook.tables.get("invoice_items")
    assert "country" not in table.allowed_dimensions
    assert "customer_country" in table.allowed_dimensions
    assert "employee_country" in table.allowed_dimensions


def test_aggregate_dimension_related_subquery(chinook: Store):
    related = chinook.tables.get("customers").related
    key = "__subquery__revenue"
    assert key in related
    assert isinstance(related[key].table, AggregateQuery)
    assert related[key].table.subquery


def test_resolve_aggregate_dimension(chinook: Store):
    assert chinook.dimensions.get("customer_orders_amount").expr.children[0] == Tree(
        "column", ["customers", "__subquery__revenue", "revenue"]
    )


def test_resolve_related_dimension(chinook: Store):
    assert chinook.dimensions.get("order_customer_country").expr.children[0] == Tree(
        "column", ["invoice_items", "invoice", "customer", "Country"]
    )


def test_resolve_dimension_on_anchor(chinook: Store):
    assert chinook.dimensions.get("genre").expr.children[0] == Tree(
        "column", ["genres", "Name"]
    )


def test_resolve_related_aggregate_dimension(chinook: Store):
    assert chinook.dimensions.get("first_order_cohort_month").expr.children[0] == Tree(
        "call",
        [
            "datediff",
            Token("STRING", "month"),
            Tree(
                "column",
                [
                    "invoice_items",
                    "invoice",
                    "customer",
                    "__subquery__min_sale_date",
                    "min_sale_date",
                ],
            ),
            Tree("column", ["invoice_items", "invoice", "InvoiceDate"]),
        ],
    )


def test_inject_default_filters_and_transforms(chinook: Store):
    assert len(chinook.transforms) == 10
    assert len(chinook.filters) == 5


def test_query_defaults(chinook: Store):
    defaults = chinook.dimensions.get("invoice_date").query_defaults
    assert defaults.filter.id == "last"
    assert defaults.filter.args == [30, "day"]
    assert defaults.transform.id == "datetrunc"
    assert defaults.transform.args == ["day"]


def test_metric_missing(chinook: Store):
    assert chinook.metrics.get("revenue").expr.children[0] == Tree(
        "call", ["coalesce", Tree("measure", ["revenue"]), Token("INTEGER", 0)]
    )


def test_transform_compile(chinook: Store):
    assert chinook.transforms.get("datepart").compile(
        Tree("column", ["dt"]), ["year"]
    ) == Tree("call", ["datepart", "year", Tree("column", ["dt"])])
