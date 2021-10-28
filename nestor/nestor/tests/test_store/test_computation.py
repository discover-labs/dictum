from lark import Tree

from nestor.store import RelationalQuery, Store


def test_relational_query_add_dimension(chinook: Store):
    q = RelationalQuery(table=chinook.tables.get("invoice_items"))

    q.add_dimension("album")
    assert q.groupby["album"].children[0] == Tree(
        "column", ["invoice_items.track.album", "Title"]
    )
    assert q.joins[0].foreign_key == "TrackId"
    assert q.joins[0].alias == "track"
    assert q.joins[0].to.table.id == "tracks"

    assert q.joins[0].to.joins[0].foreign_key == "AlbumId"
    assert q.joins[0].to.joins[0].alias == "album"
    assert q.joins[0].to.joins[0].to.table.id == "albums"

    q.add_dimension("manager_title")
    q.groupby["manager_title"].children[0] == Tree(
        "column", ["invoice_items.invoice.customer.employee.manager", "Title"]
    )
    assert q.joins[1].foreign_key == "InvoiceId"
    assert q.joins[1].alias == "invoice"
    assert q.joins[1].to.table.id == "invoices"

    assert q.joins[1].to.joins[0].foreign_key == "CustomerId"
    assert q.joins[1].to.joins[0].alias == "customer"
    assert q.joins[1].to.joins[0].to.table.id == "customers"

    assert q.joins[1].to.joins[0].to.joins[0].foreign_key == "SupportRepId"
    assert q.joins[1].to.joins[0].to.joins[0].alias == "employee"
    assert q.joins[1].to.joins[0].to.joins[0].to.table.id == "employees"

    assert q.joins[1].to.joins[0].to.joins[0].to.joins[0].foreign_key == "ReportsTo"
    assert q.joins[1].to.joins[0].to.joins[0].to.joins[0].alias == "manager"
    assert q.joins[1].to.joins[0].to.joins[0].to.joins[0].to.table.id == "employees"


def test_relational_query_measure_dimension(chinook: Store):
    q = chinook.get_relational_query(
        measures=["items_sold"], dimensions=["customer_orders_amount"]
    )
    joins = list(q._unnested_joins())
    assert len(joins) == 3
    assert joins[-1].right.subquery
