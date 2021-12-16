from dictum import Project
from dictum.project import Pivot


def test_pivot_select(project: Project):
    pivot = project.pivot("revenue", "track_count")
    df = pivot.execute()
    assert isinstance(pivot, Pivot)
    assert df.shape == (1, 2)


def test_pivot_rows(project: Project):
    pivot = project.pivot("revenue").rows("genre")
    assert pivot.execute().shape == (24, 1)


def test_pivot_columns(project: Project):
    df = project.pivot("revenue").columns("genre").execute()
    assert df.shape == (1, 24)
    assert df.index.name is None
    assert df.index == [0]


def test_pivot_both(project: Project):
    pivot = (
        project.pivot("revenue")
        .rows("genre")
        .columns(project.d.invoice_date.year.name("year"))
    )
    df = pivot.execute()
    assert df.index.name == "genre"
    assert df.columns.names == ("year", "$")
    assert df.shape == (24, 5)


def test_pivot_measures_reshape(project: Project):
    df = project.pivot("revenue", "track_count").rows("$").columns("genre").execute()
    assert df.shape == (2, 25)

    df = (
        project.pivot("revenue", "track_count")
        .rows("$")
        .rows("genre")
        .columns("media_type")
        .execute()
    )
    assert df.shape == (50, 5)
    assert df.index.names == ("$", "genre")
