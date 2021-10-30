from functools import cached_property
from typing import List

import pandas as pd
from sqlalchemy import Integer, String, create_engine
from sqlalchemy.sql import Select, case, cast, func

from nestor.backends.mixins.datediff import DatediffCompilerMixin
from nestor.backends.pandas import PandasColumnTransformer, PandasCompiler
from nestor.backends.sql_alchemy import SQLAlchemyCompiler, SQLAlchemyConnection
from nestor.store import Computation

trunc_modifiers = {
    "year": ["start of year"],
    "month": ["start of month"],
    "week": ["1 day", "weekday 1", "-7 days", "start of day"],
    "day": ["start of day"],
}

trunc_formats = {
    "hour": r"%Y-%m-%d %H:00:00",
    "minute": r"%Y-%m-%d %H:%M:00",
    "second": r"%Y-%m-%d %H:%M:%S",
}

part_formats = {
    "year": r"%Y",
    "month": r"%m",
    "week": r"%W",
    "day": r"%d",
    "hour": r"%H",
    "minute": r"%M",
    "second": r"%S",
}


class SQLiteCompiler(DatediffCompilerMixin, SQLAlchemyCompiler):
    def floor(self, args):
        arg = args[0]
        return case(
            (arg < 0, cast(arg, Integer) - 1),
            else_=cast(arg, Integer),
        )

    def ceil(self, args):
        arg = args[0]
        return case(
            (arg > 0, cast(arg, Integer) + 1),
            else_=cast(arg, Integer),
        )

    def todate(self, args: list):
        return func.date(args[0])

    def todatetime(self, args: list):
        return func.datetime(args[0])

    def datetrunc(self, args: list):
        part, value = args
        if part in trunc_modifiers:
            modifiers = trunc_modifiers[part]
            return func.datetime(value, *modifiers)
        if part in trunc_formats:
            fmt = trunc_formats[part]
            return func.strftime(fmt, value)
        if part == "quarter":
            year = self.datetrunc(["year", value])
            quarter_part = self.datepart_quarter([value])
            return func.datetime(
                year, "start of year", cast((quarter_part - 1) * 3, String) + " months"
            )
        raise ValueError(
            "Valid values for datetrunc part are year, quarter, "
            "month, week, day, hour, minute, second — "
            f"got '{part}'."
        )

    def datepart_quarter(self, args: list):
        return cast(
            (func.strftime("%m", args[0]) + 2) / 3,
            Integer,
        )

    def datepart(self, args: list):
        part, value = args
        part = part.lower()
        fmt = part_formats.get(part)
        if fmt is not None:
            return cast(func.strftime(fmt, value), Integer)
        if part == "quarter":
            return self.datepart_quarter([value])
        raise ValueError(
            "Valid values for datepart part are year, quarter, "
            "month, week, day, hour, minute, second — "
            f"got '{part}'."
        )

    def datediff_week(self, args: list):
        return cast(super().datediff_week(args), Integer)

    def datediff_day(self, args: list):
        start, end = args
        start_day = func.julianday(self.datetrunc(["day", start]))
        end_day = func.julianday(self.datetrunc(["day", end]))
        return cast(end_day - start_day, Integer)

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
