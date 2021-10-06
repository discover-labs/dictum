from pathlib import Path

import pytest

from nestor import Store
from nestor.examples import chinook
from nestor.tests.test_store import configs

full_config_path = Path(configs.__file__).parent / "full_correct.yml"
chinook_path = Path(chinook.__file__).parent / "chinook.yml"


@pytest.fixture(scope="session")
def setup_db(tmp_path_factory):
    import sqlite3

    from nestor.examples import chinook

    sql = Path(chinook.__file__).parent / "chinook.sql"
    path = tmp_path_factory.mktemp("chinook") / "chinook.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(sql.read_text())
    yield str(path)


@pytest.fixture(scope="session")
def connection(setup_db):
    from nestor.backends.sql_alchemy import SQLAlchemyConnection

    return SQLAlchemyConnection(drivername="sqlite", database=setup_db)


@pytest.fixture(scope="session")
def store_full():
    return Store.from_yaml(full_config_path)


@pytest.fixture(scope="session")
def chinook():
    return Store.from_yaml(chinook_path)
