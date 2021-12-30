from lark import Tree
from toolz import identity

from dictum.data_model import AggregateQuery, DataModel
from dictum.schema import Query, QueryDimensionRequest


def test_relational_query_add_dimension(chinook: DataModel):
    query = AggregateQuery(table=chinook.tables.get("invoice_items"))

    query.add_dimension("album", "album", identity)
    assert query.groupby[0].expr.children[0] == Tree(
        "column", ["invoice_items", "track", "album", "Title"]
    )
    assert query.joins[0].expr.children[0] == Tree(
        "eq",
        [
            Tree("column", ["invoice_items", "TrackId"]),
            Tree("column", ["invoice_items", "track", "TrackId"]),
        ],
    )
    assert query.joins[0].alias == "track"
    assert query.joins[0].to.table.id == "tracks"

    assert query.joins[0].to.joins[0].expr.children[0] == Tree(
        "eq",
        [
            Tree("column", ["tracks", "AlbumId"]),
            Tree("column", ["tracks", "album", "AlbumId"]),
        ],
    )
    assert query.joins[0].to.joins[0].alias == "album"
    assert query.joins[0].to.joins[0].to.table.id == "albums"

    query.add_dimension("manager_title", "manager_title", identity)
    query.groupby[1].expr.children[0] == Tree(
        "column",
        ["invoice_items", "invoice", "customer", "employee", "manager", "Title"],
    )
    assert query.joins[1].expr.children[0] == Tree(
        "eq",
        [
            Tree("column", ["invoice_items", "InvoiceId"]),
            Tree("column", ["invoice_items", "invoice", "InvoiceId"]),
        ],
    )
    assert query.joins[1].alias == "invoice"
    assert query.joins[1].to.table.id == "invoices"

    assert query.joins[1].to.joins[0].expr.children[0] == Tree(
        "eq",
        [
            Tree("column", ["invoices", "CustomerId"]),
            Tree("column", ["invoices", "customer", "CustomerId"]),
        ],
    )
    assert query.joins[1].to.joins[0].alias == "customer"
    assert query.joins[1].to.joins[0].to.table.id == "customers"

    assert query.joins[1].to.joins[0].to.joins[0].expr.children[0] == Tree(
        "eq",
        [
            Tree("column", ["customers", "SupportRepId"]),
            Tree("column", ["customers", "employee", "EmployeeId"]),
        ],
    )
    assert query.joins[1].to.joins[0].to.joins[0].alias == "employee"
    assert query.joins[1].to.joins[0].to.joins[0].to.table.id == "employees"

    assert query.joins[1].to.joins[0].to.joins[0].to.joins[0].expr.children[0] == Tree(
        "eq",
        [
            Tree("column", ["employees", "ReportsTo"]),
            Tree("column", ["employees", "manager", "EmployeeId"]),
        ],
    )
    assert query.joins[1].to.joins[0].to.joins[0].to.joins[0].alias == "manager"
    assert query.joins[1].to.joins[0].to.joins[0].to.joins[0].to.table.id == "employees"


def test_relational_query_measure_dimension(chinook: DataModel):
    q = chinook.get_aggregate_query(
        measures=["items_sold"],
        dimensions=[
            QueryDimensionRequest.parse_obj(
                {"dimension": {"id": "customer_orders_amount"}}
            )
        ],
    )
    joins = list(q._unnested_joins())
    assert len(joins) == 3
    assert joins[-1].right.subquery


def test_unique_joins(chinook: DataModel):
    comp = chinook.get_computation(
        query=Query.parse_obj(
            {
                "metrics": [
                    {"metric": {"id": "revenue"}},
                    {"metric": {"id": "unique_paying_customers"}},
                    {"metric": {"id": "arppu"}},
                ],
                "dimensions": [{"dimension": {"id": "invoice_date"}}],
            }
        )
    )
    assert len(comp.queries[0].unnested_joins) == 1
