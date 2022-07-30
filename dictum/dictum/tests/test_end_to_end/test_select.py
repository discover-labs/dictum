import pytest

from dictum.project import Project


def test_single_measure(project: Project):
    result = project.select(project.metrics.revenue).df()
    assert result.columns[0] == "revenue"
    assert result.iloc[0, 0] == 2328.6


def test_metric(project: Project):
    result = project.select(project.m.revenue_per_track).df()
    result.round(2).loc[0, "revenue_per_track"] == 0.66


def test_metric_groupby(project: Project):
    select = project.select(project.m.revenue_per_track).by(project.d.genre)
    result = select.df()
    assert result.shape == (25, 2)


def test_multiple_anchors(project: Project):
    result = project.select(project.metrics.revenue, project.metrics.track_count).df()
    assert next(result.itertuples()) == (0, 2328.6, 3503)


def test_multiple_anchors_by(project: Project, engine):
    select = project.select(project.m.revenue, project.m.track_count).by(
        project.d.genre
    )
    result = select.df()
    assert result.shape == (25, 3)


def test_groupby(project: Project):
    result = (
        project.select(project.metrics.revenue, project.metrics.track_count)
        .by(project.d.genre)
        .df()
    )
    assert result.shape == (25, 3)


def test_filter_eq(project: Project):
    result = (
        project.select(project.m.revenue, project.m.track_count)
        .by(project.d.genre)
        .where(project.d.artist == "Iron Maiden")
    ).df()
    assert result.shape == (4, 3)


def test_filter_ne(project: Project):
    result = (
        project.select(project.m.revenue, project.m.track_count)
        .by(project.d.artist)
        .where(project.d.genre != "Rock")
    ).df()
    assert result.shape == (165, 3)


def test_filter_gt(project: Project):
    result = project.select(project.m.revenue).where(project.d.order_amount > 5).df()
    assert result.iloc[0, 0] == 1797.81


def test_filter_ge(project: Project):
    result = project.select(project.m.revenue).where(project.d.order_amount >= 5).df()
    assert result.iloc[0, 0] == 1797.81


def test_filter_lt(project: Project):
    result = project.select(project.m.revenue).where(project.d.order_amount < 5).df()
    assert result.iloc[0, 0] == 530.79


def test_filter_le(project: Project):
    result = project.select(project.m.revenue).where(project.d.order_amount <= 5).df()
    assert result.iloc[0, 0] == 530.79


def test_filter_isin(project: Project):
    result = (
        project.select(project.m.revenue)
        .where(project.d.genre.isin("Alternative", "Rock"))
        .by(project.d.genre)
        .df()
    )
    assert result.shape == (2, 2)


def test_date_unit(project: Project):
    result = project.select(project.m.revenue).by(project.d.invoice_date.year).df()
    assert result.shape == (5, 2)


def test_step_transform(project: Project):
    result = project.select(project.m.revenue).by(project.d.order_amount.step(10)).df()
    assert result.shape == (3, 2)


def test_dimension_alias(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.invoice_date.year.name("year"))
        .df()
    )
    assert tuple(result.columns) == ("year", "revenue")


def test_metric_alias(project: Project):
    result = project.select(project.m.revenue.name("test")).by(project.d.genre).df()
    assert tuple(result.columns) == ("genre", "test")


def test_datetrunc_and_inrange(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.invoice_date.datetrunc("week"))
        .where(project.d.invoice_date.inrange("2010-01-01", "2011-12-31"))
        .df()
    )
    assert result.shape == (81, 2)


def test_top_with_measure_basic(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.genre)
        .limit(project.m.revenue.top(5))
        .df()
    )
    assert set(result.genre) == {
        "Metal",
        "Latin",
        "Rock",
        "Alternative & Punk",
        "TV Shows",
    }


def test_top_with_metrics_basic(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.genre)
        .limit(project.m.revenue_per_track.top(5))
        .df()
    )
    assert set(result.genre) == {
        "Bossa Nova",
        "Sci Fi & Fantasy",
        "TV Shows",
        "Comedy",
        "Science Fiction",
    }


