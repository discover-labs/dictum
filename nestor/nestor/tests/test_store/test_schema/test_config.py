from nestor.store.schema.config import Calculation


def test_calculation_format():
    """Test that a shorthand for the format (just a str) is replaced with a
    CalculationFormat object.
    """
    calc = Calculation.parse_obj({"name": "name", "expr": "expr", "format": ".0f"})
    assert calc.format.spec == ".0f"
