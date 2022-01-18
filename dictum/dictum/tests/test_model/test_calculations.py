from dictum.model import Model


def test_measure_dimensions_union(chinook: Model):
    assert "country" in set(
        d.id for d in chinook.measures.get("n_customers").dimensions
    )
    assert "country" in set(d.id for d in chinook.metrics.get("n_customers").dimensions)
