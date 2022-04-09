import os
import shlex
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import psycopg2
import pytest

from dictum import schema
from dictum.examples import chinook
from dictum.model import Model
from dictum.tests.test_model import configs

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
    from dictum.backends import PostgresBackend

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
        yield PostgresBackend(
            database=params["dbname"],
            host=params["host"],
            username=params["user"],
            password=params["password"],
        )
    finally:
        stop()


@contextmanager
def sqlite():
    from dictum.examples.chinook.generate import generate

    yield generate().backend


@pytest.fixture(scope="session", params=[sqlite, postgres])
def backend(request):
    with request.param() as backend:
        yield backend


@pytest.fixture(scope="session")
def project(backend):
    from dictum import Project

    project = Project.example("chinook")
    project.backend = backend
    yield project


@pytest.fixture(scope="session")
def store_full():
    return Model.from_yaml(full_config_path)


@pytest.fixture(scope="session")
def chinook():
    os.environ["CHINOOK_DATABASE"] = ""
    return Model(schema.Project.load(chinook_path).get_model())


@pytest.fixture(scope="session")
def engine():
    from dictum.engine import Engine

    return Engine()
