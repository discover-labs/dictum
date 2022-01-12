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

import dictum.model
from dictum.backends.base import Compiler, Connection
from dictum.backends.mixins.arithmetic import ArithmeticCompilerMixin
from dictum.engine import Computation, RelationalQuery


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

    def call_window(
        self, fn: str, args: list, partition: list, order: list, rows: list
    ):
        if order:
            order_by = []
            for item in order:
                col, asc = item.children
                col = col.asc() if asc else col.desc()
                order_by.append(col)
            order = order_by
        return super().call_window(fn, args, partition, order, rows)

    def window_sum(self, args, partition, order, rows):
        return func.sum(*args).over(partition_by=partition, order_by=order)

    def window_row_number(self, args, partition, order, rows):
        return func.row_number(*args).over(partition_by=partition, order_by=order)

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

    def compile_query(self, query: RelationalQuery):
        if isinstance(query.source, dictum.model.Table):
            id_ = query.source.id
            table = self._table(query.source.source)
        elif isinstance(query.source, RelationalQuery):
            id_ = None
            table = self.compile_query(query.source)

        tables = {id_: table}

        # replaces column refs with actual SQLA column objs
        column_transformer = ColumnTransformer(tables)

        # join the tables
        for join in query.unnested_joins:
            if isinstance(join.right, RelationalQuery):
                right_table = self.compile_query(join.right)
            else:
                right_table = self._table(join.right.source)
            right_table = right_table.alias(join.right_identity)
            tables[join.right_identity] = right_table
            join_expr = self.transformer.transform(
                column_transformer.transform(join.expr)
            )
            table = table.join(right_table, join_expr, isouter=(not join.inner))

        # add calcs
        columns = {}
        for column in query.columns:
            columns[column.name] = self.transformer.transform(
                column_transformer.transform(column.expr)
            )
        groupby = []
        for expr in query.groupby:
            compiled = self.transformer.transform(column_transformer.transform(expr))
            groupby.append(compiled)

        stmt = (
            select(*(v.label(k) for k, v in columns.items()))
            .select_from(table)
            .group_by(*groupby)
        )

        # apply filters
        for expr in query.filters:
            condition = self.transformer.transform(column_transformer.transform(expr))
            stmt = stmt.where(condition)

        # apply order and limit
        # order only makes sense at this stage if there's a limit
        if query.limit and query.order:
            order_clauses = []
            for item in query.order:
                expr = self.transformer.transform(
                    column_transformer.transform(item.expr)
                )
                if not item.ascending:
                    expr = expr.desc()
                order_clauses.append(expr)
            stmt = stmt.order_by(*order_clauses).limit(query.limit)

        return stmt.subquery()

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

    def calculate(self, computation: Computation, merged: Select) -> Select:
        columns = []
        transformer = ColumnTransformer({None: merged})
        for column in computation.columns:
            resolved_column = transformer.transform(column.expr)
            sql_expr = self.transformer.transform(resolved_column).label(column.name)
            columns.append(sql_expr)
        order_by = [merged.c[c] for c in computation.merge_on]
        return select(*columns).select_from(merged).order_by(*order_by)


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

    def get_raw_query(self, query: Select):
        return sqlparse.format(
            str(query.compile(bind=self.engine)),
            reindent=True,
        )

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
