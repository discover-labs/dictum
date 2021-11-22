"""Generate HTML for the documentation snippets.
"""

from pathlib import Path

import dictum
from dictum import Project
from dictum.project import Select

tutorial = Project.example("tutorial")

snippets = Path(dictum.__file__).parent.parent.parent / "docs" / "snippets"


def generate(select: Select, path: str):
    html = (
        select.execute()
        .to_html(max_rows=10)
        .replace('border="1" class="dataframe"', "")
    )
    (snippets / path).write_text(html)


generate(tutorial.select("revenue"), "tables/query_revenue.html")

generate(
    tutorial.select("revenue").by("order_created_at"),
    "dimensions/query_revenue_by_date.html",
)

generate(
    tutorial.select("revenue").by("order_created_at", transform="datetrunc('year')"),
    "dimensions/query_revenue_by_date_transform.html",
)

generate(
    (
        tutorial.select("revenue")
        .by("order_created_at", transform="datepart('year')", alias="year")
        .by("order_created_at", transform="datepart('month')", alias="month")
    ),
    "dimensions/query_revenue_by_date_alias.html",
)

generate(
    (
        tutorial.pivot("revenue")
        .rows("channel")
        .columns("order_created_at", "datepart('year')", "year")
    ),
    "dimensions/pivot.html",
)

generate(
    (
        tutorial.pivot("revenue")
        .columns("channel")
        .rows("order_created_at", "datepart('year')", "year")
        .rows("order_created_at", "datepart('quarter')", "quarter")
    ),
    "dimensions/pivot_nested.html",
)

generate(
    tutorial.select("revenue", "unique_paying_users", "arppu").by(
        "order_created_at", "datepart('year')", "year"
    ),
    "reusable_expressions/arppu.html",
)

generate(
    tutorial.select("revenue", "users").by("date", "datepart('year')", "year"),
    "union_dimensions/select_by_union.html",
)


generate(
    tutorial.select("ppu").by("user_channel"),
    "metrics_and_measures/ppu_by_channel.html",
)

generate(
    tutorial.select("users").by("user_order_count"),
    "aggregate_dimensions/user_order_count.html",
)

generate(
    (
        tutorial.pivot("orders")
        .rows("user_first_order_date", "datetrunc('month')", "cohort_month")
        .columns("months_since_first_order")
        .where("user_first_order_date", "atleast('2021-11-01')")
    ),
    "aggregate_dimensions/order_cohorts.html",
)
