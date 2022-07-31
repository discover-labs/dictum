from pathlib import Path

from typer.testing import CliRunner

from dictum.cli import app

runner = CliRunner()


def test_new(tmp_path: Path):
    test = tmp_path / "test"
    result = runner.invoke(app, args=["new"], input=f"{str(test)}\nTest project\n1\n\n")
    assert result.exit_code == 0
    assert test.is_dir()
    assert (test / "project.yml").exists()
