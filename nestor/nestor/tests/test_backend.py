from pandas.api.types import is_datetime64_any_dtype

from nestor.store import Store
from nestor.store.schema import Query


def test_measure_groupby(chinook: Store, connection):
    q = Query(measures=["track_count"], dimensions=["genre"])
    comp = chinook.execute_query(q)
    df = connection.execute(comp)
    assert df[df["genre"] == "Rock"].iloc[0]["track_count"] == 1297


def test_filter(chinook: Store, connection):
    q = Query(
        measures=["items_sold"],
        filters=[
            ":genre = 'Rock'",
            ":customer_country = 'USA'",
        ],
    )
    comp = chinook.execute_query(q)
    df = connection.execute(comp)
    assert df.iloc[0][0] == 157


def test_convert_datetime(chinook: Store, connection):
    q = Query(
        measures=["items_sold"],
        dimensions=["invoice_date"],
    )
    comp = chinook.execute_query(q)
    df = connection.execute(comp)
    assert is_datetime64_any_dtype(df["invoice_date"].dtype)
