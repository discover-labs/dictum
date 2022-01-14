from typing import Dict

import pandas as pd
from babel.dates import match_skeleton

import dictum.model
import dictum.project
from dictum.project.altair.encoding import AltairEncodingChannelHook, filter_fields
from dictum.project.altair.format import (
    ldml_date_to_d3_time_format,
    ldml_number_to_d3_format,
)
from dictum.project.altair.locale import get_default_format_for_kind, load_locale
from dictum.project.templates import environment
from dictum.schema.query import (
    QueryDimension,
    QueryDimensionRequest,
    QueryMetric,
    QueryMetricRequest,
    QueryScalarTransform,
    QueryTableTransform,
)
from dictum.transforms.scalar import ScalarTransform
from dictum.transforms.table import TableTransform

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
    kind: str

    def __init__(self, calculation, locale: str):
        self.calculation = calculation
        self.locale = locale

    def encoding_fields(self, cls=None) -> dict:
        title = {"title": self.calculation.name}

        # get type and format
        format = self.calculation.format
        type_ = self.calculation.type
        for request_transform in getattr(self.request, self.kind).transforms:
            transform = self.transforms[request_transform.id](*request_transform.args)
            format = transform.get_format(type_)
            type_ = transform.get_return_type(type_)

        if (fmt := format_config_to_d3_format(format, self.locale)) is not None:
            title["format"] = fmt

        fields = {
            "field": f"{self._type}:{self}",
            "type": type_to_encoding_type[self.calculation.type],
            "axis": title,
            "legend": title,
            "header": title,
        }

        fields["type"] = type_to_encoding_type[type_]
        return filter_fields(cls, fields)

    @property
    def _type(self) -> str:
        if isinstance(self.calculation, dictum.model.Metric):
            return "metric"
        return "dimension"

    def _repr_html_(self):
        template = environment.get_template("calculation.html.j2")
        calculation = self.calculation
        if (
            isinstance(calculation, dictum.model.Metric)
            and len(calculation.measures) == 1
        ):
            calculation = calculation.measures[0]
        prefix = "$" if self._type == "metric" else ":"
        return template.render(calculation=calculation, prefix=prefix)

    def name(self, name: str):
        self.request.alias = name
        return self

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

    def __str__(self):
        return self.request.render()


class ProjectMetricRequest(ProjectCalculation):
    kind = "metric"

    def __init__(self, calculation, locale: str, transforms: Dict[str, TableTransform]):
        self.request = QueryMetricRequest(metric=QueryMetric(id=calculation.id))
        self.transforms = transforms
        super().__init__(calculation, locale)

    def __getattr__(self, name: str):
        if name not in self.transforms:
            raise AttributeError(name)
        self.request.metric.transforms.append(QueryTableTransform(id=name))
        return self

    def __call__(self, *args, of=None, within=None):
        of = [] if of is None else of
        within = [] if within is None else within
        self.request.metric.transforms[-1].args = list(args)
        self.request.metric.transforms[-1].of = [i.request for i in of]
        self.request.metric.transforms[-1].within = [i.request for i in within]
        return self


class ProjectMetric(ProjectMetricRequest):
    def name(self, name: str):
        return ProjectMetricRequest(
            calculation=self.calculation, locale=self.locale, transforms=self.transforms
        ).name(name)

    def __getattr__(self, name: str):
        if name not in self.transforms:
            raise AttributeError(name)
        return getattr(
            ProjectMetricRequest(
                calculation=self.calculation,
                locale=self.locale,
                transforms=self.transforms,
            ),
            name,
        )


class ProjectMetrics:
    def __init__(self, project: "dictum.project.Project"):
        self.__project = project
        transforms = project.model.table_transforms
        for metric in project.model.metrics.values():
            setattr(
                self,
                metric.id,
                ProjectMetric(metric, project.model.locale, transforms),
            )

    def _repr_html_(self):
        return pd.DataFrame(
            {"id": m.id, "name": m.name} for m in self.__project.model.metrics.values()
        ).to_html()


class ProjectDimensionRequest(ProjectCalculation):
    kind = "dimension"

    def __init__(
        self, calculation, locale: str, transforms: Dict[str, ScalarTransform]
    ):
        self.request = QueryDimensionRequest(
            dimension=QueryDimension(id=calculation.id)
        )
        self.transforms = transforms
        super().__init__(calculation, locale)

    def __getattr__(self, name: str):
        if name not in self.transforms:
            raise AttributeError(name)  # for Jupyter checking for _repr_html_ etc.
        self.request.dimension.transforms.append(QueryScalarTransform(id=name))
        return self

    def __call__(self, *args):
        self.request.dimension.transforms[-1].args = list(args)
        return self


class ProjectDimension(ProjectDimensionRequest):
    def __getattr__(self, name: str):
        if name not in self.transforms:
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
        transforms = project.model.scalar_transforms
        for dimension in project.model.dimensions.values():
            setattr(
                self,
                dimension.id,
                ProjectDimension(
                    dimension, locale=project.model.locale, transforms=transforms
                ),
            )
