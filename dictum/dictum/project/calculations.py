from typing import Dict

import pandas as pd
from babel.dates import match_skeleton

import dictum.data_model
import dictum.project
from dictum import utils
from dictum.data_model import Transform
from dictum.project.altair.encoding import AltairEncodingChannelHook, filter_fields
from dictum.project.altair.format import (
    ldml_date_to_d3_time_format,
    ldml_number_to_d3_format,
)
from dictum.project.altair.locale import get_default_format_for_kind, load_locale
from dictum.project.templates import environment
from dictum.schema.query import (
    QueryDimensionRequest,
    QueryDimensionTransform,
    QueryMetricRequest,
)

type_to_encoding_type = {
    "bool": "ordinal",
    "date": "temporal",
    "datetime": "temporal",
    "int": "quantitative",
    "float": "quantitative",
    "str": "nominal",
}


def format_config_to_d3_format(config, locale):
    if config.kind == "string":
        return None

    convert = ldml_number_to_d3_format
    if config.kind in {"date", "datetime"}:
        convert = ldml_date_to_d3_time_format

    pattern = config.pattern
    if config.skeleton is not None:
        _locale = load_locale(locale)
        format = _locale.datetime_skeletons.get(config.skeleton)
        if format is None:
            skel_key = match_skeleton(config.skeleton, _locale.datetime_skeletons)
            if skel_key is not None:
                format = _locale.datetime_skeletons[skel_key]
        if format is not None:
            pattern = format.pattern

    if pattern is None:
        return get_default_format_for_kind(config.kind, locale)

    return convert(pattern)


class ProjectCalculation(AltairEncodingChannelHook):
    def __init__(self, calculation, locale: str):
        self.calculation = calculation
        self.locale = locale

    def encoding_fields(self, cls=None) -> dict:
        title = {"title": self.calculation.name}

        fmt = format_config_to_d3_format(self.calculation.format, self.locale)
        if fmt is not None:
            title["format"] = fmt

        obj = {
            "field": f"{self._type}:{self}",
            "type": type_to_encoding_type[self.calculation.type],
            "axis": title,
            "legend": title,
            "header": title,
        }

        return filter_fields(cls, obj)

    @property
    def _type(self) -> str:
        if isinstance(self.calculation, dictum.data_model.Metric):
            return "metric"
        return "dimension"

    def _repr_html_(self):
        template = environment.get_template("calculation.html.j2")
        calculation = self.calculation
        if (
            isinstance(calculation, dictum.data_model.Metric)
            and len(calculation.measures) == 1
        ):
            calculation = calculation.measures[0]
        prefix = "$" if self._type == "metric" else ":"
        return template.render(calculation=calculation, prefix=prefix)

    def name(self, name: str):
        self.request.alias = name
        return self

    def __str__(self):
        return self.calculation.id


class ProjectMetric(ProjectCalculation):
    def __init__(self, calculation, locale: str):
        super().__init__(calculation, locale)
        self.request = QueryMetricRequest(metric=calculation.id)


class ProjectMetrics:
    def __init__(self, project: "dictum.project.Project"):
        self.__project = project
        for metric in project.data_model.metrics.values():
            setattr(self, metric.id, ProjectMetric(metric, project.data_model.locale))

    def _repr_html_(self):
        return pd.DataFrame(
            {"id": m.id, "name": m.name}
            for m in self.__project.data_model.metrics.values()
        ).to_html()


class ProjectDimensionRequest(ProjectCalculation):
    def __init__(self, calculation, locale: str, transforms: Dict[str, Transform]):
        self.request = QueryDimensionRequest(dimension=calculation.id)
        self.transforms = transforms
        super().__init__(calculation, locale)

    def __eq__(self, other):
        return self.eq(other)

    def __ne__(self, other):
        return self.ne(other)

    def __gt__(self, other):
        return self.gt(other)

    def __ge__(self, other):
        return self.ge(other)

    def __lt__(self, other):
        return self.lt(other)

    def __le__(self, other):
        return self.le(other)

    def __invert__(self):
        return self.invert()

    def __getattr__(self, name: str):
        if name.startswith("_repr_"):
            raise AttributeError(name)  # for Jupyter checking for _repr_html_ etc.
        self.request.transforms.append(QueryDimensionTransform(id=name))
        return self

    def __call__(self, *args):
        self.request.transforms[-1].args = list(args)
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

    def encoding_fields(self, cls=None) -> dict:
        fields = super().encoding_fields(cls=cls)
        format = self.calculation.format
        type_ = self.calculation.type
        for request_transform in self.request.transforms:
            transform = self.transforms[request_transform.id](*request_transform.args)
            format = transform.get_format(type_)
            type_ = transform.get_return_type(type_)
        if (fmt := format_config_to_d3_format(format, self.locale)) is not None:
            for key in ["axis", "legend", "header"]:
                if key in fields:
                    fields[key]["format"] = fmt
        if "type" in fields:
            fields["type"] = type_to_encoding_type[type_]
        return fields


class ProjectDimension(ProjectDimensionRequest):
    def __getattr__(self, name: str):
        if name.startswith("_repr_"):
            raise AttributeError(name)  # for Jupyter checking for _repr_html_ etc.
        return getattr(
            ProjectDimensionRequest(
                self.calculation, locale=self.locale, transforms=self.transforms
            ),
            name,
        )

    def name(self, name: str):
        return ProjectDimensionRequest(self.calculation, self.transforms).name(name)

    def __str__(self):
        return self.calculation.id


class ProjectDimensions:
    def __init__(self, project: "dictum.project.Project"):
        transforms = project.data_model.transforms
        for dimension in project.data_model.dimensions.values():
            setattr(
                self,
                dimension.id,
                ProjectDimension(
                    dimension, locale=project.data_model.locale, transforms=transforms
                ),
            )
