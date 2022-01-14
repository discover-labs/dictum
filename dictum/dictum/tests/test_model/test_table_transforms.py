from dictum.engine import Engine
from dictum.model import Model
from dictum.schema import Query
from dictum.transforms.table import TopTransform


def test_top_bottom_basic(chinook: Model, engine: Engine):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [{"dimension": {"id": "genre"}}],
        }
    )
    resolved = chinook.get_resolved_query(query)
    comp = engine.get_computation(resolved)
    basic = TopTransform(2, chinook.metrics.get("revenue"))

    res = basic.transform_computation(comp)
    assert res.queries[0].limit == 2
    assert len(res.queries[0].order) == 1
    assert res.queries[0].order[0].ascending is False
