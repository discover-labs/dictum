import os
from pathlib import Path
from typing import Optional

import typer
import uvicorn

app = typer.Typer()


def get_profiles_config_path(cli_option: Optional[Path] = None) -> str:
    if cli_option is not None:
        return str(cli_option)
    envvar = os.getenv("NESTOR_PROFILES_CONFIG_PATH")
    if envvar is not None:
        if Path(envvar).is_file():
            return envvar
        raise FileNotFoundError(f"Profiles config {envvar} not found")
    cwd = Path.cwd() / "profiles.yml"
    if cwd.is_file():
        return str(cwd)
    raise ValueError("Profiles config not found")


@app.command()
def run(
    store_config_path: Path = typer.Option(
        ..., dir_okay=False, envvar="NESTOR_STORE_CONFIG_PATH"
    ),
    profiles_config_path: Optional[Path] = None,
    profile: Optional[str] = None,
):
    os.environ["NESTOR_STORE_CONFIG_PATH"] = str(store_config_path)
    os.environ["NESTOR_PROFILES_CONFIG_PATH"] = get_profiles_config_path(
        profiles_config_path
    )
    if profile is not None:
        os.environ["NESTOR_PROFILE"] = profile
    uvicorn.run("dictum.server:app", reload=True)


@app.command()
def version():
    from dictum import __version__

    typer.echo(f"dictum v{__version__}")
