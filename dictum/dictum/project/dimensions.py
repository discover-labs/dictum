import functools

import dictum.project
from dictum import utils
from dictum.project.templates import environment
from dictum.store import Dimension


def _repr_other(fn):
    @functools.wraps("fn")
    def wrapped(self, other):
        return fn(self, utils.repr_expr_constant(other))

    return wrapped


class ProjectDimensionTransform:
    def __init__(self, dimension: "ProjectDimension", name: str):
        self.dimension = dimension
        self.name = name
        self.args = []

    def __call__(self, *args):
        self.args = args
        return self

    def __str__(self):
        args = ", ".join(utils.repr_expr_constant(a) for a in self.args)
        if args > "":
            args = f"({args})"
        return f"{self.dimension}.{self.name}{args}"


class ProjectDimension:
    def __init__(self, dimension: Dimension):
        self.dimension = dimension

    @_repr_other
    def __eq__(self, other) -> str:
        return f"{self} = {other}"

    @_repr_other
    def __ne__(self, other) -> str:
        return f"{self} <> {other}"

    @_repr_other
    def __gt__(self, other) -> str:
        return f"{self} > {other}"

    @_repr_other
    def __ge__(self, other) -> str:
        return f"{self} >= {other}"

    @_repr_other
    def __lt__(self, other) -> str:
        return f"{self} < {other}"

    @_repr_other
    def __le__(self, other) -> str:
        return f"{self} <= {other}"

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)  # for Jupyter checking for _repr_html_ etc.
        return ProjectDimensionTransform(self, name)

    def __str__(self):
        return self.dimension.id

    def _repr_html_(self):
        template = environment.get_template("calculation.html.j2")
        return template.render(calculation=self.dimension, prefix=":")


class ProjectDimensions:
    def __init__(self, project: "dictum.project.Project"):
        for dimension in project.store.dimensions.values():
            setattr(self, dimension.id, ProjectDimension(dimension))
