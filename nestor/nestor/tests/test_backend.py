from pandas.api.types import is_datetime64_any_dtype

from nestor.store import Store
from nestor.store.schema import Query


def test_groupby(chinook: Store, connection):
    q = Query(metrics=["track_count"], dimensions=["genre"])
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert df[df["genre"] == "Rock"].iloc[0]["track_count"] == 1297


def test_filter(chinook: Store, connection):
    q = Query(
        metrics=["items_sold"],
        filters=[
            ":genre = 'Rock'",
            ":customer_country = 'USA'",
        ],
    )
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert df.iloc[0][0] == 157


def _test_convert_datetime(chinook: Store, connection):
    """Temporarily off, because not sure if this is needed. SQLite's datetime()
    returns a string, not a datetime (unlike a raw column), but everything is sent
    as a string to the frontend anyway. Only problem is the Python API, which we don't
    have yet.
    """
    q = Query(
        metrics=["items_sold"],
        dimensions=["invoice_date"],
    )
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert is_datetime64_any_dtype(df["invoice_date"].dtype)


def test_metric_not_measure(chinook: Store, connection):
    q = Query(metrics=["revenue", "track_count", "revenue_per_track"])
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert next(df.round(2).itertuples()) == (0, 2328.6, 3503, 0.66)


def test_metric_with_groupby(chinook: Store, connection):
    q = Query(metrics=["arppu", "track_count"], dimensions=["genre"])
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert df.shape == (25, 3)


def test_multiple_facts(chinook: Store, connection):
    q = Query(metrics=["items_sold", "track_count"])
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert tuple(df.iloc[0]) == (2240, 3503)


def test_multiple_facts_dimensions(chinook: Store, connection):
    q = Query(metrics=["items_sold", "track_count"], dimensions=["genre"])
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert tuple(df[df["genre"] == "Rock"].iloc[0][["items_sold", "track_count"]]) == (
        835,
        1297,
    )


def test_if(chinook: Store, connection):
    """Test if() function and case when ... then ... else ... end constructs"""
    q = Query(metrics=["items_sold"], dimensions=["invoice_year", "leap_year"])
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert df[df["leap_year"] == "Yes"].iloc[0]["invoice_year"] == 2012


def test_subquery_join(chinook: Store, connection):
    q = Query(metrics=["items_sold"], dimensions=["customer_orders_amount"])
    comp = chinook.get_computation(q)
    df = connection.compute(comp)
    assert df.shape == (2, 2)
    assert df[df["customer_orders_amount"] == 30].iloc[0].items_sold == 1708
