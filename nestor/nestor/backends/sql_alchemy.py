from functools import cached_property
from typing import List, Optional

import pandas as pd
import sqlparse
from lark import Transformer
from sqlalchemy import (
    Date,
    DateTime,
    Float,
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
    true,
)
from sqlalchemy.engine.url import URL
from sqlalchemy.sql import Select
from sqlalchemy.sql.functions import coalesce

from nestor.backends.base import BackendResult, Compiler, Connection
from nestor.backends.mixins.arithmetic import ArithmeticCompilerMixin
from nestor.store import AggregateQuery, Computation


def get_case_insensitive_column(table: Table, column: str):
    """SQL is case-insensitive, but SQLAlchemy isn't, because columns are stored
    in a dict-like structure, keys exactly as specified in the database. That's
    why this function is needed.
    """
    if column in table.c:
        return table.c[column]
    for k, v in table.c.items():
        if k.lower() == column.lower():
            return v
    raise KeyError(f"Can't find column {column} in table {table.name}")


class ColumnTransformer(Transformer):
    """Replaces columns in the expressions with actual column objects from the join."""

    def __init__(self, tables, visit_tokens: bool = True) -> None:
        self._tables = tables
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children: list):
        identity, field = children
        return get_case_insensitive_column(self._tables[identity], field)

    def measure(self, children: list):
        return get_case_insensitive_column(self._tables[0], children[0])


class SQLAlchemyCompiler(ArithmeticCompilerMixin, Compiler):
    def __init__(self, connection: "SQLAlchemyConnection"):
        self.connection = connection
        super().__init__()

    def column(self, _):
        """A no-op. SQLAlchemy columns need to know about tables,
        so this transformation is done beforehand with ColumnTransformer.
        """

    def IN(self, a, b):
        return a.in_(b)

    def NOT(self, x):
        return not_(x)

    def AND(self, a, b):
        return and_(a, b)

    def OR(self, a, b):
        return or_(a, b)

    def isnull(self, value):
        return value == None  # noqa: E711

    def case(self, whens, else_=None):
        return case(whens, else_=else_)

    def sum(self, args):
        return func.sum(*args)

    def avg(self, args):
        return func.avg(*args)

    def min(self, args):
        return func.min(*args)

    def max(self, args):
        return func.max(*args)

    def count(self, args):
        return func.count(*args)

    def countd(self, args):
        return func.count(distinct(*args))

    def floor(self, args):
        return func.floor(*args)

    def ceil(self, args):
        return func.ceil(*args)

    def abs(self, args):
        return func.abs(*args)

    def coalesce(self, args: list):
        return func.coalesce(*args)

    def tointeger(self, args: list):
        return cast(args[0], Integer)

    def tonumber(self, args: list):
        return cast(args[0], Float)

    def todate(self, args: list):
        return cast(args[0], Date)

    def todatetime(self, args: list):
        return cast(args[0], DateTime)

    def _table(self, source: str):
        *schema, tablename = source.split(".")
        if len(schema) == 0:
            schema = None
        else:
            schema = schema[0]
        return self.connection.table(tablename, schema=schema)

    def compile_query(self, query: AggregateQuery):
        table: Table = self._table(query.table.source)

        tables = {query.table.id: table}
        for join in query.unnested_joins:
            if join.right.subquery:
                right_table = self.compile_query(join.right)
            else:
                right_table = self._table(join.right.table.source)
            right_table = right_table.alias(join.right_identity)
            tables[join.right_identity] = right_table
            related_key = get_case_insensitive_column(right_table, join.right_key)
            foreign_key = get_case_insensitive_column(
                tables[join.left_identity], join.left_key
            )
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

        return stmt.subquery()

    def merge_on_lod(self, a: Select, b: Select, merge_on: List[str]):
        """Merge on level of detail. Like pd.concat, axis=1, but with SQL. Full outer
        join with coalesce on relevant columns.
        """
        if len(merge_on) > 0:
            cond = and_(*(a.c[c] == b.c[c] for c in merge_on))
            join = a.outerjoin(b, onclause=cond, full=True)
        else:
            join = a.join(b, true())
        return select(
            *(coalesce(a.c[c], b.c[c]).label(c) for c in merge_on),
            *(c for c in a.c.values() if c.name not in merge_on),
            *(c for c in b.c.values() if c.name not in merge_on),
        ).select_from(join)

    def merge_queries(self, queries: List[Select], merge_on: List[str]):
        table, *tables = queries
        for t in tables:
            table = self.merge_on_lod(table, t, merge_on)
        return table.subquery() if isinstance(table, Select) else table

    def calculate_metrics(self, computation: Computation, merged: Select) -> Select:
        metrics = []
        transformer = ColumnTransformer([merged])
        for label, tree in computation.metrics.items():
            resolved_metrics = transformer.transform(tree)
            sql_expr = self.transformer.transform(resolved_metrics).label(label)
            metrics.append(sql_expr)
        return select(
            *(merged.c[c] for c in computation.merge),
            *metrics,
        ).select_from(merged)


class SQLAlchemyConnection(Connection):

    type = "sql_alchemy"
    compiler_cls = SQLAlchemyCompiler

    def __init__(
        self,
        drivername: str = "sqlite",
        database: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        pool_size: Optional[int] = None,
    ):
        self.url = URL.create(
            drivername=drivername,
            database=database,
            host=host,
            port=port,
            username=username,
            password=password,
        )
        self.pool_size = pool_size  # TODO: include pool size
        super().__init__()

    @cached_property
    def engine(self):
        return create_engine(self.url, pool_size=self.pool_size)

    @cached_property
    def metadata(self) -> MetaData:
        return MetaData(self.engine)

    def compute(self, computation: Computation) -> BackendResult:
        query = self.compile(computation)
        raw_query = sqlparse.format(str(query.compile()), reindent=True)
        return BackendResult(data=self.execute(query), raw_query=raw_query)

    def execute(self, query) -> List[dict]:
        return pd.read_sql(query, self.engine).to_dict(orient="records")

    def table(self, name: str, schema: Optional[str] = None) -> Table:
        return Table(name, self.metadata, schema=schema, autoload=True)
