import os
from pathlib import Path

import pytest

from dictum import schema
from dictum.examples import chinook
from dictum.model import Model

chinook_path = Path(chinook.__file__).parent


@pytest.fixture(scope="session")
def backend():
    from dictum.examples.chinook.generate import generate

    yield generate().backend


@pytest.fixture(scope="session")
def project(backend):
    from dictum import Project

    project = Project.example("chinook")
    project.backend = backend
    yield project


@pytest.fixture(scope="session")
def chinook():
    os.environ["CHINOOK_DATABASE"] = ""
    return Model(schema.Project.load(chinook_path).get_model())


@pytest.fixture(scope="session")
def engine():
    from dictum.engine import Engine

    return Engine()
