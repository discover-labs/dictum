import functools
from typing import Dict

import dictum.project
from dictum import utils
from dictum.data_model import Dimension, Transform
from dictum.project.altair.encoding import AltairEncodingChannelHook, ChannelInfoType
from dictum.project.templates import environment
from dictum.schema.query import QueryDimensionRequest, QueryDimensionTransform


def _repr_other(fn):
    @functools.wraps("fn")
    def wrapped(self, other):
        return fn(self, utils.repr_expr_constant(other))

    return wrapped


dimension_to_encoding_type = {
    "date": "temporal",
    "datetime": "temporal",
    "int": "quantitative",
    "float": "quantitative",
    "str": "nominal",
}


class ProjectDimension(AltairEncodingChannelHook):
    def __init__(self, dimension: Dimension, transforms: Dict[str, Transform]):
        self.dimension = dimension
        self.request = QueryDimensionRequest(dimension=dimension.id)
        self.transforms = transforms

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
        self.request.transform = QueryDimensionTransform(id=name)
        return self

    def __call__(self, *args):
        self.request.transform.args = args
        return self

    def name(self, name: str):
        self.request.alias = name
        return self

    def __str__(self):
        if self.request.transform is None:
            return self.request.dimension
        args = ", ".join(
            utils.repr_expr_constant(a) for a in self.request.transform.args
        )
        if len(args) > 0:
            args = f"({args})"
        alias = ""
        if self.request.alias is not None:
            alias = f' as "{self.request.alias}"'
        return f"{self.request.dimension}.{self.request.transform.id}{args}{alias}"

    def _repr_html_(self):
        template = environment.get_template("calculation.html.j2")
        return template.render(calculation=self.dimension, prefix=":")

    def encoding_fields(self, info: ChannelInfoType) -> dict:
        type_ = self.dimension.type
        if self.request.transform is not None:
            transform = self.transforms.get(self.request.transform.id)
            if transform is None:
                raise KeyError(f"Transform {self.request.transform.id} does not exist")
            if transform.return_type is not None:
                type_ = transform.return_type
        obj = {
            "type": dimension_to_encoding_type[type_],
            "field": f"dimension:{self}",
        }
        title = {"title": self.dimension.name}
        if info == "axis":
            obj.update({"axis": title})
        elif info == "header":
            obj.update({"header": title})
        elif info == "legend":
            obj.update({"legend": title})
        return obj


class ProjectDimensions:
    def __init__(self, project: "dictum.project.Project"):
        transforms = project.store.transforms
        for dimension in project.store.dimensions.values():
            setattr(
                self,
                dimension.id,
                ProjectDimension(dimension, transforms=transforms),
            )
