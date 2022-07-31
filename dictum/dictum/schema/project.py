import os
from getpass import getpass
from itertools import chain
from pathlib import Path
from typing import Dict, Optional, Union

import yaml
from jinja2 import Template
from pydantic import BaseModel

from dictum.schema.id import ID
from dictum.schema.model import Model

root_items = {"tables", "metrics", "unions", "profiles"}


def _merge(target: dict, source: dict):
    result = target.copy()
    for k, v in source.items():
        if k in root_items:
            result[k] = _merge(result.get(k, {}), source[k])
            continue
        if k in result:
            raise KeyError(f"Duplicate key in project config: {k}")
        result[k] = v
    return result


class Env:
    def __init__(self):
        self.data = os.environ.copy()

    def __getattr__(self, key: str):
        try:
            return self.data[key]
        except KeyError:
            val = getpass(key)
            self.data[key] = val
            return val


env = Env()


def _load_yaml_template(path: Path):
    return yaml.load(Template(path.read_text()).render(env=env), Loader=yaml.SafeLoader)


def _load_dict_from_path(path: Union[str, Path]) -> dict:
    """Load a single YAML file or multiple YAML files in nested folders."""
    path = Path(path)
    if path.is_file():
        result = _load_yaml_template(path)
        if not isinstance(result, dict):
            raise TypeError(f"Error loading {path}: top-level object must be a dict")
        return result

    if path.is_dir():
        result = {}
        for file in chain(path.glob("**/*.yml"), path.glob("**/*.yaml")):
            key = file.stem
            data = _load_yaml_template(file)
            if not isinstance(data, dict):
                raise TypeError(
                    f"Error loading {path}: top-level object must be a dict"
                )
            result[key] = data
        return result

    raise FileNotFoundError(f"Path {path} does not exist")


class Profile(BaseModel):
    type: str
    parameters: dict = {}


class Profiles(BaseModel):
    default_profile: str
    profiles: Dict[ID, Profile]


class Project(BaseModel):
    name: str
    description: Optional[str]
    locale: str = "en_US"
    currency: str = "USD"

    tables_path: str = "tables"
    metrics_path: str = "metrics"
    unions_path: str = "unions.yml"
    profiles_path: str = "profiles.yml"

    root: Path

    @classmethod
    def load(cls, path: Union[str, Path]):
        path = Path(path)
        if not path.is_dir():
            raise FileNotFoundError("Project path must be a directory")
        project_yml = path / "project.yml"
        if not project_yml.is_file():
            raise FileNotFoundError(
                "Project must contain a project.yml file at the root"
            )
        data = _load_yaml_template(project_yml)
        data["root"] = str(path)
        return cls.parse_obj(data)

    def get_profile(self, profile=None) -> dict:
        data = _load_yaml_template(self.root / self.profiles_path)
        profiles = Profiles.parse_obj(data)
        profile = profiles.default_profile if profile is None else profile
        try:
            return profiles.profiles[profile]
        except KeyError:
            raise KeyError(f"Profile {profile} is not present in profiles")

    def get_model(self) -> Model:
        data = {}
        data["tables"] = _load_dict_from_path(self.root / self.tables_path)
        data["metrics"] = _load_dict_from_path(self.root / self.metrics_path)
        data["unions"] = _load_dict_from_path(self.root / self.unions_path)
        data.update(self.dict(include={"name", "description", "locale", "currency"}))
        return Model.parse_obj(data)
