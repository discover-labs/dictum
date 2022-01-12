from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd
from lark import Transformer

from dictum.backends.base import Compiler
from dictum.backends.mixins.arithmetic import ArithmeticCompilerMixin
from dictum.backends.mixins.datediff import DatediffCompilerMixin
from dictum.engine import RelationalQuery


class PandasColumnTransformer(Transformer):
    """Replace column references with pd.Series"""

    def __init__(
        self, tables: Dict[str, pd.DataFrame], visit_tokens: bool = True
    ) -> None:
        self._tables = tables
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children: list):
        identity, column = children
        return self._tables[identity][column]


class PandasCompiler(ArithmeticCompilerMixin, DatediffCompilerMixin, Compiler):
    def column(self, table: str, name: str):
        """Not required, columns are replaced by pd.Series with PandasColumnTransformer"""

    def IN(self, value, values):
        return value.isin(values)

    def NOT(self, value):
        return ~value

    def AND(self, a, b):
        return a & b

    def OR(self, a, b):
        return a | b

    def isnull(self, value):
        return value.isna()

    def case(self, *whens, else_=None):
        return pd.Series(
            np.select(*zip(*whens), default=else_),
            index=whens[0][0].index,
        )

    # built-in functions
    # aggregate

    def sum(self, args: list):
        return args[0].sum()

    def avg(self, args: list):
        return args[0].mean()

    def min(self, args: list):
        return args[0].min()

    def max(self, args: list):
        return args[0].max()

    def count(self, args: list):
        """Aggregate count, with optional argument"""

    def countd(self, args: list):
        return args[0].unique().shape[0]

    # window functions

    def window_sum(self, args, partition, order, rows):
        val = args[0]
        if partition:
            return val.groupby(partition).transform(sum)
        return val.groupby(pd.Series(0, index=val.index)).transform(sum)

    def window_row_number(self, args, partition, order, rows):
        val = args[0]
        if order:
            cols, asc = zip(i.children for i in order)
            df = pd.concat([val, *cols])
            val = df.sort_values(by=df.columns[1:], ascending=asc)
        if partition:
            val = val.groupby([partition])
        return val.cumcount() + 1

    # scalar functions

    def abs(self, args: list):
        return args[0].abs()

    def floor(self, args: list):
        return args[0].floor()

    def ceil(self, args: list):
        return args[0].ceil()

    def coalesce(self, args: list):
        result, *rest = args
        for item in rest:
            result = result.fillna(item)
        return result

    # type casting

    def tointeger(self, args: list):
        return args[0].astype(int)

    def tonumber(self, args: list):
        return args[0].astype(float)

    def todate(self, args: list):
        return pd.to_datetime(args[0]).dt.round("D")

    def todatetime(self, args: list):
        return pd.to_datetime(args[0])

    # dates

    def datepart(self, args: list):
        """Part of a date as an integer. First arg is part as a string, e.g. 'month',
        second is date/datetime.
        """
        return getattr(args[1].dt, args[0])

    def datetrunc(self, args: list):
        """Date truncated to a given part. Args same as datepart."""
        mapping = {
            "year": "YS",
            "month": "MS",
            "day": "D",
        }
        return args[1].dt.round(mapping[args[0]])

    # for DatediffCompilerMixin
    def datediff_day(self, args: list):
        start, end = args
        return (end - start).days

    def now(self, _):
        return datetime.now()

    def today(self, _):
        return datetime.today()

    # compilation

    def compile_query(self, query: RelationalQuery):
        """This is to support SQLite, so not implemented yet."""
        raise NotImplementedError

    def merge_queries(self, queries: List, merge_on: List[str]):
        """This is to support SQLite, so not implemented yet."""
        raise NotImplementedError

    def calculate(self, merged):
        """This is to support SQLite, so not implemented yet."""
        raise NotImplementedError
