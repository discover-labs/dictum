import datetime
from typing import List

import pandas as pd
from altair.utils.data import to_values

import dictum.project
import dictum.project.calculations
from dictum.schema.query import QueryMetricRequest


class DictumData:
    def __init__(
        self,
        project: "dictum.project.Project",
        metrics: List["dictum.project.calculations.ProjectMetric"],
    ):
        self.project = project
        self.requests = [QueryMetricRequest(metric=m.calculation.id) for m in metrics]
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
        df = pd.DataFrame(res.data)

        # dates are not auto-converted to Pandas datetime and so are not sanitized
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, datetime.date)).any():
                df[col] = pd.to_datetime(df[col])
        return to_values(df)

    def to_dict(self):
        return {"name": "__dictum__"}
