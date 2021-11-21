from dictum.store.schema.config import Calculation, Table


def test_set_related_ids():
    table = Table.parse_obj(
        {
            "id": "test",
            "source": "test",
            "related": {"test": {"table": "test", "foreign_key": "test"}},
        }
    )
    table.related["test"].alias == "test"


def test_set_measures_ids():
    table = Table.parse_obj(
        {
            "id": "test",
            "source": "test",
            "measures": {"test": {"name": "test", "expr": "test"}},
        }
    )
    table.measures["test"].id == "test"


def test_set_dimensions_ids():
    table = Table.parse_obj(
        {
            "id": "test",
            "source": "test",
            "dimensions": {
                "test": {"name": "test", "expr": "expr", "type": "datetime"}
            },
        }
    )
    table.dimensions["test"].id == "test"


def test_expr_alias():
    calc = Calculation.parse_obj(
        {"id": "test", "name": "test", "type": "number", "expr": "str_expr"}
    )
    assert calc.str_expr == "str_expr"
