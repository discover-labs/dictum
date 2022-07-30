import datetime
from typing import List

import pandas as pd
from altair.utils.data import to_values

import dictum.project
import dictum.project.calculations
from dictum import engine, schema
from dictum.schema import Query


class DictumData:
    def __init__(
        self,
        project: "dictum.project.Project",
        metrics: List["dictum.project.calculations.ProjectMetric"],
    ):
        self.project = project
        self.requests = [m.request for m in metrics]
        self.filters = []
        self.limits = []

    def extend_query(self, query: Query):
        query = query.copy()
        for req in self.requests:
            if req not in query.metrics:
                query.metrics.append(req)
        query.filters.extend(self.filters)
        query.limit.extend(self.limits)
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

    def execute(self, query: schema.Query) -> engine.Result:
        query = self.extend_query(query)
        return self.project.execute(query)

    def to_dict(self):
        return {"name": "__dictum__"}
