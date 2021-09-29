from nestor.backends.sql_alchemy import SQLAlchemyConnection
from nestor.store import Store
from nestor.store.schema import Query


def test_sqla(chinook: Store):
    conn = SQLAlchemyConnection(
        drivername="sqlite", database="../../baguette-bi/chinook.db"
    )
    q = Query(
        measures=["track_count"],
        dimensions=["track_length_10s_bins"],
    )
    comp = chinook.execute_query(q)
    df = conn.execute(comp)
    breakpoint()
