import datetime

import pytest
from pandas.api.types import is_datetime64_any_dtype

from dictum.backends.base import BackendResult
from dictum.store import AggregateQuery, ColumnCalculation, Computation, Store
from dictum.store.expr.parser import parse_expr
from dictum.store.schema import Query


def test_groupby(chinook: Store, connection):
    q = Query.parse_obj(
        {"metrics": [{"metric": "track_count"}], "dimensions": [{"dimension": "genre"}]}
    )
    comp = chinook.get_computation(q)
    df = connection.compute_df(comp)
    assert df[df["genre"] == "Rock"].iloc[0]["track_count"] == 1297


def test_filter(chinook: Store, connection):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "items_sold"}],
            "filters": [
                {"dimension": "genre", "filter": {"id": "in", "args": ["Rock"]}},
                {
                    "dimension": "customer_country",
                    "filter": {"id": "in", "args": ["USA"]},
                },
            ],
        }
    )
    comp = chinook.get_computation(q)
    df = connection.compute_df(comp)
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
    q = Query.parse_obj(
        {
            "metrics": [
                {"metric": "revenue"},
                {"metric": "track_count"},
                {"metric": "revenue_per_track"},
            ]
        }
    )
    comp = chinook.get_computation(q)
    df = connection.compute_df(comp)
    assert next(df.round(2).itertuples()) == (0, 2328.6, 3503, 0.66)


def test_metric_with_groupby(chinook: Store, connection):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "arppu"}, {"metric": "track_count"}],
            "dimensions": [{"dimension": "genre"}],
        }
    )
    comp = chinook.get_computation(q)
    df = connection.compute_df(comp)
    assert df.shape == (25, 3)


def test_multiple_facts(chinook: Store, connection):
    q = Query.parse_obj(
        {"metrics": [{"metric": "items_sold"}, {"metric": "track_count"}]}
    )
    comp = chinook.get_computation(q)
    df = connection.compute_df(comp)
    assert tuple(df.iloc[0]) == (2240, 3503)


def test_multiple_facts_dimensions(chinook: Store, connection):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "items_sold"}, {"metric": "track_count"}],
            "dimensions": [{"dimension": "genre"}],
        }
    )
    comp = chinook.get_computation(q)
    df = connection.compute_df(comp)
    assert tuple(df[df["genre"] == "Rock"].iloc[0][["items_sold", "track_count"]]) == (
        835,
        1297,
    )


def test_if(chinook: Store, connection):
    """Test if() function and case when ... then ... else ... end constructs"""
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "items_sold"}],
            "dimensions": [{"dimension": "invoice_year"}, {"dimension": "leap_year"}],
        }
    )
    comp = chinook.get_computation(q)
    df = connection.compute_df(comp)
    assert df[df["leap_year"] == "Yes"].iloc[0]["invoice_year"] == 2012


def test_subquery_join(chinook: Store, connection):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "items_sold"}],
            "dimensions": [{"dimension": "customer_orders_amount_10_bins"}],
        }
    )
    comp = chinook.get_computation(q)
    df = connection.compute_df(comp)
    assert df.shape == (2, 2)
    assert df[df["customer_orders_amount_10_bins"] == 30].iloc[0].items_sold == 1708


@pytest.fixture(scope="module")
def compute(chinook: Store, connection):
    def computer(expr: str, type="datetime"):
        expr = parse_expr(expr)
        dims = [ColumnCalculation(name="value", expr=expr, type=type)]
        comp = Computation(
            queries=[
                AggregateQuery(
                    table=chinook.tables.get("media_types"),
                    groupby=dims,
                )
            ],
            dimensions=dims,
            metrics=[],
        )
        df = connection.compute_df(comp)
        return str(df.iloc[0, 0])

    return computer


def test_datetrunc(compute):
    dt = "2021-12-19 14:05:38"

    def datetrunc(part: str):
        return compute(f"datetrunc('{part}', toDatetime('{dt}'))")

    assert datetrunc("year") == "2021-01-01 00:00:00"
    assert datetrunc("quarter") == "2021-10-01 00:00:00"
    assert datetrunc("month") == "2021-12-01 00:00:00"
    assert datetrunc("week") == "2021-12-13 00:00:00"
    assert (
        compute("datetrunc('week', toDatetime('2022-01-03'))") == "2022-01-03 00:00:00"
    )
    assert datetrunc("day") == "2021-12-19 00:00:00"
    assert datetrunc("hour") == "2021-12-19 14:00:00"
    assert datetrunc("minute") == "2021-12-19 14:05:00"
    assert datetrunc("second") == "2021-12-19 14:05:38"


