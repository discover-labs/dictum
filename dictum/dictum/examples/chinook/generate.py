import os
from pathlib import Path

from dictum import CachedProject


def generate():
    base = Path(__file__).parent
    path = base / "chinook.yml"
    os.environ["CHINOOK_DATABASE"] = ""
    project = CachedProject(path)
    with project.connection.engine.connect() as conn:
        conn.connection.executescript((base / "chinook.sqlite.sql").read_text())
    return project
