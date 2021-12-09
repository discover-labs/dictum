import pandas as pd

import dictum.project
import dictum.data_model
from dictum.project.templates import environment


class ProjectMetric:
    def __init__(self, metric: "dictum.data_model.Metric"):
        self.metric = metric

    def __str__(self):
        return self.metric.id

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
