import functools
from typing import Dict

import dictum.project
from dictum import utils
from dictum.data_model import Dimension, Transform
from dictum.project.altair.encoding import AltairEncodingChannelHook, cls_to_info_type
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


class ProjectDimensionRequest(AltairEncodingChannelHook):
    def __init__(self, dimension: Dimension, transforms: Dict[str, Transform]):
        self.dimension = dimension
        self.request = QueryDimensionRequest(dimension=dimension.id)
        self.transforms = transforms

    def __eq__(self, other):
        return self.eq(other)

    def __ne__(self, other):
        return self.ne(other)

    def __gt__(self, other):
        return self.gt(other)

    def __ge__(self, other) -> str:
        return self.ge(other)

    def __lt__(self, other) -> str:
        return self.lt(other)

    def __le__(self, other) -> str:
        return self.le(other)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)  # for Jupyter checking for _repr_html_ etc.
        self.request.transforms.append(QueryDimensionTransform(id=name))
        return self

    def __call__(self, *args):
        self.request.transforms[-1].args = args
        return self

    def name(self, name: str):
        self.request.alias = name
        return self

    def __str__(self):
        transforms = []
        for transform in self.request.transforms:
            args = ", ".join(utils.repr_expr_constant(a) for a in transform.args)
            if len(args) > 0:
                args = f"({args})"
            transforms.append(f"{transform.id}{args}")
        transforms = ".".join(transforms)
        alias = ""
        if self.request.alias is not None:
            alias = f' as "{self.request.alias}"'
        return f"{self.request.dimension}.{transforms}{alias}"

    def encoding_fields(self, cls) -> dict:
        type_ = self.dimension.type
        for req_transform in self.request.transforms:
            transform = self.transforms.get(req_transform.id)
            if transform is None:
                raise KeyError(f"Transform {req_transform.id} does not exist")
            if transform.return_type is not None:
                # last transform with a defined return type
                type_ = transform.return_type
        obj = {
            "type": dimension_to_encoding_type[type_],
            "field": f"dimension:{self}",
        }
        title = {"title": self.dimension.name}
        info = cls_to_info_type(cls)
        if info == "axis":
            obj.update({"axis": title})
        elif info == "header":
            obj.update({"header": title})
        elif info == "legend":
            obj.update({"legend": title})
        return obj


class ProjectDimension(ProjectDimensionRequest):
    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)  # for Jupyter checking for _repr_html_ etc.
        return getattr(ProjectDimensionRequest(self.dimension, self.transforms), name)

    def name(self, name: str):
        return ProjectDimensionRequest(self.dimension, self.transforms).name(name)

    def __str__(self):
        return self.dimension.id

    def _repr_html_(self):
        template = environment.get_template("calculation.html.j2")
        return template.render(calculation=self.dimension, prefix=":")


class ProjectDimensions:
    def __init__(self, project: "dictum.project.Project"):
        transforms = project.store.transforms
        for dimension in project.store.dimensions.values():
            setattr(
                self,
                dimension.id,
                ProjectDimension(dimension, transforms=transforms),
            )
