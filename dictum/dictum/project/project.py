import importlib
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

import altair as alt
import pandas as pd

import dictum.project.analyses as analyses
from dictum.backends.base import BackendResult, Connection
from dictum.backends.profiles import ProfilesConfig
from dictum.data_model import DataModel
from dictum.project.calculations import ProjectDimensions, ProjectMetrics
from dictum.project.chart import ProjectChart
from dictum.project.templates import environment
from dictum.ql import compile_query
from dictum.schema import Query


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
        self.m = ProjectMetrics(self)
        self.metrics = self.m
        self.d = ProjectDimensions(self)
        self.dimensions = self.d
        if self.data_model.theme is not None:
            alt.themes.register("dictum_theme", lambda: self.data_model.theme)
            alt.themes.enable("dictum_theme")

    @cached_property
    def data_model(self) -> DataModel:
        return DataModel.from_yaml(self.path)

    @cached_property
    def connection(self) -> Connection:
        config = ProfilesConfig.from_yaml(self.profiles)
        return config.get_connection(self.profile)

    def execute(self, query: Query) -> BackendResult:
        computation = self.data_model.get_computation(query)
        return self.connection.compute(computation)

    def ql(self, query: str):
        q = compile_query(query)
        res = self.execute(q)
        return pd.DataFrame(res.data)

    def select(self, *metrics: str) -> "analyses.Select":
        """
        Select metrics from the project.

        Arguments:
            *metrics: Metric IDs to select.

        Returns:
            A ``Select`` object that can be further modified by chain-calling it's
            methods.
        """
        return analyses.Select(self, *metrics)

    def pivot(self, *metrics: str) -> "analyses.Pivot":
        """Select metrics from the project and construct a pivot table.

        Arguments:
            *metrics: Metric IDs to select.

        Returns:
            A ``Select`` object that can be further modified by chain-calling it's
            methods.
        """
        return analyses.Pivot(self, *metrics)

    @property
    def chart(self) -> ProjectChart:
        return ProjectChart(self)

    @classmethod
    def example(cls, name: str) -> "Project":
        """Load an example project.

        Arguments:
            name (str):
                Name of the example project. Valid values: ``chinook``,
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
            f"Project '{self.data_model.name}', {len(self.data_model.metrics)} metrics, "
            f"{len(self.data_model.dimensions)} dimensions. "
            f"Connected to {self.connection}."
        )
        data = []
        for metric in self.data_model.metrics.values():
            for dimension in metric.dimensions:
                data.append((metric.id, dimension.id, "✚"))
        return (
            pd.DataFrame(data=data, columns=["metric", "dimension", "check"])
            .pivot(index="dimension", columns="metric", values="check")
            .fillna("")
        )

    def _repr_html_(self):
        template = environment.get_template("project.html.j2")
        return template.render(project=self)


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