def test_top_with_multiple_basic(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.genre)
        .limit(
            project.m.revenue.top(10),
            project.m.revenue_per_track.top(10),
        )
        .df()
    )
    assert set(result.genre) == {
        "Blues",
        "TV Shows",
        "Drama",
        "Alternative & Punk",
        "Metal",
        "R&B/Soul",
    }


def test_top_with_multiple_basic_reverse_order(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.genre)
        .limit(
            project.m.revenue_per_track.top(10),
            project.m.revenue.top(10),
        )
        .df()
    )
    assert set(result.genre) == {
        "Blues",
        "TV Shows",
        "Drama",
        "Alternative & Punk",
        "Metal",
        "R&B/Soul",
    }


def test_top_with_measure_basic_metric(project: Project):
    result = (
        project.select(project.m.revenue_per_track)
        .by(project.d.genre)
        .limit(project.m.revenue.top(5))
        .df()
    )
    assert set(result.genre) == {
        "Metal",
        "Latin",
        "Rock",
        "Alternative & Punk",
        "TV Shows",
    }


def test_top_with_metric_basic_metric(project: Project):
    result = (
        project.select(project.m.revenue_per_track)
        .by(project.d.genre)
        .limit(project.m.revenue_per_track.top(5))
        .df()
    )
    assert set(result.genre) == {
        "Bossa Nova",
        "Sci Fi & Fantasy",
        "TV Shows",
        "Comedy",
        "Science Fiction",
    }


def test_top_with_multiple_basic_metric(project: Project):
    result = (
        project.select(project.m.revenue_per_track)
        .by(project.d.genre)
        .limit(
            project.m.revenue.top(10),
            project.m.revenue_per_track.top(10),
        )
        .df()
    )
    assert set(result.genre) == {
        "Blues",
        "TV Shows",
        "Drama",
        "Alternative & Punk",
        "Metal",
        "R&B/Soul",
    }


def test_top_with_multiple_basic_metric_reverse_order(project: Project):
    result = (
        project.select(project.m.revenue_per_track)
        .by(project.d.genre)
        .limit(
            project.m.revenue_per_track.top(10),
            project.m.revenue.top(10),
        )
        .df()
    )
    assert set(result.genre) == {
        "Blues",
        "TV Shows",
        "Drama",
        "Alternative & Punk",
        "Metal",
        "R&B/Soul",
    }


def test_top_with_measure_within(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.genre, project.d.artist)
        .limit(project.m.revenue.top(3, within=[project.d.genre]))
        .df()
    )
    assert result.shape == (56, 3)


def test_top_with_measure_within_of(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.genre, project.d.artist)
        .limit(
            project.m.revenue.top(3, within=[project.d.genre]),
            project.m.revenue.top(3, of=[project.d.genre]),
        )
        .df()
    )
    assert result.shape == (9, 3)
    assert set(result.genre) == {"Latin", "Metal", "Rock"}


def test_top_with_metric_within_of(project: Project):
    result = (
        project.select(project.m.revenue, project.m.revenue_per_track)
        .by(project.d.genre, project.d.artist)
        .limit(
            project.m.revenue_per_track.top(3, within=[project.d.genre]),
            project.m.revenue_per_track.top(3, of=[project.d.genre]),
        )
        .df()
    )
    assert result.shape == (6, 4)


def test_tops_with_total(project: Project, engine):
    result = (
        project.select("revenue", "revenue.total")
        .by("customer_country", "customer_city")
        .limit(
            "revenue.top(3) of (customer_country)",
            "revenue.top(1) of (customer_city) within (customer_country)",
        )
        .df()
    )
    assert result.shape == (3, 4)


def test_tops_with_total_within(project: Project):
    result = project.ql(
        """
    select revenue, revenue.total within (customer_country)
    by customer_country, customer_city
    limit revenue.top(5) of (customer_country),
        revenue.top(1) of (customer_city) within (customer_country)
    """
    ).df()
    assert result.shape == (5, 4)


