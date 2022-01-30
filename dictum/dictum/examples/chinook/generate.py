import os
from pathlib import Path

from dictum import Project


def generate():
    base = Path(__file__).parent
    path = base / "chinook.yml"
    os.environ["CHINOOK_DATABASE"] = ""
    project = Project(path)
    with project.backend.engine.connect() as conn:
        conn.connection.executescript((base / "chinook.sqlite.sql").read_text())
    return project
