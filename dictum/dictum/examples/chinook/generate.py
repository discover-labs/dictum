import os
from pathlib import Path

from dictum import Project


def generate():
    path = Path(__file__).parent
    os.environ["CHINOOK_DATABASE"] = ""
    project = Project(path)
    with project.backend.engine.connect() as conn:
        conn.connection.executescript((path / "chinook.sqlite.sql").read_text())
    return project
