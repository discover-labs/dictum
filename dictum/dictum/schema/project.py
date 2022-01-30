import os
from pathlib import Path
from typing import Dict, Union

import yaml
from jinja2 import Template
from pydantic import BaseModel

from dictum.schema.model.model import Model


class Profile(BaseModel):
    type: str
    parameters: dict


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
        self.data = os.environ

    def __getattr__(self, key: str):
        try:
            return self.data[key]
        except KeyError:
            raise KeyError(f"Environment variable {key} is not defined")


class Project(Model):
    default_profile: str
    profiles: Dict[str, Profile] = {}

    @classmethod
    def from_yaml(cls, path: Union[str, Path]):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Path {str(path)} does not exist")

        result = {}
        paths = []
        if path.is_dir():
            paths = path.glob("**/*.yml")
        elif path.is_file():
            paths = [path]

        for p in paths:
            template = Template(p.read_text())
            rendered = template.render(env=Env())
            data = yaml.load(rendered, Loader=yaml.SafeLoader)
            result = _merge(result, data)

        return cls.parse_obj(result)
