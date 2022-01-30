import os
from pathlib import Path
from typing import Any, Dict, Optional

import pkg_resources
import yaml
from jinja2 import Template
from pydantic import BaseModel

from dictum.backends.base import Backend


class Env:
    def __init__(self):
        self.data = os.environ

    def __getattr__(self, key: str):
        try:
            return self.data[key]
        except KeyError:
            raise KeyError(f"Environment variable {key} is not defined")


class Profile(BaseModel):
    type: str
    parameters: Dict[str, Any]


class ProfilesConfig(BaseModel):
    default: str
    profiles: Dict[str, Profile]

    @classmethod
    def from_yaml(cls, path: str):
        path = Path(path)
        template = Template(path.read_text())
        rendered = template.render(env=Env())
        data = yaml.load(rendered, Loader=yaml.SafeLoader)
        return cls.parse_obj(data)

    def get_profile(self, profile: Optional[str] = None) -> Profile:
        if profile is None:
            result = self.profiles.get(self.default)
        else:
            result = self.profiles.get(profile)
        if result is None:
            raise KeyError(f"Profile {profile} doesn't exist")
        return result

    def get_backend(self, profile: Optional[str] = None) -> Backend:
        profile = self.get_profile(profile)
        connection_cls = Backend.registry.get(profile.type)
        if connection_cls is None:
            connection_cls = self.get_plugin_connection(profile.type)
        return connection_cls(**profile.parameters)

    def get_plugin_connection(self, type: str):
        for entry_point in pkg_resources.iter_entry_points(
            "dictum.backends", name=type
        ):
            return entry_point.load()
        raise ImportError(
            f"Backend {type} was not found. Try installing dictum-backend-{type} package."
        )
