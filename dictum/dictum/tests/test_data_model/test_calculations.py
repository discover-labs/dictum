from lark import Tree

from dictum.data_model import DataModel


def test_table_calculation_joins(chinook: DataModel):
    assert chinook.measures.get("revenue").joins == []
    join = chinook.measures.get("unique_paying_customers").joins[0]
    assert join.expr.children[0] == Tree(
        "eq",
        [
            Tree("column", ["invoice_items", "InvoiceId"]),
            Tree("column", ["invoice_items", "invoice", "InvoiceId"]),
        ],
    )
    assert join.alias == "invoice"

    join = chinook.dimensions.get("manager_title").joins[0]
    join.expr.children[0] == Tree(
        "eq",
        [
            Tree("column", ["employees", "ReportsTo"]),
            Tree("column", ["employees", "manager", "EmployeeId"]),
        ],
    )
    assert join.alias == "manager"


def test_dimensions_joins(chinook: DataModel):
    dimension = chinook.dimensions.get("customer_orders_amount")
    assert len(dimension.joins) == 1


def test_measure_dimensions_union(chinook: DataModel):
    assert "country" in set(
        d.id for d in chinook.measures.get("n_customers").dimensions
    )
    assert "country" in set(d.id for d in chinook.metrics.get("n_customers").dimensions)