def test_datepart(compute):
    """ISO states that the first week of the year is the week that contains the first
    Thursday of the year, or the week that contains January 4th. Not all database engines
    conform to this and it would be very tedious to implement that on the backend level,
    so we don't test for the edge cases (start and end of year) here. Just use whatever
    logic the RDBMS provides.
    """
    dt = "2021-12-19 14:05:38"

    def datepart(part: str):
        return int(compute(f"datepart('{part}', toDatetime('{dt}'))", type="number"))

    assert datepart("year") == 2021
    assert datepart("quarter") == 4
    assert compute("datepart('quarter', toDatetime('2021-12-31'))", "number") == "4"
    assert compute("datepart('quarter', toDatetime('2022-01-01'))", "number") == "1"
    assert datepart("month") == 12
    assert datepart("week") == 50
    assert datepart("day") == 19
    assert datepart("hour") == 14
    assert datepart("minute") == 5
    assert datepart("second") == 38


def test_datediff(compute):
    def datediff(part, s, e):
        return int(
            compute(
                f"datediff('{part}', toDatetime('{s}'), toDatetime('{e}'))", "number"
            )
        )

    assert datediff("year", "2021-12-31 23:59:59", "2022-01-01 00:00:00") == 1
    assert datediff("quarter", "2021-12-31 23:59:59", "2022-01-01 00:00:00") == 1
    assert datediff("month", "2021-12-31 23:59:59", "2022-01-01 00:00:00") == 1
    assert datediff("week", "2022-01-02 23:59:59", "2022-01-03 00:00:00") == 1
    assert datediff("day", "2021-12-31 23:59:59", "2022-01-01 00:00:00") == 1
    assert datediff("hour", "2021-12-31 23:59:59", "2022-01-01 00:00:00") == 1
    assert datediff("minute", "2021-12-31 23:59:59", "2022-01-01 00:00:00") == 1
    assert datediff("second", "2021-12-31 23:59:59", "2022-01-01 00:00:00") == 1

    assert datediff("year", "2021-01-01", "2021-12-31") == 0
    assert datediff("quarter", "2021-01-01", "2021-03-31") == 0
    assert datediff("month", "2021-01-01", "2021-01-31") == 0
    assert datediff("week", "2022-01-03", "2022-01-09") == 0
    assert datediff("day", "2021-12-31 00:00:00", "2021-12-31 23:59:59") == 0
    assert datediff("hour", "2021-12-31 04:00:00", "2021-12-31 04:59:59") == 0
    assert datediff("minute", "2021-12-31 04:59:00", "2021-12-31 04:59:59") == 0
    assert datediff("second", "2021-12-31 04:59:59", "2021-12-31 04:59:59") == 0


def test_date(chinook: Store, connection):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}],
            "dimensions": [{"dimension": "invoice_date"}],
        }
    )
    comp = chinook.get_computation(q)
    result = connection.compute(comp)
    assert isinstance(result, BackendResult)
    assert isinstance(result.data, list)
    assert isinstance(result.data[0], dict)
    assert isinstance(result.data[0]["invoice_date"], datetime.date)


def test_datetime(chinook: Store, connection):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}],
            "dimensions": [{"dimension": "invoice_datetime"}],
        }
    )
    comp = chinook.get_computation(q)
    result = connection.compute(comp)
    assert isinstance(result, BackendResult)
    assert isinstance(result.data, list)
    assert isinstance(result.data[0], dict)
    assert isinstance(result.data[0]["invoice_datetime"], datetime.datetime)


def test_alias(chinook: Store, connection):
    q = Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}],
            "dimensions": [
                {
                    "dimension": "invoice_date",
                    "transform": {"id": "datepart", "args": ["year"]},
                    "alias": "year",
                },
                {
                    "dimension": "invoice_date",
                    "transform": {"id": "datepart", "args": ["month"]},
                    "alias": "month",
                },
            ],
        }
    )
    comp = chinook.get_computation(q)
    result = connection.compute(comp)
    assert set(result.data[0]) == {"revenue", "year", "month"}
