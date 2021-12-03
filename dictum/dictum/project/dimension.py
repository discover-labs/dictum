from collections import UserDict

import pandas as pd

import dictum.project
from dictum.store import Dimension


def _repr(val):
    if isinstance(val, str):
        return f"'{val}'"
    return str(val)


class ProjectDimensionTransform:
    def __init__(self, dimension: "ProjectDimension", name: str):
        self.dimension = dimension
        self.name = name
        self.args = []

    def __call__(self, *args):
        self.args = args
        return self

    def __str__(self):
        args = ", ".join(_repr(a) for a in self.args)
        if args > "":
            args = f"({args})"
        return f"{self.dimension}.{self.name}{args}"


class ProjectDimension:
    def __init__(self, dimension: Dimension):
        self.dimension = dimension
        self.transform = None

    def __eq__(self, other) -> str:
        return f"{self} = {other}"

    def __ne__(self, other) -> str:
        return f"{self} <> {other}"

    def __gt__(self, other) -> str:
        return f"{self} > {other}"

    def __ge__(self, other) -> str:
        return f"{self} >= {other}"

    def __lt__(self, other) -> str:
        return f"{self} < {other}"

    def __le__(self, other) -> str:
        return f"{self} <= {other}"

    def __getattr__(self, name: str):
        self.transform = ProjectDimensionTransform(self, name)
        return self.transform

    def __str__(self):
        return self.dimension.id


class ProjectDimensions(UserDict):
    def __init__(self, project: "dictum.project.Project"):
        self.project = project

    def __getitem__(self, key: str):
        dimension = self.project.store.dimensions.get(key)
        return ProjectDimension(dimension)

    def _repr_html_(self):
        return pd.DataFrame(
            data=[
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                }
                for d in self.project.store.dimensions.values()
            ]
        ).to_html()
