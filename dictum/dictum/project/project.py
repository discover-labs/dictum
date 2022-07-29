import importlib
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

import altair as alt
import pandas as pd

from dictum import schema
from dictum.backends.base import Backend
from dictum.engine import Engine, Result
from dictum.model import Model
from dictum.project import analyses
from dictum.project.calculations import ProjectDimensions, ProjectMetrics
from dictum.project.chart import ProjectChart
from dictum.project.magics import QlMagics
from dictum.project.templates import environment
from dictum.schema import Query


class Project:
    """
    Internally Dictum works with two main classes: ``Store``, which contains all you
    tables, metrics and dimensions; and ``Connection``, which represents a concrete
    backend implementation. ``Store`` takes a query and transforms it into a
    ``Computation`` object, which is then compiled to SQL by the Connection and
    executed.

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
        profile: Optional[str] = None,
    ):
        """
        Arguments:
            path: Path to either the model YAML file or the
                project directory. If a directory, model config is expected to be in
                ``project.yml`` file. Defaults to current working directory.
            profile: Profile name from ``profiles.yml`` to be used. Defaults to the
                default specified in the config.
        """

        if path is None:
            path = Path.cwd()
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")
        self.path = path
        self.profile = profile
        self.m = ProjectMetrics(self)
        self.metrics = self.m
        self.d = ProjectDimensions(self)
        self.dimensions = self.d
        if self.model.theme is not None:
            alt.themes.register("dictum_theme", lambda: self.model.theme)
            alt.themes.enable("dictum_theme")

    @cached_property
    def _project(self) -> schema.Project:
        return schema.Project.load(self.path)

    @cached_property
    def model(self) -> Model:
        return Model(self._project.get_model())

    @cached_property
    def engine(self) -> Engine:
        return Engine(self.model)

    @cached_property
    def backend(self) -> Backend:
        profile = self._project.get_profile(self.profile)
        return Backend.create(profile.type, profile.parameters)

    def execute(self, query: Query) -> Result:
        computation = self.engine.get_computation(query)
        return computation.execute(self.backend)

    def query_graph(self, query: Query):
        computation = self.engine.get_computation(query)
        return computation.graph()

    def ql(self, query: str):
        return analyses.QlQuery(self, query)

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
            f"Project '{self.model.name}', {len(self.model.metrics)} metrics, "
            f"{len(self.model.dimensions)} dimensions. "
            f"Connected to {self.backend}."
        )
        data = []
        for metric in self.model.metrics.values():
            for dimension in metric.dimensions:
                data.append((metric.id, dimension.id, "✚"))
        return (
            pd.DataFrame(data=data, columns=["metric", "dimension", "check"])
            .pivot(index="dimension", columns="metric", values="check")
            .fillna("")
        )

    def magic(self):
        from IPython import get_ipython  # so that linters don't whine

        ip = get_ipython()
        ip.register_magics(QlMagics(project=self, shell=ip))
        print(
            r"The magic is registered, now you can use %ql and %%ql to query "
            f"{self.model.name} project"
        )

    def _repr_html_(self):
        template = environment.get_template("project.html.j2")
        return template.render(project=self)
