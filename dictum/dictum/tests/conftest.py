import shlex
import shutil
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import mkdtemp

import psycopg2
import pytest

from dictum import Store
from dictum.examples import chinook
from dictum.tests.test_store import configs

full_config_path = Path(configs.__file__).parent / "full_correct.yml"
chinook_path = Path(chinook.__file__).parent


container_name = "test-dictum-backend-postgres"

db_script = str((Path(__file__).parent / "chinook.postgres.sql").resolve())


def stop(fail=False):
    cmd = shlex.split(f"docker stop {container_name}")
    try:
        subprocess.check_call(cmd)
    except subprocess.SubprocessError:
        if fail:
            raise


@contextmanager
def postgres():
    from dictum.backends import PostgresConnection

    script = chinook_path / "chinook.postgres.sql"
    cmd = shlex.split(
        f"docker run -d --rm --name {container_name} -p 5432:5432 "
        "-e POSTGRES_USER=chinook -e POSTGRES_PASSWORD=chinook "
        f"-v {script}:/script.sql "
        "postgres"
    )
    subprocess.check_call(cmd)
    params = dict(
        host="localhost", dbname="chinook", user="chinook", password="chinook"
    )
    for _ in range(30):
        try:
            psycopg2.connect(**params)
            break
        except psycopg2.OperationalError:
            time.sleep(1)

    restore_cmd = shlex.split(
        f"docker container exec {container_name} psql -U chinook -W chinook -f /script.sql"
    )
    subprocess.check_call(restore_cmd)
    try:
        yield PostgresConnection(
            database=params["dbname"],
            host=params["host"],
            username=params["user"],
            password=params["password"],
        )
    finally:
        stop()


@contextmanager
def sqlite():
    import sqlite3

    from dictum.backends.sqlite import SQLiteConnection

    script = chinook_path / "chinook.sqlite.sql"
    tempdir = Path(mkdtemp())
    database = tempdir / "chinook.db"
    with sqlite3.connect(database) as conn:
        conn.executescript(script.read_text())

    try:
        yield SQLiteConnection(str(database))
    finally:
        shutil.rmtree(tempdir)


@pytest.fixture(scope="session", params=[sqlite, postgres])
def connection(request):
    with request.param() as conn:
        yield conn


@pytest.fixture(scope="session")
def store_full():
    return Store.from_yaml(full_config_path)


@pytest.fixture(scope="session")
def chinook():
    return Store.from_yaml(chinook_path / "chinook.yml")
