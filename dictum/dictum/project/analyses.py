from typing import List, Union

from pandas import DataFrame

from dictum import engine, project
from dictum.project.calculations import ProjectDimensionRequest
from dictum.project.formatting import Formatter
from dictum.ql import (
    compile_dimension,
    compile_dimension_request,
    compile_metric_request,
    compile_query,
)
from dictum.schema import Query


class Analysis:
    def __init__(self, project: "project.Project", *metrics):
        self.project = project
        self.query = Query(metrics=[compile_metric_request(str(m)) for m in metrics])

    def _execute(self) -> engine.Result:
        return self.project.execute(self.query)

    def _get_df(self, result: "engine.Result") -> DataFrame:
        return DataFrame(result.data)

    def df(self, *, format: bool = False) -> DataFrame:
        """Execute the query and return a Pandas DataFrame. In Jupyter, if you don't
        need to store the result in a variable and want to just see the data, you can
        skip calling this method. ``Select``'s representation in Jupyter is its result.
        """
        result = self._execute()
        if format:
            return self._get_formatted_df(result)
        return self._get_df(result)

    def _get_formatted_df(self, result: "engine.Result") -> DataFrame:
        if len(result.data) == 0:
            return DataFrame(result.data)
        formatter = Formatter(
            locale=self.project.model.locale,
            formats={k: v.format for k, v in result.display_info.items()},
        )
        df = DataFrame(formatter.format(result.data))
        df.columns = [result.display_info[c].name for c in df.columns]
        return df

    def graph(self):
        return self.project.query_graph(self.query)

    @property
    def queries(self) -> List[str]:
        return self.project.execute(self.query).executed_queries

    def _repr_html_(self):
        return self.df(format=True).to_html(max_rows=20)

    def dimensions(self):
        dimensions = self.project.model.suggest_dimensions(self.query)
        return DataFrame(
            data=[
                {"id": d.id, "name": d.name, "description": d.description}
                for d in dimensions
            ]
        )

    def metrics(self):
        metrics = self.project.model.suggest_metrics(self.query)
        return DataFrame(
            data=[
                {"id": m.id, "name": m.name, "description": m.description}
                for m in metrics
            ]
        )


class Select(Analysis):
    """Represents a select query that will return the data in the "tall" format.

    This class is not supposed to be instantiated directly, for instantiating use
    ``Project.select(*metrics: str)``.

    After selecting the metrics, the query can be further refined by calling its methods.
    """

    def by(self, *dimensions) -> "Select":
        """Add one or more dimensions to the query. Can be called multiple times for
        adding more than one grouping.

        Arguments:
            dimensions:
                List of one of:

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
        for dimension in dimensions:
            if isinstance(dimension, ProjectDimensionRequest):
                request = dimension.request
            else:
                request = compile_dimension_request(str(dimension))
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
            self.query.filters.append(compile_dimension(str(f)))
        return self

    def limit(self, *filters):
        for f in filters:
            self.query.limit.append(compile_metric_request(str(f)).metric)
        return self


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

    def __init__(self, project: "project.Project", *metrics):
        super().__init__(project, *metrics)
        self._rows = []
        self._columns = []

    def rows(self, *dimensions: Union[str, ProjectDimensionRequest]) -> "Pivot":
        """Add a dimension to the row grouping.

        Arguments:
            dimension:
                One of:

                - Dimension ID in string form to add: ``"date"``
                - String grouping expression with a transform: ``"date.datepart('year')"``
                - Built grouping expression: ``project.date.year.name("year")``

            alias: An optional alias for the resulting column name. Use this when you
                add the same dimension with different transform multiple times.

        Returns:
            self
        """
        for dimension in dimensions:
            if isinstance(dimension, str) and dimension == "$":
                self._rows.append(dimension)
            else:
                self.by(dimension)
                dim = self.query.dimensions[-1]
                name = dim.alias if dim.alias is not None else dim.name
                self._rows.append(name)
        return self

    def columns(self, *dimensions: Union[str, ProjectDimensionRequest]) -> "Pivot":
        """Add a dimension to the column grouping.

        Arguments:
            dimension:
                One of:

                - Dimension ID in string form to add: ``"date"``
                - String grouping expression with a transform: ``"date.datepart('year')"``
                - Built grouping expression: ``project.date.datepart("year")``

            alias: An optional alias for the resulting column name. Use this when you
                add the same dimension with different transform multiple times.

        Returns:
            self
        """
        for dimension in dimensions:
            if isinstance(dimension, str) and dimension == "$":
                self._columns.append(dimension)
            else:
                self.by(dimension)
                dim = self.query.dimensions[-1]
                name = dim.alias if dim.alias is not None else dim.name
                self._columns.append(name)
        return self

    def _pivot(self, df: DataFrame, rows: List[str], columns: List[str]) -> DataFrame:
        columns = [*columns]
        rows = [*rows]
        df.columns.rename("$", inplace=True)
        if len(rows) == 0 and len(columns) == 0:
            return df

        dimensions = [(r.alias or r.name) for r in self.query.dimensions]
        df = df.melt(id_vars=dimensions, value_name="__")

        if "$" not in rows and "$" not in rows:
            columns.append("$")
        if len(rows) == 0:
            df[0] = 0
            rows.append(0)

        df = df.pivot(index=rows, columns=columns, values="__")
        if df.index.nlevels == 1 and df.index.name == 0:
            df.index.name = None

        return df

    def df(self) -> DataFrame:
        df = super().df()
        rows = [*self._rows]
        columns = [*self._columns]
        return self._pivot(df, rows, columns)

    def _repr_html_(self):
        return self.df().to_html(max_rows=20)


class QlQuery(Analysis):
    def __init__(self, project: "project.Project", query: str):
        # not calling super().__init__, because have to parse the query
        self.project = project
        self.query = compile_query(query)
