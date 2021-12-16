from typing import List

import pandas as pd
from altair.utils.data import to_values

import dictum.project
import dictum.project.metrics
from dictum.schema.query import QueryMetricRequest


class DictumData:
    def __init__(
        self,
        project: "dictum.project.Project",
        metrics: List["dictum.project.metrics.ProjectMetric"],
    ):
        self.project = project
        self.requests = [QueryMetricRequest(metric=m.metric.id) for m in metrics]
        self.filters = []

    def extend_query(self, query):
        query = query.copy()
        for req in self.requests:
            if req not in query.metrics:
                query.metrics.append(req)
        query.filters.extend(self.filters)
        return query

    def get_values(self, query):
        query = self.extend_query(query)
        res = self.project.execute(query)
        return to_values(pd.DataFrame(res.data))

    def to_dict(self):
        return {"name": "__dictum__"}
