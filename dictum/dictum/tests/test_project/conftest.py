import pytest

from dictum import Project


@pytest.fixture(scope="module")
def project() -> Project:
    return Project.example("chinook")
