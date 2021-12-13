import pytest

from dictum import Project


@pytest.fixture(scope="module")
def project() -> Project:
    return Project.example("chinook")


def test_pivot_in(project: Project):
    project.pivot("revenue").where(project.d.genre.isin("Rock"))
