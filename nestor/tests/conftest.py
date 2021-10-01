import sqlite3
from pathlib import Path

import pytest

from nestor import Store
from nestor.store.schema import Config
from tests.test_store import configs

full_config_path = Path(configs.__file__).parent / "full_correct.yml"
chinook_path = Path(configs.__file__).parent / "chinook.yml"


@pytest.fixture(scope="session")
def chinook_db(tmp_path_factory):
    from nestor.examples import chinook

    sql = Path(chinook.__file__).parent / "chinook.sql"
    path = tmp_path_factory.mktemp("chinook") / "chinook.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(sql.read_text())
    yield str(path)


@pytest.fixture(scope="session")
def config_full():
    return Config.from_yaml(full_config_path)


@pytest.fixture(scope="session")
def store_full(config_full: Config):
    return Store(config_full)


@pytest.fixture(scope="session")
def chinook():
    return Store.from_yaml(chinook_path)
