from functools import cached_property
from typing import Optional

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

from nestor.backends.base import Compiler
from nestor.store import Computation


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

    def compile(self, computation: Computation):
        tree = computation.join_tree
        table: Table = self._table(tree.table.source)

        tables = {tree.identity: table}
        for join in tree.unnested_joins:
            right_table = self._table(join.right_source).alias(join.right_identity)
            tables[join.right_identity] = right_table
            related_key = right_table.c[join.right_key]
            foreign_key = tables[join.left_identity].c[join.left_key]
            table = table.outerjoin(right_table, foreign_key == related_key)

        measures = {}
        dimensions = {}
        column_transformer = ColumnTransformer(tables)
        for key, expr in computation.measures.items():
            measures[key] = self.transformer.transform(
                column_transformer.transform(expr)
            )
        for key, expr in computation.dimensions.items():
            dimensions[key] = self.transformer.transform(
                column_transformer.transform(expr)
            )

        stmt = (
            select(
                *(v.label(k) for k, v in dimensions.items()),
                *(v.label(k) for k, v in measures.items()),
            )
            .select_from(table)
            .group_by(*dimensions.values())
        )

        for expr in computation.filters:
            condition = self.transformer.transform(column_transformer.transform(expr))
            stmt = stmt.where(condition)

        return stmt


class SQLAlchemyConnection:
    def __init__(
        self,
        drivername="sqlite",
        database=None,
        host=None,
        port=None,
        username=None,
        password=None,
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

    @cached_property
    def engine(self):
        return create_engine(self.url)

    @cached_property
    def metadata(self) -> MetaData:
        return MetaData(self.engine)

    def execute(self, computation: Computation) -> pd.DataFrame:
        query = self.compiler.compile(computation)
        return pd.read_sql(query, self.engine)

    def table(self, name: str, schema: Optional[str] = None) -> Table:
        return Table(name, self.metadata, schema=schema, autoload=True)
