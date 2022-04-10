import datetime

import pytest
from pandas import DataFrame
from pandas.api.types import is_datetime64_any_dtype

from dictum.backends.base import Backend
from dictum.engine import Column, Engine, RelationalQuery
from dictum.model import Model
from dictum.model.expr.parser import parse_expr
from dictum.schema import Query


@pytest.fixture(scope="module")
def compute_df(chinook: Model, engine: Engine, backend: Backend):
    def compute(query: Query):
        resolved = chinook.get_resolved_query(query)
        computation = engine.get_computation(resolved)
        return DataFrame(computation.execute(backend).data)

    return compute


@pytest.fixture(scope="module")
def compute_results(chinook: Model, engine: Engine, backend: Backend):
    def compute(query: Query):
        resolved = chinook.get_resolved_query(query)
        computation = engine.get_computation(resolved)
        return computation.execute(backend).data

    return compute


def test_groupby(compute_df: callable):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "track_count"}}],
            "dimensions": [{"dimension": {"id": "genre"}}],
        }
    )
    df = compute_df(query)
    assert df[df["genre"] == "Rock"].iloc[0]["track_count"] == 1297


def test_filter(compute_df: callable):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "items_sold"}}],
            "filters": [
                {"id": "genre", "transforms": [{"id": "isin", "args": ["Rock"]}]},
                {
                    "id": "customer_country",
                    "transforms": [{"id": "isin", "args": ["USA"]}],
                },
            ],
        }
    )
    df = compute_df(query)
    assert df.iloc[0][0] == 157


@pytest.mark.skip
def test_convert_datetime(chinook: Model, connection):
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


def test_metric_not_measure(compute_df: callable):
    query = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "revenue"}},
                {"metric": {"id": "track_count"}},
                {"metric": {"id": "revenue_per_track"}},
            ]
        }
    )
    df = compute_df(query)
    assert next(df.round(2).itertuples()) == (0, 2328.6, 3503, 0.66)


def test_metric_with_groupby(compute_df: callable):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "arppu"}}, {"metric": {"id": "track_count"}}],
            "dimensions": [{"dimension": {"id": "genre"}}],
        }
    )
    df = compute_df(query)
    assert df.shape == (25, 3)


def test_multiple_facts(compute_df: callable):
    query = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "items_sold"}},
                {"metric": {"id": "track_count"}},
            ]
        }
    )
    df = compute_df(query)
    assert tuple(df.iloc[0]) == (2240, 3503)


def test_multiple_facts_dimensions(compute_df: callable):
    query = Query.parse_obj(
        {
            "metrics": [
                {"metric": {"id": "items_sold"}},
                {"metric": {"id": "track_count"}},
            ],
            "dimensions": [{"dimension": {"id": "genre"}}],
        }
    )
    df = compute_df(query)
    assert tuple(df[df["genre"] == "Rock"].iloc[0][["items_sold", "track_count"]]) == (
        835,
        1297,
    )


def test_if(compute_df: callable):
    """Test if() function and case when ... then ... else ... end constructs"""
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "items_sold"}}],
            "dimensions": [
                {"dimension": {"id": "invoice_year"}},
                {"dimension": {"id": "leap_year"}},
            ],
        }
    )
    df = compute_df(query)
    assert df[df["leap_year"] == "Yes"].iloc[0]["invoice_year"] == 2012


def test_subquery_join(compute_df: callable):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "items_sold"}}],
            "dimensions": [{"dimension": {"id": "customer_orders_amount_10_bins"}}],
        }
    )
    df = compute_df(query)
    assert df.shape == (2, 2)
    assert df[df["customer_orders_amount_10_bins"] == 30].iloc[0].items_sold == 1708


@pytest.fixture(scope="module")
def compute(chinook: Model, backend: Backend):
    def computer(expr: str, type="datetime"):
        expr = parse_expr(expr)
        columns = [Column(name="value", expr=expr, type=type)]
        query = RelationalQuery(
            source=chinook.tables.get("media_types"),
            _groupby=columns,
            join_tree=[],
        )
        compiled = backend.compile_query(query)
        return str(backend.execute(compiled).iloc[0, 0])

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
    Thursday of the year, or the week that contains January 4th. Not all database
    engines conform to this and it would be very tedious to implement that on the
    backend level, so we don't test for the edge cases (start and end of year) here.
    Just use whatever logic the RDBMS provides.
    """
    dt = "2021-12-19 14:05:38"

    def datepart(part: str):
        return int(compute(f"datepart('{part}', toDatetime('{dt}'))", type="int"))

    assert datepart("year") == 2021
    assert datepart("quarter") == 4
    assert compute("datepart('quarter', toDatetime('2021-12-31'))", "int") == "4"
    assert compute("datepart('quarter', toDatetime('2022-01-01'))", "int") == "1"
    assert datepart("month") == 12
    assert datepart("week") == 50
    assert datepart("day") == 19
    assert datepart("hour") == 14
    assert datepart("minute") == 5
    assert datepart("second") == 38


def test_datediff(compute):
    def datediff(part, s, e):
        return int(
            compute(f"datediff('{part}', toDatetime('{s}'), toDatetime('{e}'))", "int")
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


def test_date(compute_results: callable):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [{"dimension": {"id": "invoice_date"}}],
        }
    )
    results = compute_results(query)
    assert isinstance(results, list)
    assert isinstance(results[0], dict)
    assert isinstance(results[0]["invoice_date"], datetime.date)


def test_datetime(compute_results: callable):
    query = Query.parse_obj(
        {
            "metrics": [{"metric": {"id": "revenue"}}],
            "dimensions": [{"dimension": {"id": "invoice_datetime"}}],
        }
    )
    results = compute_results(query)
    assert isinstance(results, list)
    assert isinstance(results[0], dict)
    assert isinstance(results[0]["invoice_datetime"], datetime.datetime)
