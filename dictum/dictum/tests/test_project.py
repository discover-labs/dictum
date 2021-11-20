from dictum import Project, func


def test_pivot_aliases(project: Project):
    pivot = (
        project.pivot("revenue")
        .rows("invoice_date", func.datepart("year"), "year")
        .columns("invoice_date", func.datepart("quarter"), "quarter")
    )
    df = pivot.df()
    assert df.index.names == ["year", "$"]
    assert df.columns.names == ["quarter"]
