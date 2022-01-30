"""Same queries as with select, but in ql. We mainly care about everything working, the
query parsing tests are tested where ql itself is tested.
"""

from dictum.project import Project


def test_ql_query(project: Project):
    query = """
    select revenue.percent() as "Percent of Revenue"
    by invoice_date.year as Year, artist
    limit revenue.top(1) of (artist) within (invoice_date.year)
    """
    ql = project.ql(query)
    result = ql.df()
    assert result.shape[0] == 5

    fmt = ql.df(format=True)
    assert tuple(fmt.columns) == ("Year", "Artist", "Percent of Revenue")
