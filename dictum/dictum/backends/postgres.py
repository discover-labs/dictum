from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Integer
from sqlalchemy.sql import cast, func

from dictum.backends.mixins.datediff import DatediffCompilerMixin
from dictum.backends.sql_alchemy import SQLAlchemyCompiler, SQLAlchemyConnection
from dictum.store import Computation


class PostgresCompiler(DatediffCompilerMixin, SQLAlchemyCompiler):
    def datepart(self, args: list):
        # cast cause date_part returns double
        return cast(func.date_part(*args), Integer)

    def datetrunc(self, args: list):
        return func.date_trunc(*args)

    def datediff_day(self, args: list):
        start = self.datetrunc(["day", args[0]])
        end = self.datetrunc(["day", args[1]])
        return self.datepart(["day", end - start])  # the argument is an interval

    def now(self, _):
        return func.now()

    def today(self, _):
        return self.todate(func.now())


class PostgresConnection(SQLAlchemyConnection):
    type = "postgres"
    compiler_cls = PostgresCompiler

    def __init__(
        self,
        database: str = "postgres",
        host: str = "localhost",
        port: int = 5432,
        username: str = "postgres",
        password: Optional[str] = None,
        pool_size: Optional[int] = 5,
    ):
        super().__init__(
            drivername="postgresql",
            database=database,
            host=host,
            port=port,
            username=username,
            password=password,
            pool_size=pool_size,
        )

    def coerce_types(self, data: List[dict], computation: Computation):
        columns = [*computation.metrics, *computation.dimensions]
        types = {c.name: c.type for c in columns}
        for row in data:
            for k, v in row.items():
                if types[k] in {"number", "decimal", "percent", "currency"}:
                    if isinstance(row[k], Decimal):
                        row[k] = float(v)
        return data
