import pandas as pd

import dictum.data_model
import dictum.project
from dictum.project.altair.encoding import AltairEncodingChannelHook, ChannelInfoType
from dictum.project.templates import environment
from dictum.schema.query import QueryMetricRequest


class ProjectMetric(AltairEncodingChannelHook):
    def __init__(self, metric: "dictum.data_model.Metric"):
        self.metric = metric
        self.request = QueryMetricRequest(metric=metric.id)

    def __str__(self):
        return self.request.name

    def encoding_fields(self, info: ChannelInfoType) -> dict:
        """https://gist.github.com/saaj/0d6bb9b70964a1313cf5"""
        obj = {
            "field": f"metric:{self.metric.id}",
            "type": "quantitative",
            # "axis": {
            #     "format": (
            #         "$.0f"
            #         if self.metric.format and self.metric.format.kind == "currency"
            #         else ".0f"
            #     ),
            #     "title": self.metric.name,
            # },
        }
        title = {"title": self.metric.name}
        if info == "axis":
            obj.update({"axis": title})
        elif info == "header":
            obj.update({"header": title})
        elif info == "legend":
            obj.update({"legend": title})
        return obj

    def _repr_html_(self):
        template = environment.get_template("calculation.html.j2")
        calculation = (
            self.metric if len(self.metric.measures) > 1 else self.metric.measures[0]
        )
        return template.render(calculation=calculation, prefix="$")


class ProjectMetrics:
    def __init__(self, project: "dictum.project.Project"):
        self.__project = project
        for metric in project.store.metrics.values():
            setattr(self, metric.id, ProjectMetric(metric))

    def _repr_html_(self):
        return pd.DataFrame(
            {"id": m.id, "name": m.name} for m in self.__project.store.metrics.values()
        ).to_html()
