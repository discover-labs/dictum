import importlib
import logging
from functools import cached_property
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from dictum.backends.base import BackendResult, Connection
from dictum.backends.profiles import ProfilesConfig
from dictum.store import Store
from dictum.store.schema.query import (
    Query,
    QueryDimensionFilter,
    QueryDimensionRequest,
    QueryDimensionTransform,
    QueryMetricRequest,
)

logger = logging.getLogger(__name__)


class Project:
    """
    Internally Dictum works with two main classes: ``Store``, which contains all you
    tables, metrics and dimensions; and ``Connection``, which represents a concrete
    backend implementation. ``Store`` takes a query and transforms it into a
    ``Computation`` object, which is then compiled to SQL by the Connection and executed.

    The ``Project`` class exists to bring everything together. This is what we advise to
    use during the development of your data model.

    Note that this class will read and build the data model on each invocation, so it
    only makes sense to use it if your data model changes between invocations. For
    interactive analysis and applications, see ``CachedProject``, which will read the
    model only once.
    """

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        profiles: Optional[Union[str, Path]] = None,
        profile: Optional[str] = None,
    ):
        """
        Arguments:
            path: Path to either the model YAML file or the
                project directory. If a directory, model config is expected to be in
                ``project.yml`` file. Defaults to current working directory.
            profiles: Path to the profiles config. Defaults to a `profiles.yml`
                file stored in the same directory as the data model file specified by
                ``path``.
            profile: Profile name from ``profiles.yml`` to be used. Defaults to the
                default specified in the config.
        """

        if path is None:
            path = Path.cwd()
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")
        if path.is_dir():
            path = path / "project.yml"
        if profiles is None:
            profiles = path.parent / "profiles.yml"
        if not profiles.is_file():
            raise FileNotFoundError(f"File {profiles} does not exist")
        self.path = path
        self.profiles = profiles
        self.profile = profile

    @property
    def store(self) -> Store:
        return Store.from_yaml(self.path)

    @property
    def connection(self) -> Connection:
        config = ProfilesConfig.from_yaml(self.profiles)
        return config.get_connection(self.profile)

    def execute(self, query: Query) -> BackendResult:
        computation = self.store.get_computation(query)
        return self.connection.compute(computation)

    def select(self, *metrics: str) -> "Select":
        """
        Select metrics from the project.

        Arguments:
            *metrics: Metric IDs to select.

        Returns:
            A ``Select`` object that can be further modified by chain-calling it's
            methods.
        """
        return Select(self, *metrics)

    def pivot(self, *metrics: str) -> "Pivot":
        """Select metrics from the project and construct a pivot table.

        Arguments:
            *metrics: Metric IDs to select.

        Returns:
            A ``Select`` object that can be further modified by chain-calling it's
            methods.
        """
        return Pivot(self, *metrics)

    @classmethod
    def example(cls, name: str) -> "CachedProject":
        """Load an example project.

        Arguments:
            name (str): Name of the example project. Valid values: ``chinook``,
            ``tutorial``.

        Returns:
            CachedProject: same as ``Project``, but won't read the model config at each
                method invocation.
        """
        example = importlib.import_module(f"dictum.examples.{name}.generate")
        return example.generate()

    def describe(self) -> pd.DataFrame:
        """Show project's metrics and dimensions and their compatibility. If a metric
        can be used with a dimension, there will be a ``+`` sign at the intersection of
        their respective row and column.

        Returns:
            pandas.DataFrame: metric-dimension compatibility matrix
        """
        print(
            f"Project '{self.store.name}', {len(self.store.metrics)} metrics, "
            f"{len(self.store.dimensions)} dimensions. "
            f"Connected to {self.connection}."
        )
        data = []
        for metric in self.store.metrics.values():
            for dimension in metric.dimensions:
                data.append((metric.id, dimension.id, "✚"))
        return (
            pd.DataFrame(data=data, columns=["metric", "dimension", "check"])
            .pivot(index="dimension", columns="metric", values="check")
            .fillna("")
        )


class CachedProject(Project):
    """Same as ``Project``, but reads the configs only once. Use this class for
    interactive analysis and applications, when you data model is not expected to change.
    """

    @cached_property
    def store(self) -> Store:
        return super().store

    @cached_property
    def connection(self) -> Connection:
        return super().connection


