from typing import Optional

from sqlalchemy import Integer
from sqlalchemy.sql import cast, func

from nestor.backends.sql_alchemy import SQLAlchemyCompiler, SQLAlchemyConnection


class PostgresCompiler(SQLAlchemyCompiler):
    def datepart(self, args: list):
        # cast cause date_part returns double
        return cast(func.date_part(*args), Integer)

    def datetrunc(self, args: list):
        return func.date_trunc(*args)


class PostgresConnection(SQLAlchemyConnection):
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
