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
    """Brings connection and store together, executes queries."""

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        profiles: Optional[Union[str, Path]] = None,
        profile: Optional[str] = None,
    ):
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

    def select(self, *metrics) -> "Select":
        return Select(self, *metrics)

    def pivot(self, *metrics):
        return Pivot(self, *metrics)

    @classmethod
    def example(cls, name: str):
        example = importlib.import_module(f"dictum.examples.{name}.generate")
        return example.generate()

    def describe(self):
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
    @cached_property
    def store(self) -> Store:
        return super().store

    @cached_property
    def connection(self) -> Connection:
        return super().connection


class Select:
    def __init__(self, client: Project, *metrics):
        self.client = client
        self.query = Query(metrics=[QueryMetricRequest(metric=m) for m in metrics])

    def by(
        self,
        dimension: str,
        transform: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> "Select":
        self.query.dimensions.append(
            QueryDimensionRequest(
                dimension=dimension,
                transform=QueryDimensionTransform.parse(transform),
                alias=alias,
            )
        )
        return self

    def where(self, dimension: str, filter: Optional[str] = None) -> "Select":
        self.query.filters.append(
            QueryDimensionFilter(
                dimension=dimension, filter=QueryDimensionTransform.parse(filter)
            )
        )
        return self

    def execute(self) -> BackendResult:
        return self.client.execute(self.query)

    def _get_df(self, data: List[dict]) -> pd.DataFrame:
        return pd.DataFrame(data)

    def df(self) -> pd.DataFrame:
        result = self.client.execute(self.query)
        return self._get_df(result.data)

    def _repr_html_(self):
        result = self.client.execute(self.query)
        print(f"Executed query in {result.duration} ms")
        df = self._get_df(result.data)
        return df.to_html()


class Pivot(Select):
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
    ):
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
    ):
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
