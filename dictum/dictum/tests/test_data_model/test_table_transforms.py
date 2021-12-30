from dictum.data_model import DataModel
from dictum.data_model.transforms.table import TopBottomTransform
from dictum.schema import Query


def test_top_bottom_basic(chinook: DataModel):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [{"dimension": {"id": "genre"}}],
        }
    )
    comp = chinook.get_computation(query)
    basic = TopBottomTransform(2, False, chinook.metrics.get("revenue"))

    res = basic.transform_computation(comp)
    assert res.queries[0].limit == 2
    assert len(res.queries[0].order) == 1
    assert res.queries[0].order[0].ascending is False
