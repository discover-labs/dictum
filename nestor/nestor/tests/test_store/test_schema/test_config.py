from nestor.store.schema.config import Calculation, Table


def test_calculation_format():
    """Test that a shorthand for the format (just a str) is replaced with a
    CalculationFormat object.
    """
    calc = Calculation.parse_obj(
        {"id": "test", "name": "name", "expr": "expr", "format": ".0f"}
    )
    assert calc.format.spec == ".0f"


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
            "dimensions": {"test": {"name": "test", "expr": "expr", "type": "time"}},
        }
    )
    table.dimensions["test"].id == "test"
