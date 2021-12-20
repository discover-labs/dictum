import altair as alt

from dictum.project.altair.data import DictumData
from dictum.project.altair.monkeypatch import (
    is_dictum_definition,
    monkeypatch_altair,
    request_from_field,
    requests_from_channel,
)
from dictum.project.project import Project
from dictum.schema.query import Query

monkeypatch_altair()


def test_encode_shorthand(project: Project):
    assert (
        project.chart().encode(x=project.m.revenue).encoding.x.field == "metric:revenue"
    )


def test_channel_init(project: Project):
    channel = alt.X(project.m.revenue)
    assert channel.shorthand == alt.Undefined
    assert channel.field == "metric:revenue"


def test_facet_resolve(project: Project):
    chart = project.chart().mark_bar().encode(x=project.m.revenue)
    media_type = alt.FieldName("dimension:media_type")
    assert chart.facet(project.d.media_type)._kwds["facet"].field == media_type
    assert chart.facet(row=project.d.media_type)._kwds["facet"].row.field == media_type
    assert (
        chart.facet(column=project.d.media_type)._kwds["facet"].column.field
        == media_type
    )


def test_repeat_resolve(project: Project):
    chart = (
        project.chart()
        .mark_bar()
        .encode(x=project.d.media_type, y=alt.repeat("repeat"))
    )
    assert chart.repeat([project.m.revenue])._kwds["repeat"][0] == "metric:revenue"
    assert (
        chart.repeat(row=[project.m.revenue])._kwds["repeat"].row[0] == "metric:revenue"
    )
    assert (
        chart.repeat(column=[project.m.revenue])._kwds["repeat"].column[0]
        == "metric:revenue"
    )
    assert (
        chart.repeat(layer=[project.m.revenue])._kwds["repeat"].layer[0]
        == "metric:revenue"
    )


def test_iterunits():
    ch = alt.Chart("#").mark_bar()

    assert len(list(ch._iterunits())) == 1
    assert len(list((ch + ch)._iterunits())) == 2
    assert len(list((ch | ch)._iterunits())) == 2
    assert len(list((ch & ch)._iterunits())) == 2
    assert len(list((ch | ch | ch)._iterunits())) == 3
    assert len(list((ch & ch & ch)._iterunits())) == 3
    assert len(list((ch | ch & ch)._iterunits())) == 3
    assert len(list((ch & ch | ch)._iterunits())) == 3
    assert len(list((ch & ch | ch & ch)._iterunits())) == 4
    assert len(list((ch | ch & ch | ch)._iterunits())) == 4
    assert len(list(((ch | ch) & ch)._iterunits())) == 3
    assert len(list((ch | (ch & ch))._iterunits())) == 3

    facet = alt.Chart("#").mark_bar().facet(column="test:N")
    assert len(list(facet._iterunits())) == 1
    assert len(list((ch | (ch & facet))._iterunits())) == 3

    repeat = alt.Chart("#").mark_bar().repeat(column=["test"])
    assert len(list(repeat._iterunits())) == 1
    assert len(list((ch | (ch & repeat))._iterunits())) == 3


def test_iterunits_data():
    a = alt.NamedData("a")
    b = alt.NamedData("b")
    ch = alt.Chart(a).mark_bar()

    assert next(ch._iterunits())[1] == a
    assert [d for _, d in (ch | ch)._iterunits()] == [a, a]
    assert [d for _, d in (ch & ch)._iterunits()] == [a, a]
    assert [d for _, d in (ch & ch.properties(data=b))._iterunits()] == [a, b]
    assert [d for _, d in (ch & (ch.properties(data=b) & ch))._iterunits()] == [a, b, a]

    facet = ch.facet(column="test:N")
    assert [d for _, d in facet._iterunits()] == [a]
    assert [d for _, d in (ch | facet.properties(data=b))._iterunits()] == [a, b]

    repeat = alt.Chart(a).mark_bar().encode(x="x:N", y="y:Q").repeat(["a"])
    assert list(repeat._iterunits()) == [(repeat, a)]


def test_iterchannels():
    ch = alt.Chart("#").mark_bar().encode(x="x:Q", y="y:N")
    assert len(list(ch._iterchannels())) == 2
    assert len(list(ch.encode(text="z:N")._iterchannels())) == 3
    assert len(list(ch.facet(column="test:N").spec._iterchannels())) == 2
    assert len(list(ch.facet(column="test:N")._iterchannels())) == 2


def test_chart_to_dict(project: Project):
    d = (
        project.chart()
        .mark_bar(stroke="white")
        .encode(
            x=project.m.track_count,
            y=alt.Y(project.d.genre, sort="-x"),
            color=alt.Color(project.d.media_type, sort="-x"),
            order=alt.Order(project.m.track_count, sort="descending"),
        )
    ).to_dict()
    assert d["encoding"]["x"]["field"] == "metric:track_count"
    assert d["encoding"]["y"]["field"] == "dimension:genre"


def test_chart_query(project: Project):
    chart = (
        project.chart()
        .mark_bar(stroke="white")
        .encode(
            x=project.d.invoice_date.year,
            y=project.m.revenue,
            color=alt.Color(project.d.media_type),
        )
    )
    assert chart._query() == Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}],
            "dimensions": [
                {"dimension": "media_type"},
                {"dimension": "invoice_date", "transforms": [{"id": "year"}]},
            ],
        }
    )


def test_query_sort(project: Project):
    chart = (
        project.chart()
        .mark_bar()
        .encode(x=alt.X(project.d.genre, sort=project.m.revenue))
    )
    assert chart._query() == Query.parse_obj(
        {
            "metrics": [{"metric": "revenue"}],
            "dimensions": [{"dimension": "genre"}],
        }
    )


def test_repeat_not_resolving_data(project: Project):
    chart = (
        project.chart()
        .mark_line()
        .encode(x=project.d.genre, y=alt.Y(alt.repeat("layer")))
        .repeat(layer=[project.m.track_count, project.m.revenue])
    )
    assert len(list(chart._iterunits())) > 0
    unit, data = next(chart._iterunits())
    assert unit is chart
    assert isinstance(data, DictumData)


def test_channel_sort(project: Project):
    assert alt.X(project.d.genre, sort=project.m.revenue).sort.field == "metric:revenue"


def test_is_dictum_definition():
    assert is_dictum_definition(alt.FieldName("metric:revenue"))
    assert is_dictum_definition("metric:revenue")
    assert is_dictum_definition("dimension:x")
    assert is_dictum_definition("dimension:x.test.blah()")
    assert not is_dictum_definition("blahblah:Q")


def test_request_from_field():
    assert request_from_field("metric:revenue").metric == "revenue"
    assert request_from_field(alt.FieldName("metric:revenue")).metric == "revenue"
    assert request_from_field(alt.FieldName("blah")) is None
    assert request_from_field("dimension:xx.date").dimension == "xx"


def test_requests_from_channel(project: Project):
    assert len(requests_from_channel(alt.X(field="metric:test"))) == 1
    assert (
        len(
            requests_from_channel(
                alt.X(
                    project.d.genre,
                    sort=alt.EncodingSortField(project.m.revenue, order="descending"),
                )
            )
        )
        == 2
    )
    assert len(requests_from_channel(alt.X("something:Q"))) == 0
