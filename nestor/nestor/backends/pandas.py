from typing import Dict, List

import numpy as np
import pandas as pd
from lark import Transformer

from nestor.backends.arithmetic import ArithmeticCompilerMixin
from nestor.backends.base import Compiler
from nestor.store import RelationalQuery


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

    def measure(self, children: list):
        return self._tables[0][children[0]]


class PandasCompiler(ArithmeticCompilerMixin, Compiler):
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

    # scalar functions

    def abs(self, args: list):
        return args[0].abs()

    def floor(self, args: list):
        return args[0].floor()

    def ceil(self, args: list):
        return args[0].ceil()

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

    # compilation

    def compile_query(self, query: RelationalQuery):
        """This is to support SQLite, so not implemented yet."""
        raise NotImplementedError

    def merge_queries(self, queries: List, merge_on: List[str]):
        """This is to support SQLite, so not implemented yet."""
        raise NotImplementedError

    def calculate_metrics(self, merged):
        """This is to support SQLite, so not implemented yet."""
        raise NotImplementedError
