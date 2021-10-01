import pytest

from nestor.backends.sql_alchemy import SQLAlchemyConnection
from nestor.store import Store
from nestor.store.schema import Query


@pytest.fixture(scope="module")
def conn(chinook_db):
    return SQLAlchemyConnection(drivername="sqlite", database=chinook_db)


def test_sqla(chinook: Store, conn):
    q = Query(measures=["track_count"], dimensions=["genre"])
    comp = chinook.execute_query(q)
    df = conn.execute(comp)
    assert df[df["genre"] == "Rock"].iloc[0]["track_count"] == 1297


def test_filter(chinook: Store, conn):
    q = Query(
        measures=["items_sold"],
        filters=[
            ":genre = 'Rock'",
            ":customer_country = 'USA'",
        ],
    )
    comp = chinook.execute_query(q)
    df = conn.execute(comp)
    assert df.iloc[0][0] == 157