class Select:
    """Represents a select query that will return the data in the "tall" format.

    This class is not supposed to be instantiated directly, for instantiating use
    ``Project.select(*metrics: str)``.

    After selecting the metrics, the query can be further refined by calling its methods.
    """

    def __init__(self, project: Project, *metrics):
        self.project = project
        self.query = Query(metrics=[QueryMetricRequest(metric=m) for m in metrics])

    def by(
        self,
        dimension: str,
        transform: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> "Select":
        """Add a dimension to the query. Can be called multiple times for adding more
        than one grouping.

        Arguments:
            dimension: Dimension ID to add.
            transform: An optional transform in the form of a string. Must be a function
                call, e.g. ``"datetrunc('month')"``. You can also use a ``dictum.func``
                object to construct the strings in Python. The equivalent of the above
                example is `func.datetrunc("month")`.
            alias: An optional alias for the resulting column name. Use this when you
                add the same dimension with different transform multiple times.

        Returns:
            self

        Examples:
            ```py
            (
                project.select("revenue")
                .by("date", transform="datepart('year')", alias="year")
                .by("date", transform="datepart('month')", alias="month")
            )
            ```

            ```py
            (
                project.select("users_count")
                .by("user_revenue", transform=func.step(100))
            )
            ```


        """
        self.query.dimensions.append(
            QueryDimensionRequest(
                dimension=dimension,
                transform=QueryDimensionTransform.parse(transform),
                alias=alias,
            )
        )
        return self

    def where(self, dimension: str, filter: str) -> "Select":
        """Add a dimension filter to the query.

        Arguments:
            dimension: Dimension ID to filter on.
            filter: Filter expression. Just like transform, must be a function call and
                can be built by calling methods on `dictum.func`.

        Returns:
            self

        Examples:
            ```py
            (
                project.select("revenue")
                .by("date", func.month)
                .where("order_amount", func.atleast(10))
            )
            ```
        """
        self.query.filters.append(
            QueryDimensionFilter(
                dimension=dimension, filter=QueryDimensionTransform.parse(filter)
            )
        )
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
            .rows("sale_date", func.datepart("year"), "year")
            .columns("sale_date", func.datepart("month"), "month")
        )
        ```

        ```py
        (
            project.pivot("revenue")
            .rows("channel")
            .columns("sale_date", func.datepart("year"), "year")
            .columns("$")
        )
        ```
    """

    def __init__(self, client: Project, *metrics):
        super().__init__(client, *metrics)
        self._rows = []
        self._columns = []
        self._dimensions = []

    def rows(
        self,
        dimension: str,
        transform: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> "Pivot":
        """Add a dimension to the row grouping.

        Arguments:
            dimension: Dimension ID to add.
            transform: An optional transform in the form of a string. Must be a function
                call, e.g. ``"datetrunc('month')"``. You can also use a ``dictum.func``
                object to construct the strings in Python. The equivalent of the above
                example is `func.datetrunc("month")`.
            alias: An optional alias for the resulting row index level. Use this when you
                add the same dimension with different transform multiple times.

        Returns:
            self
        """
        name = alias if alias is not None else dimension
        self._rows.append(name)
        if dimension == "$":
            return self
        return self.by(dimension, transform, alias)

    def columns(
        self,
        dimension: str,
        transform: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> "Pivot":
        """Add a dimension to the column grouping.

        Arguments:
            dimension: Dimension ID to add.
            transform: An optional transform in the form of a string. Must be a function
                call, e.g. ``"datetrunc('month')"``. You can also use a ``dictum.func``
                object to construct the strings in Python. The equivalent of the above
                example is `func.datetrunc("month")`.
            alias: An optional alias for the resulting column index level. Use this when
                you add the same dimension with different transform multiple times.

        Returns:
            self
        """
        name = alias if alias is not None else dimension
        self._columns.append(name)
        if dimension == "$":
            return self
        return self.by(dimension, transform, alias)

    @cached_property
    def dimensions(self):
        result = []
        for r in self.query.dimensions:
            name = r.alias if r.alias is not None else r.dimension
            result.append(name)
        return result

    def _get_df(self, data: List[dict]) -> pd.DataFrame:
        df = super()._get_df(data)
        df = (
            df.set_index(self.dimensions)
            .rename_axis(index=self.dimensions, columns="$")
            .unstack(self._columns)
        )
        if len(self._rows) > 1:
            df = df.reorder_levels(self._rows)
        df = df.stack("$")
        return df


class FuncBuilder:
    def __init__(self, name: str):
        self.name = name

    @staticmethod
    def convert(arg):
        if isinstance(arg, str):
            return f"'{arg}'"
        return str(arg)

    def __call__(self, *args):
        arglist = ", ".join(self.convert(a) for a in args)
        return f"{self.name}({arglist})"

    def __str__(self):
        return f"{self.name}()"


class Func:
    def __getattr__(self, name: str):
        return FuncBuilder(name)


func = Func()