def test_tops_with_matching_total_and_percent(project: Project):
    result = project.ql(
        """
    select revenue,
        revenue.percent of (customer_city) as "% of City Revenue",
        revenue.total within (customer_country) as "Total Revenue: Country"
    by customer_country, customer_city
    limit revenue.top(5) of (customer_country),
        revenue.top(1) of (customer_city) within (customer_country)
    """
    ).df()
    assert result.shape == (5, 5)


def test_total_basic(project: Project):
    result = (
        project.select(project.m.revenue, project.m.revenue.total())
        .by(project.d.genre)
        .df()
    )
    assert result.shape == (24, 3)
    assert result.revenue__total.unique().tolist() == [2328.6]


def test_total_metric(project: Project):
    select = (
        project.select(
            project.m.revenue_per_track,
            project.m.revenue_per_track.total(within=[project.d.genre]),
        )
        .by(project.d.genre, project.d.artist)
        .limit(project.m.revenue.top(3, within=[project.d.genre]))
    )
    result = select.df()
    assert result.shape == (56, 4)
    assert len(set(result.genre)) == len(
        set(result.revenue_per_track__total_within_genre)
    )


def test_total_transformed_dimension(project: Project):
    result = (
        project.select("revenue.total within (Time.year)")
        .by("Time.year", "Time.month")
        .df()
    )
    assert len(result.iloc[:, -1].unique()) == 5


def test_total_filters(project: Project):
    """Test that filters are applied to the table transforms too (was a bug)"""
    select = (
        project.select(project.m.revenue.total())
        .by(project.d.genre)
        .where(project.d.genre.isin("Rock", "Alternative & Punk"))
    )
    result = select.df()
    assert result["revenue__total"].unique()[0] == 1068.21


def test_percent_basic(project: Project):
    result = project.select(project.m.revenue.percent()).by(project.d.genre).df()
    assert result.shape == (24, 2)
    assert result["revenue__percent"].sum() == 1


def test_percent_of(project: Project):
    result = project.select("revenue.percent of (artist)").by("genre", "artist").df()
    unique = result.groupby("genre").sum().iloc[:, 0].round(4).unique()
    assert unique.size == 1
    assert unique[0] == 1.0


def test_percent_within(project: Project):
    result = project.select("revenue.percent within (genre)").by("genre", "artist").df()
    unique = result.groupby("genre").sum().iloc[:, 0].round(4).unique()
    assert unique.size == 1
    assert unique[0] == 1.0


def test_percent_of_within(project: Project):
    result = (
        project.select(
            "revenue",
            "revenue.percent of (artist) within (genre)",
        ).by("genre", "artist", "album")
        # .where("artist = 'Faith No More'")
        .df()
    )
    values = result.query("genre == 'TV Shows' and artist == 'The Office'")[
        "revenue__percent_of_artist_within_genre"
    ].unique()
    assert len(values) == 1
    assert values.round(4)[0] == 0.3404


def test_percent_with_top(project: Project):
    """Percent should be calculated before top"""
    result = (
        project.select(project.m.revenue.percent())
        .by(project.d.genre)
        .limit(project.m.revenue.top(5))
        .df()
    )
    assert result.shape == (5, 2)
    assert round(result["revenue__percent"].sum(), 4) == 0.7752


def test_percent_with_top_within(project: Project):
    result = (
        project.select(
            project.m.revenue.percent(within=[project.d.genre]).name(
                "artist_revenue_within_genre"
            )
        )
        .by(project.d.genre, project.d.artist)
        .limit(project.m.revenue.top(1, within=[project.d.genre]))
        .df()
    )
    assert result.shape == (24, 3)
    assert result.columns[-1] == "artist_revenue_within_genre"  # alias works


def test_percent_integer(project: Project):
    """Check that the output type is handled correctly (float, not the original int)
    and that the percentages for unique values do not add up to 100%"""
    select = project.select(project.m.unique_paying_customers.percent()).by(
        project.d.genre
    )
    result = select.df()
    assert round(result["unique_paying_customers__percent"].sum(), 2) == 7.46


