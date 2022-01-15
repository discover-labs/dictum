from dictum.project import Project


def test_single_measure(project: Project):
    result = project.select(project.metrics.revenue).execute()
    assert result.iloc[0, 0] == 2328.6


def test_metric(project: Project):
    result = project.select(project.m.revenue_per_track).execute()
    result.round(2).loc[0, "revenue_per_track"] == 0.66


def test_multiple_anchors(project: Project):
    result = project.select(
        project.metrics.revenue, project.metrics.track_count
    ).execute()
    assert next(result.itertuples()) == (0, 2328.6, 3503)


def test_groupby(project: Project):
    result = (
        project.select(project.metrics.revenue, project.metrics.track_count)
        .by(project.d.genre)
        .execute()
    )
    assert result.shape == (25, 3)


def test_filter_eq(project: Project):
    result = (
        project.select(project.m.revenue, project.m.track_count)
        .by(project.d.genre)
        .where(project.d.artist == "Iron Maiden")
    ).execute()
    assert result.shape == (4, 3)


def test_filter_ne(project: Project):
    result = (
        project.select(project.m.revenue, project.m.track_count)
        .by(project.d.artist)
        .where(project.d.genre != "Rock")
    ).execute()
    assert result.shape == (165, 3)


def test_filter_gt(project: Project):
    result = (
        project.select(project.m.revenue).where(project.d.order_amount > 5).execute()
    )
    assert result.iloc[0, 0] == 1797.81


def test_filter_ge(project: Project):
    result = (
        project.select(project.m.revenue).where(project.d.order_amount >= 5).execute()
    )
    assert result.iloc[0, 0] == 1797.81


def test_filter_lt(project: Project):
    result = (
        project.select(project.m.revenue).where(project.d.order_amount < 5).execute()
    )
    assert result.iloc[0, 0] == 530.79


def test_filter_le(project: Project):
    result = (
        project.select(project.m.revenue).where(project.d.order_amount <= 5).execute()
    )
    assert result.iloc[0, 0] == 530.79


def test_filter_isin(project: Project):
    result = (
        project.select(project.m.revenue)
        .where(project.d.genre.isin("Alternative", "Rock"))
        .by(project.d.genre)
        .execute()
    )
    assert result.shape == (2, 2)


def test_date_unit(project: Project):
    result = project.select(project.m.revenue).by(project.d.invoice_date.year).execute()
    assert result.shape == (5, 2)


def test_dimension_alias(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.invoice_date.year.name("year"))
        .execute()
    )
    assert tuple(result.columns) == ("year", "revenue")


def test_metric_alias(project: Project):
    result = (
        project.select(project.m.revenue.name("test"))
        .by(project.d.genre)
        .execute()
    )
    assert tuple(result.columns) == ("genre", "test")


def test_datetrunc_and_inrange(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.invoice_date.datetrunc("week"))
        .where(project.d.invoice_date.inrange("2010-01-01", "2011-12-31"))
        .execute()
    )
    assert result.shape == (81, 2)


def test_top_with_measure_basic(project: Project):
    result = (
        project.select(project.m.revenue)
        .by(project.d.genre)
        .limit(project.m.revenue.top(5))
        .execute()
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
        .execute()
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
        .execute()
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
        .execute()
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
        .execute()
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
        .execute()
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
        .execute()
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
        .execute()
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
        .execute()
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
        .execute()
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
        .execute()
    )
    assert result.shape == (6, 4)


def test_total_basic(project: Project):
    result = (
        project.select(project.m.revenue, project.m.revenue.total())
        .by(project.d.genre)
        .execute()
    )
    assert result.shape == (24, 3)
    assert result.revenue__total.unique().tolist() == [2328.6]


# TODO: test_total_within_of


def test_percent_basic(project: Project):
    result = project.select(project.m.revenue.percent()).by(project.d.genre).execute()
    assert result.shape == (24, 2)
    assert result["revenue__percent"].sum() == 1


def test_percent_with_top(project: Project):
    """Percent should be calculated before top"""
    result = (
        project.select(project.m.revenue.percent())
        .by(project.d.genre)
        .limit(project.m.revenue.top(5))
        .execute()
    )
    assert result.shape == (5, 2)
    assert round(result["revenue__percent"].sum(), 4) == 0.7752


def test_percent_with_top_within(project: Project):
    result = (
        project.select(
            project.m.revenue.percent(within=[project.d.genre]).name(
                "Percent of top-1 Artist Revenue within Genre"  # TODO: ???
            )
        )
        .by(project.d.genre, project.d.artist)
        .limit(project.m.revenue.top(1, within=[project.d.genre]))
        .execute()
    )
    breakpoint()
