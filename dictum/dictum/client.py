import logging
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from time import perf_counter
from typing import Optional, Union

import pandas as pd

from dictum.backends.base import BackendResult, Connection
from dictum.backends.profiles import ProfilesConfig
from dictum.ql import parse_query
from dictum.store import Store
from dictum.store.schema.query import (
    Query,
    QueryDimensionFilter,
    QueryDimensionRequest,
    QueryDimensionTransform,
    QueryMetricRequest,
)

logger = logging.getLogger(__name__)


@contextmanager
def timer(template: str, ndigits: Optional[int] = None):
    start = perf_counter()
    yield
    dur = round(perf_counter() - start, ndigits=ndigits)
    print(template.format(dur))


class Client:
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
        with timer("Built store in {}s", 2):
            store = Store.from_yaml(self.path)
        return store

    @property
    def connection(self) -> Connection:
        config = ProfilesConfig.from_yaml(self.profiles)
        return config.get_connection(self.profile)

    def execute(self, query: Query) -> BackendResult:
        computation = self.store.get_computation(query)
        with timer("Executed query in {}s", 2):
            result = self.connection.compute(computation)
        return result

    def get_df(self, query: Query) -> pd.DataFrame:
        computation = self.store.get_computation(query)
        with timer("Executed query in {}s", 2):
            df = self.connection.compute_df(computation)
        return df

    def select(self, *metrics) -> "Select":
        return Select(self, *metrics)

    def query(self, ql_query: str) -> pd.DataFrame:
        query = parse_query(ql_query)
        return self.get_df(query)

    def __call__(self, *args, **kwargs):
        return self.select(*args, **kwargs)


class CachedClient(Client):
    @cached_property
    def store(self):
        return super().store

    @cached_property
    def connection(self):
        return super().connection


class Select:
    def __init__(self, client: Client, *metrics):
        self.client = client
        self.query = Query(metrics=[QueryMetricRequest(metric=m) for m in metrics])

    def by(self, dimension: str, transform: Optional[str] = None) -> "Select":
        self.query.dimensions.append(
            QueryDimensionRequest(
                dimension=dimension, transform=QueryDimensionTransform.parse(transform)
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

    def df(self) -> pd.DataFrame:
        return self.client.get_df(self.query)

    def _repr_html_(self):
        return self.df().to_html()


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
