from functools import cached_property
from typing import List

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import Select, func

from nestor.backends.pandas import PandasColumnTransformer, PandasCompiler
from nestor.backends.sql_alchemy import SQLAlchemyCompiler, SQLAlchemyConnection
from nestor.store import Computation

part_modifiers = {
    "day": "start of day",
    "month": "start of month",
    "year": "start of year",
}


class SQLiteCompiler(SQLAlchemyCompiler):
    def datetrunc(self, args: list):
        part, dt = args
        modifier = part_modifiers[part]
        return func.datetime(dt, modifier)

    def datepart(self, args: list):
        return super().datepart(args)

    def merge_queries(self, queries: List[Select], merge_on: List[str]):
        """SQLite doesn't support outer joins, so we have to materialize here and
        proceed with Pandas.
        """
        dfs = [self.connection.execute(q.select()) for q in queries]
        if len(merge_on) > 0:
            dfs = [df.set_index(merge_on) for df in dfs]
        res = pd.concat(dfs, axis=1)
        if len(merge_on) > 0:
            res = res.reset_index()
        return res

    def calculate_metrics(
        self, computation: Computation, merged: pd.DataFrame
    ) -> pd.DataFrame:
        compiler = PandasCompiler()
        transformer = PandasColumnTransformer([merged])
        for name, tree in computation.metrics.items():
            s = transformer.transform(tree)
            merged[name] = compiler.transformer.transform(s)
        return merged[computation.merge + list(computation.metrics)]


class SQLiteConnection(SQLAlchemyConnection):

    type = "sqlite"
    compiler_cls = SQLiteCompiler

    def __init__(self, database: str):
        super().__init__(drivername="sqlite", database=database)

    @cached_property
    def engine(self):
        return create_engine(self.url)

    def compute(self, computation: Computation) -> pd.DataFrame:
        return self.compiler.compile(computation)
