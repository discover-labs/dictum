from nestor.store import Store


def test_table_calculation_joins(chinook: Store):
    assert chinook.measures.get("revenue").joins == []
    join = chinook.measures.get("unique_paying_customers").joins[0]
    assert join.foreign_key == "InvoiceId"
    assert join.alias == "invoice"

    join = chinook.dimensions.get("manager_title").joins[0]
    assert join.foreign_key == "ReportsTo"
    assert join.alias == "manager"


def test_dimensions_joins(chinook: Store):
    dimension = chinook.dimensions.get("customer_orders_amount")
    assert len(dimension.joins) == 1
