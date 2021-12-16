from altair import Chart

import dictum.project
from dictum.project.altair.data import DictumData
from dictum.ql.transformer import compile_filter


class ProjectChart:
    def __init__(self, project: "dictum.project.Project"):
        self.project = project
        self.data = DictumData(project, [])

    def __call__(self, *metrics):
        self.data = DictumData(self.project, metrics)
        return self

    @property
    def chart(self) -> Chart:
        return Chart(self.data)

    def where(self, *filters) -> Chart:
        self.data.filters.extend(compile_filter(str(f)) for f in filters)
        return self.chart

    def __getattr__(self, name: str):
        if name.startswith("_repr_"):
            raise AttributeError
        return getattr(self.chart, name)
