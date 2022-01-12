import pytest

from dictum.engine import Computation, Engine, RelationalQuery
from dictum.model import DimensionsUnion, Model
from dictum.schema import Query


@pytest.fixture(scope="module")
def engine():
    return Engine()


def test_aggregate_simple_measure(engine: Engine, chinook: Model):
    query = Query.parse_obj({"metrics": [{"metric": {"id": "revenue"}}]})
    resolved = chinook.get_resolved_query(query)
    res = engine.get_computation(resolved).queries[0]
    assert isinstance(res, RelationalQuery)
    assert res.source.id == "invoice_items"
    assert len(res.columns) == 1
    assert res.columns[0].name == "revenue"
    assert res.joins == []
    assert res.filters == []
    assert res.groupby == []
    assert res.order == []
    assert res.limit is None


def test_aggregate_measure_dimension(engine: Engine, chinook: Model):
    query = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "revenue"}},
                {"metric": {"id": "unique_paying_customers"}},
            ],
            "dimensions": [{"dimension": {"id": "genre"}}],
        }
    )
    resolved = chinook.get_resolved_query(query)
    res = engine.get_computation(resolved).queries[0]
    assert isinstance(res, RelationalQuery)
    assert len(res.unnested_joins) == 3
    assert len(res.joins) == 2
    assert len(res.columns) == 3
    assert len(res.groupby) == 1


def test_aggregate_aggregate_dimension(engine: Engine, chinook: Model):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [{"dimension": {"id": "customer_orders_amount"}}],
        }
    )
    resolved = chinook.get_resolved_query(query)
    res = engine.get_computation(resolved).queries[0]
    assert len(res.unnested_joins) == 3
    assert isinstance(res.unnested_joins[-1].right, RelationalQuery)  # a subquery


def test_merged_query_no_dimensions(engine: Engine, chinook: Model):
    query = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "revenue"}},
                {"metric": {"id": "track_count"}},
            ]
        }
    )
    resolved = chinook.get_resolved_query(query)
    res = engine.get_computation(resolved)
    assert isinstance(res, Computation)
    assert len(res.queries) == 2
    assert res.queries[0].source.id == "invoice_items"
    assert res.queries[1].source.id == "tracks"
    assert res.merge_on == []
    assert len(res.columns) == 2


def test_merged_query_with_dimensions(engine: Engine, chinook: Model):
    query = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "revenue"}},
                {"metric": {"id": "track_count"}},
            ],
            "dimensions": [
                {"dimension": {"id": "genre"}},
            ],
        }
    )
    resolved = chinook.get_resolved_query(query)
    res = engine.get_computation(resolved)
    assert isinstance(res, Computation)
    assert len(res.queries) == 2
    assert res.queries[0].source.id == "invoice_items"
    assert res.queries[1].source.id == "tracks"
    assert res.merge_on == ["genre"]
    assert len(res.columns) == 3


@pytest.mark.skip
def test_store_measure_related_column(chinook: Model):
    q = Query.parse_obj({"metrics": [{"metric": {"id": "unique_paying_customers"}}]})
    comp = chinook.get_computation(q)
    assert len(comp.queries[0].joins) == 1


@pytest.mark.skip
def test_suggest_metrics_no_dims(chinook: Model):
    q = Query.parse_obj({"metrics": [{"metric": {"id": "track_count"}}]})
    metrics = chinook.suggest_metrics(q)
    assert len(metrics) == 12

    q = Query.parse_obj(
        {"metrics": [{"metric": {"id": "track_count"}}, {"metric": {"id": "revenue"}}]}
    )
    metrics = chinook.suggest_metrics(q)
    assert len(metrics) == 12


@pytest.mark.skip
def test_suggest_metrics_with_dims(chinook: Model):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [{"dimension": {"id": "customer_country"}}],
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
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [{"dimension": {"id": "genre"}}],
        }
    )
    metrics = chinook.suggest_metrics(q)
    assert len(metrics) == 10


@pytest.mark.skip
def test_suggest_dimensions(chinook: Model):
    q = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "track_count"}},
                {"metric": {"id": "revenue"}},
            ],
            "dimensions": [{"dimension": {"id": "album"}}],
        }
    )
    dimensions = chinook.suggest_dimensions(q)
    assert set(d.id for d in dimensions) == {
        "genre",
        "artist",
        "track_length_10s_bins",
        "media_type",
    }


@pytest.mark.skip
def test_suggest_metrics_with_union(chinook: Model):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "n_customers"}}],
            "dimensions": [{"dimension": {"id": "country"}}],
        }
    )
    metrics = chinook.suggest_metrics(q)
    assert metrics[0].id == "n_customers"
    assert metrics[1].id == "n_employees"


@pytest.mark.skip
def test_suggest_dimensions_with_union(chinook: Model):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "n_customers"}}],
            "dimensions": [{"dimension": {"id": "country"}}],
        }
    )
    dimensions = chinook.suggest_dimensions(q)
    assert len(dimensions) == 11


@pytest.mark.skip
def test_compute_union(chinook: Model):
    q = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "n_customers"}},
                {"metric": {"id": "n_employees"}},
            ],
            "dimensions": [{"dimension": {"id": "country"}}],
        }
    )
    comp = chinook.get_computation(q)
    for query in comp.queries:
        assert query.groupby[0].name == "country"


@pytest.mark.skip
def test_alias(chinook: Model):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [
                {
                    "dimension": {
                        "id": "invoice_date",
                        "transforms": [{"id": "datepart", "args": ["year"]}],
                    },
                    "alias": "year",
                },
                {
                    "dimension": {
                        "id": "invoice_date",
                        "transforms": [{"id": "datepart", "args": ["month"]}],
                    },
                    "alias": "month",
                },
            ],
        }
    )
    comp = chinook.get_computation(q)
    assert comp.columns[0].name == "year"
    assert comp.columns[1].name == "month"


@pytest.mark.skip
def test_missing_join_for_aggregate_dimension(chinook: Model):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "items_sold"}}],
            "dimensions": [
                {"dimension": {"id": "customer_country"}},
                {"dimension": {"id": "first_order_cohort_month"}},
            ],
        }
    )
    comp = chinook.get_computation(q)
    assert len(comp.queries[0].unnested_joins) == 3


@pytest.mark.skip
def test_transform_order(chinook: Model):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [
                {
                    "dimension": {
                        "id": "invoice_date",
                        "transforms": [{"id": "year"}, {"id": "gt", "args": [0]}],
                    },
                }
            ],
        }
    )
    comp = chinook.get_computation(q)
    assert comp.queries[0].groupby[0].expr.children[0] == Tree(
        "gt",
        [
            Tree(
                "call",
                [
                    "datepart",
                    Token("STRING", "year"),
                    Tree("column", ["invoice_items.invoice", "InvoiceDate"]),
                ],
            ),
            Token("INTEGER", "0"),
        ],
    )


@pytest.mark.skip
def test_metric_transform(chinook: Model):
    query = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "revenue"}},
                {"metric": {"id": "revenue", "transforms": [{"id": "sum"}]}},
            ],
            "dimensions": [{"dimension": {"id": "genre"}}],
        }
    )
    comp = chinook.get_computation(query)
    assert comp.columns[2].expr == Tree(
        "expr",
        [
            Tree(
                "call_window",
                [
                    "sum",
                    Tree(
                        "call",
                        [
                            "coalesce",
                            Tree("column", [None, "revenue"]),
                            Token("INTEGER", "0"),
                        ],
                    ),
                    Tree("partition_by", []),
                    None,
                    None,
                ],
            )
        ],
    )
