from functools import cached_property
from typing import Optional

import numpy as np
import pandas as pd
from lark import Transformer
from sqlalchemy import (
    Integer,
    MetaData,
    Table,
    and_,
    case,
    cast,
    create_engine,
    distinct,
    func,
    not_,
    or_,
    select,
)
from sqlalchemy.engine.url import URL

from nestor.backends.base import Compiler, Connection
from nestor.store import Computation, RelationalQuery


class ColumnTransformer(Transformer):
    """Replaces columns in the expressions with actual column objects from the join."""

    def __init__(self, tables, visit_tokens: bool = True) -> None:
        self._tables = tables
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children: list):
        identity, field = children
        return self._tables[identity].c[field]


class SQLAlchemyCompiler(Compiler):
    def __init__(self, connection: "SQLAlchemyConnection"):
        self.connection = connection
        super().__init__()

    def INTEGER(self, token):
        return int(token)

    def FLOAT(self, token):
        return float(token)

    def STRING(self, token):
        return str(token)

    def AND(self, a, b):
        return and_(a, b)

    def OR(self, a, b):
        return or_(a, b)

    def NOT(self, x):
        return not_(x)

    def IN(self, a, b):
        return a.in_(b)

    def eq(self, a, b):
        return a == b

    def neq(self, a, b):
        return a != b

    def add(self, a, b):
        return a + b

    def sub(self, a, b):
        return a - b

    def mul(self, a, b):
        return a * b

    def div(self, a, b):
        return a / b

    def count(self, args):
        return func.count(*args)

    def distinct(self, args):
        return func.count(distinct(*args))

    def sum(self, args):
        return func.sum(*args)

    def avg(self, args):
        return func.avg(*args)

    def min(self, args):
        return func.min(*args)

    def max(self, args):
        return func.max(*args)

    def floor(self, args):
        """For supporing SQLite, which doesn't have floor."""
        arg = args[0]
        return case(
            (arg < 0, cast(arg, Integer) - 1),
            else_=cast(arg, Integer),
        )

    def ceil(self, args):
        """For supporing SQLite, which doesn't have ceil."""
        arg = args[0]
        return case(
            (arg > 0, cast(arg, Integer) + 1),
            else_=cast(arg, Integer),
        )

    def _table(self, source: str):
        *schema, tablename = source.split(".")
        if len(schema) == 0:
            schema = None
        else:
            schema = schema[0]
        return self.connection.table(tablename, schema=schema)

    def compile_query(self, query: RelationalQuery):
        tree = query.join_tree
        table: Table = self._table(tree.table.source)

        tables = {tree.identity: table}
        for join in tree.unnested_joins:
            right_table = self._table(join.right_source).alias(join.right_identity)
            tables[join.right_identity] = right_table
            related_key = right_table.c[join.right_key]
            foreign_key = tables[join.left_identity].c[join.left_key]
            table = table.outerjoin(right_table, foreign_key == related_key)

        aggregate = {}
        groupby = {}
        column_transformer = ColumnTransformer(tables)
        for key, expr in query.aggregate.items():
            aggregate[key] = self.transformer.transform(
                column_transformer.transform(expr)
            )
        for key, expr in query.groupby.items():
            groupby[key] = self.transformer.transform(
                column_transformer.transform(expr)
            )

        stmt = (
            select(
                *(v.label(k) for k, v in groupby.items()),
                *(v.label(k) for k, v in aggregate.items()),
            )
            .select_from(table)
            .group_by(*groupby.values())
        )

        for expr in query.filters:
            condition = self.transformer.transform(column_transformer.transform(expr))
            stmt = stmt.where(condition)

        return stmt

    def compile(self, computation: Computation):
        return [self.compile_query(f) for f in computation.queries]


class SQLAlchemyConnection(Connection):

    type = "sql_alchemy"

    def __init__(
        self,
        drivername="sqlite",
        database=None,
        host=None,
        port=None,
        username=None,
        password=None,
        pool_size: Optional[int] = None,
    ):
        self.compiler = SQLAlchemyCompiler(self)
        self.url = URL.create(
            drivername=drivername,
            database=database,
            host=host,
            port=port,
            username=username,
            password=password,
        )
        self.pool_size = pool_size  # TODO: include pool size

    @cached_property
    def engine(self):
        return create_engine(self.url)

    @cached_property
    def metadata(self) -> MetaData:
        return MetaData(self.engine)

    def execute(self, computation: Computation) -> pd.DataFrame:
        df = None
        for query in self.compiler.compile(computation):
            result = pd.read_sql(query, self.engine)
            if len(computation.merge) > 0:
                result = result.set_index(computation.merge)
            if df is None:
                df = result
            else:
                df = pd.merge(
                    df, result, how="outer", left_index=True, right_index=True
                )
        if len(computation.merge) > 0:
            df = df.reset_index()
        return df.replace([np.nan], [None])

    def table(self, name: str, schema: Optional[str] = None) -> Table:
        return Table(name, self.metadata, schema=schema, autoload=True)
