from functools import cached_property
from typing import List, Optional, Union

import pandas as pd

import dictum.project
from dictum.backends.base import BackendResult
from dictum.project.dimensions import ProjectDimension, ProjectDimensionTransform
from dictum.ql import compile_filter, compile_grouping
from dictum.query import Query, QueryMetricRequest


class Select:
    """Represents a select query that will return the data in the "tall" format.

    This class is not supposed to be instantiated directly, for instantiating use
    ``Project.select(*metrics: str)``.

    After selecting the metrics, the query can be further refined by calling its methods.
    """

    def __init__(self, project: "dictum.project.Project", *metrics):
        self.project = project
        self.query = Query(metrics=[QueryMetricRequest(metric=str(m)) for m in metrics])

    def by(
        self,
        dimension: Union[str, ProjectDimension, ProjectDimensionTransform],
        alias: Optional[str] = None,
    ) -> "Select":
        """Add a dimension to the query. Can be called multiple times for adding more
        than one grouping.

        Arguments:
            dimension:
                One of:

                - Dimension ID in string form to add: ``"date"``
                - String grouping expression with a transform: ``"date.datepart('year')"``
                - Built grouping expression: ``project["date"].datepart("year")``

            alias: An optional alias for the resulting column name. Use this when you
                add the same dimension with different transform multiple times.

        Returns:
            self

        Examples:
            ```py
            (
                project.select("revenue")
                .by("date.year", "year")
                .by("date.month", "month")
            )
            ```

            ```py
            (
                project.select("users_count")
                .by(project["user_revenue"].step(100))
            )
            ```


        """
        request = compile_grouping(str(dimension))
        if alias is not None:
            request.alias = alias
        self.query.dimensions.append(request)
        return self

    def where(self, *filters: str) -> "Select":
        """Add one or more dimension filters to the query. Can be called multiple times.

        Arguments:
            filters: One or more filters to apply.
                One of:

                - String transform expression: ``"amount > 0"``
                - Built transform expression: ``project["amount"] > 0``,
                  ``project["date"].last(30, "day")``

        Returns:
            self

        Examples:
            ```py
            (
                project.select("revenue")
                .by("date.month")
                .where("order_amount >= 10")
            )
            ```
        """
        for f in filters:
            self.query.filters.append(compile_filter(str(f)))
        return self

    def _execute(self) -> BackendResult:
        return self.project.execute(self.query)

    def _get_df(self, data: List[dict]) -> pd.DataFrame:
        return pd.DataFrame(data)

    def execute(self) -> pd.DataFrame:
        """Execute the query and return a Pandas DataFrame. In Jupyter, if you don't
        need to store the result in a variable and want to just see the data, you can
        skip calling this method. ``Select``'s representation in Jupyter is its result.
        """
        result = self.project.execute(self.query)
        return self._get_df(result.data)

    def _repr_html_(self):
        result = self.project.execute(self.query)
        print(f"Executed query in {result.duration} ms")
        df = self._get_df(result.data)
        return df.to_html()

    def dimensions(self):
        dimensions = self.project.store.suggest_dimensions(self.query)
        return pd.DataFrame(
            data=[
                {"id": d.id, "name": d.name, "description": d.description}
                for d in dimensions
            ]
        )

    def metrics(self):
        metrics = self.project.store.suggest_metrics(self.query)
        return pd.DataFrame(
            data=[
                {"id": m.id, "name": m.name, "description": m.description}
                for m in metrics
            ]
        )


class Pivot(Select):
    """Like ``Select``, but allows you to shape the data into an arbitrary _wide_ format.

    This class shouldn't be instantiated directly, use ``Project.pivot`` instead. After
    selecting the metrics, you can further refine and shape the pivot by chain-calling
    its methods.

    There's a special dimension called `$`, which represents metric names. By default
    metric names are displayed at the last level of row index, but you can control this
    by calling either `.rows("$")` or `.columns("$")` in the appropriate order.

    Examples:
        ```py
        (
            project.pivot("revenue")
            .rows("sale_date.year")
            .columns("sale_date.month")
        )
        ```

        ```py
        (
            project.pivot("revenue")
            .rows("channel")
            .columns("sale_date.year")
            .columns("$")
        )
        ```
    """

    def __init__(self, project: "dictum.project.Project", *metrics):
        super().__init__(project, *metrics)
        self._rows = []
        self._columns = []
        self._dimensions = []

    def rows(
        self,
        dimension: Union[str, ProjectDimension, ProjectDimensionTransform],
        alias: Optional[str] = None,
    ) -> "Pivot":
        """Add a dimension to the row grouping.

        Arguments:
            dimension:
                One of:

                - Dimension ID in string form to add: ``"date"``
                - String grouping expression with a transform: ``"date.datepart('year')"``
                - Built grouping expression: ``project["date"].datepart("year")``

            alias: An optional alias for the resulting column name. Use this when you
                add the same dimension with different transform multiple times.

        Returns:
            self
        """
        dimension = str(dimension)
        name = alias if alias is not None else dimension
        self._rows.append(name)
        if dimension == "$":
            return self
        return self.by(dimension, alias)

    def columns(
        self,
        dimension: str,
        alias: Optional[str] = None,
    ) -> "Pivot":
        """Add a dimension to the column grouping.

        Arguments:
            dimension:
                One of:

                - Dimension ID in string form to add: ``"date"``
                - String grouping expression with a transform: ``"date.datepart('year')"``
                - Built grouping expression: ``project["date"].datepart("year")``

            alias: An optional alias for the resulting column name. Use this when you
                add the same dimension with different transform multiple times.

        Returns:
            self
        """
        dimension = str(dimension)
        name = alias if alias is not None else dimension
        self._columns.append(name)
        if dimension == "$":
            return self
        return self.by(dimension, alias)

    @cached_property
    def aliased_dimensions(self):
        result = []
        for r in self.query.dimensions:
            name = r.alias if r.alias is not None else r.dimension
            result.append(name)
        return result

    def _get_df(self, data: List[dict]) -> pd.DataFrame:
        if "$" not in self._rows and "$" not in self._columns:
            self._rows.append("$")
        df = super()._get_df(data)
        df = df.melt(id_vars=self.aliased_dimensions, var_name="$", value_name="__")
        df = df.pivot(index=self._rows, columns=self._columns, values="__")
        if isinstance(df, pd.Series):
            df = pd.DataFrame(data=df)
        return df
