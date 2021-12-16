from datetime import date, datetime
from functools import cached_property
from typing import Dict, List, Optional, Union

import dateutil.parser
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

from dictum.backends.base import Compiler, Connection
from dictum.backends.mixins.arithmetic import ArithmeticCompilerMixin
from dictum.data_model import AggregateQuery, Computation


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

    def _table(self, source: Union[str, Dict]):
        if isinstance(source, str):
            return self.connection.table(source)
        if isinstance(source, dict):
            schema = source.get("schema")
            table = source.get("table")
            if table is None:
                raise ValueError(f"table is required for a {self.type} backend")
            return self.connection.table(table, schema)
        raise ValueError(f"Source must be a str or a dict for a {self.type} backend")

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
        for column in query.aggregate:
            aggregate[column.name] = self.transformer.transform(
                column_transformer.transform(column.expr)
            )
        for column in query.groupby:
            groupby[column.name] = self.transformer.transform(
                column_transformer.transform(column.expr)
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

    def cross_join(queries: List[Select]):
        table, *tables = queries
        for t in tables:
            table = table.join(t, true())
        return table

    def merge_queries(self, queries: List[Select], merge_on: List[str]):
        table, *tables = queries
        for t in tables:
            cond = (
                and_(*(table.c[c] == t.c[c] for c in merge_on))
                if len(merge_on) > 0
                else true()
            )
            join = table.outerjoin(t, cond, full=True)
            table = (
                select(
                    *(coalesce(table.c[m], t.c[m]).label(m) for m in merge_on),
                    *(c for k, c in table.c.items() if k not in merge_on),
                    *(c for k, c in t.c.items() if k not in merge_on),
                )
                .select_from(join)
                .subquery()
            )
        return table

    def calculate_metrics(self, computation: Computation, merged: Select) -> Select:
        metrics = []
        transformer = ColumnTransformer([merged])
        for column in computation.metrics:
            resolved_metrics = transformer.transform(column.expr)
            sql_expr = self.transformer.transform(resolved_metrics).label(column.name)
            metrics.append(sql_expr)
        merge = [c.name for c in computation.dimensions]
        order_by = [merged.c[name] for name in merge]
        return (
            select(
                *(merged.c[c] for c in merge),
                *metrics,
            )
            .select_from(merged)
            .order_by(*order_by)
        )


def _date_mapper(v):
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return dateutil.parser.parse(v).date()
    if isinstance(v, datetime):
        return v.date()
    return v


def _datetime_mapper(v):
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime.combine(v, datetime.min.time())
    if isinstance(v, str):
        return dateutil.parser.parse(v)
    return v


_type_mappers = {
    "bool": bool,
    "float": float,
    "int": int,
    "str": str,
    "date": _date_mapper,
    "datetime": _datetime_mapper,
}


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

    def get_raw_query(self, query):
        return sqlparse.format(str(query.compile()), reindent=True)

    def execute(self, query: Select) -> List[dict]:
        cur = self.engine.execute(query)
        return [row._asdict() for row in cur.fetchall()]

    def table(self, name: str, schema: Optional[str] = None) -> Table:
        return Table(name, self.metadata, schema=schema, autoload=True)

    def __str__(self):
        return repr(self.engine.url)

    def coerce_types(self, data: List[dict], types: Dict[str, str]):
        for row in data:
            for k, v in row.items():
                if row[k] is None:
                    continue
                row[k] = _type_mappers[types[k]](v)
        return data