def test_format_metric(project: Project):
    result = project.select(project.m.revenue).df(format=True)
    assert result.columns[0] == "Revenue"  # column name comes from the metric name
    assert result.iloc[0, 0] == "$2,328.60"  # the value is formatted


def test_format_dimension_name(project: Project):
    result = project.select(project.m.revenue).by(project.d.genre).df(format=True)
    assert list(result.columns) == ["Genre", "Revenue"]


def test_format_transform(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.invoice_date.year)
        .df(format=True)
    )
    assert list(result.columns) == ["Invoice Date (year)", "Revenue"]
    assert result.iloc[0, 0] == "2009"


def test_format_dimension_transform_alias(project: Project):
    result = (
        project.select(project.m.revenue.percent().name("Percent of Revenue"))
        .by(project.d.invoice_date.year.name("Year"))
        .df(format=True)
    )
    assert list(result.columns) == ["Year", "Percent of Revenue"]


def test_filtered_table(project: Project):
    result = project.select(project.m.rock_revenue).df()
    assert result.iloc[0, 0] == 826.65


def test_filtered_measure(project: Project):
    result = project.select("music_revenue").df()
    assert result.iloc[0, 0] == 2107.71


def test_filtered_and_unfiltered_measures_together(project: Project):
    result = project.select("revenue", "music_revenue").df()
    assert next(result.itertuples(index=False)) == (2328.6, 2107.71)


def test_generic_time(project: Project):
    result = project.select("revenue").by("Time.datetrunc('year')").df()
    assert result.shape == (5, 2)


def test_generic_time_alias_display_name(project: Project):
    result = project.select("revenue").by("Year as test").df(format=True)
    assert result.columns[0] == "test"


def test_generic_time_format(project: Project):
    result = project.select("revenue").by("Year").df(format=True)
    assert result.iloc[0]["Year"] == "2009"


@pytest.mark.parametrize(
    "dimension,n",
    [
        ("Year", 5),
        ("Quarter", 20),
        ("Month", 60),
        ("Week", 202),
        ("Day", 354),
        ("Date", 354),
        ("Hour", 354),  # dates in the database
        ("Minute", 354),
        ("Second", 354),
        ("Time", 354),
    ],
)
def test_generic_time_trunc(project: Project, dimension: str, n: int):
    result = project.select("revenue").by(dimension).df()
    assert result.shape == (n, 2)


def test_generic_time_trunc_transform(project: Project):
    result = project.select("revenue").by("Month.datetrunc('year')").df()
    assert result.shape == (5, 2)


def test_sum_table_transform(project: Project):
    result = project.select("revenue.sum").by("genre").df()
    assert result["revenue__sum"].unique().size == 1
    assert result["revenue__sum"].unique()[0] == 2328.6


def test_sum_table_transform_within(project: Project):
    result = (
        project.select("revenue", "revenue.sum() within (genre)")
        .by("genre", "artist")
        .df()
    )
    gb = result.groupby("genre").aggregate(
        {"revenue": "sum", "revenue__sum_within_genre": "max"}
    )
    assert (gb["revenue"].round(2) == gb["revenue__sum_within_genre"]).all()


def test_measure_with_related_column(project: Project):
    """Test that related columns are supported in measures"""
    project.select("unique_paying_customers").df()  # no error


def test_default_time_format(project: Project):
    result = project.select("revenue").by("invoice_date").df(format=True)
    assert result.iloc[0]["Invoice Date"] == "1/1/09"


def test_percents_without_alias(project: Project):
    """Bug found writing the docs. Something is wrong when running this query, fails
    in the pandas merge Visitor with KeyError, column not found.
    """
    (
        project.select(
            "revenue.percent within (invoice_date.year)",
            "revenue.percent of (invoice_date.quarter) within (invoice_date.year)",
        )
        .by("invoice_date.year", "invoice_date.quarter", "invoice_date.month")
        .df()
    )


def test_total_of_within_keyerror(project: Project):
    """Bug found writing the docs, similar to the above"""
    (
        project.select(
            "revenue.total within (Year)",
            "revenue.total of (Year)",
        ).by("Year", "Quarter")
    ).df()
