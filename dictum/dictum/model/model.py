import dataclasses
from typing import Dict

from dictum import schema
from dictum.model.calculations import Dimension, DimensionsUnion, Measure, Metric
from dictum.model.dicts import DimensionDict, MeasureDict, MetricDict
from dictum.model.scalar import transforms as scalar_transforms
from dictum.model.table import RelatedTable, Table, TableFilter
from dictum.model.time import dimensions as time_dimensions

displayed_fields = {"id", "name", "description", "type", "format", "missing"}

table_calc_fields = displayed_fields | {"str_expr"}


class Model:
    def __init__(self, model: schema.Model):
        self.name = model.name
        self.description = model.description
        self.locale = model.locale

        self.tables: Dict[str, Table] = {}
        self.measures = MeasureDict()
        self.dimensions = DimensionDict()
        self.metrics = MetricDict()
        self.scalar_transforms = scalar_transforms

        self.theme = model.theme

        # add unions
        for union in model.unions.values():
            self.dimensions[union.id] = DimensionsUnion(
                **union.dict(include=displayed_fields)
            )

        # add all tables, their relationships and calculations
        for config_table in model.tables.values():
            table = self.create_table(config_table)
            self.tables[table.id] = table

            # add table dimensions
            for dimension in config_table.dimensions.values():
                self.add_dimension(dimension, table)

            # add table measures
            for measure in config_table.measures.values():
                self.add_measure(measure, table)

        # add detached dimensions
        for dimension in model.dimensions.values():
            table = self.tables[dimension.table]
            self.add_dimension(dimension, table)

        # add metrics
        for metric in model.metrics.values():
            self.add_metric(metric)

        # add measure backlinks
        for table in self.tables.values():
            for measure in table.measures.values():
                for target in table.allowed_join_paths:
                    target.measure_backlinks[measure.id] = table

        # add default time dimensions
        self.dimensions.update(time_dimensions)

    def create_table(self, table: schema.Table):
        result = Table(
            **table.dict(include={"id", "source", "description", "primary_key"})
        )
        for related in table.related.values():
            result.related[related.alias] = RelatedTable(
                parent=result,
                tables=self.tables,
                **related.dict(
                    include={"str_table", "str_related_key", "foreign_key", "alias"}
                ),
            )
        result.filters = [TableFilter(str_expr=f, table=result) for f in table.filters]
        return result

    def add_measure(self, measure: schema.Measure, table: Table) -> Measure:
        result = Measure(
            table=table,
            **measure.dict(include=table_calc_fields | {"str_filter", "str_time"}),
        )
        if measure.metric:
            self.metrics.add(Metric.from_measure(measure, self))
        table.measures.add(result)
        self.measures.add(result)

    def add_dimension(self, dimension: schema.Dimension, table: Table) -> Dimension:
        result = Dimension(
            table=table,
            **dimension.dict(include=table_calc_fields),
        )
        table.dimensions[result.id] = result
        if dimension.union is not None:
            if dimension.union in table.dimensions:
                raise KeyError(
                    f"Duplicate union dimension {dimension.union} "
                    f"on table {table.id}"
                )
            table.dimensions[dimension.union] = dataclasses.replace(
                result, id=dimension.union, is_union=True
            )
        self.dimensions.add(result)

    def add_metric(self, metric: schema.Metric):
        if metric.table is not None:
            # table is specified, treat as that table's measure
            table = self.tables.get(metric.table)
            measure = schema.Measure(**metric.dict(by_alias=True), metric=True)
            return self.add_measure(measure, table)

        # no, it's a real metric
        self.metrics[metric.id] = Metric(
            model=self,
            **metric.dict(include=table_calc_fields),
        )

    # def suggest_metrics(self, query: schema.Query) -> List[Measure]:
    #     """Suggest a list of possible metrics based on a query.
    #     Only metrics that can be used with all the dimensions from the query
    #     """
    #     result = []
    #     query_dims = set(r.dimension.id for r in query.dimensions)
    #     for metric in self.metrics.values():
    #         if metric.id in query.metrics:
    #             continue
    #         allowed_dims = set(d.id for d in metric.dimensions)
    #         if query_dims < allowed_dims:
    #             result.append(metric)
    #     return sorted(result, key=lambda x: (x.name))

    # def suggest_dimensions(self, query: schema.Query) -> List[Dimension]:
    #     """Suggest a list of possible dimensions based on a query. Only dimensions
    #     shared by all measures that are already in the query.
    #     """
    #     dims = set(self.dimensions) - set(r.dimension.id for r in query.dimensions)
    #     for request in query.metrics:
    #         metric = self.metrics.get(request.metric.id)
    #         for measure in metric.measures:
    #             dims = dims & set(measure.table.allowed_dimensions)
    #     return sorted([self.dimensions[d] for d in dims], key=lambda x: x.name)

    # def get_range_computation(self, dimension_id: str) -> Computation:
    #     """Get a computation that will compute a range of values for a given
    #       dimension.
    #     This is seriously out of line with what different parts of computation mean,
    #     so maybe we need to give them more abstract names.
    #     """
    #     dimension = self.dimensions.get(dimension_id)
    #     table = dimension.table
    #     min_, max_ = dimension.prepare_range_expr([table.id])
    #     return Computation(
    #         queries=[
    #             AggregateQuery(
    #                 join_tree=AggregateQuery(table=table, identity=table.id),
    #                 aggregate={"min": min_, "max": max_},
    #             )
    #         ]
    #     )

    # def get_values_computation(self, dimension_id: str) -> Computation:
    #     """Get a computation that will compute a list of unique possible values for
    #     this dimension.
    #     """
    #     dimension = self.dimensions.get(dimension_id)
    #     table = dimension.table
    #     return Computation(
    #         queries=[
    #             AggregateQuery(
    #                 join_tree=AggregateQuery(table=table, identity=table.id),
    #                 groupby={"values": dimension.prepare_expr([table.id])},
    #             )
    #         ]
    #     )

    def get_currencies_for_query(self, query: schema.Query):
        currencies = set()
        for request in query.metrics:
            metric = self.metrics.get(request.metric.id)
            if metric.format is not None and metric.format.currency is not None:
                currencies.add(metric.format.currency)
        for request in query.dimensions:
            dimension = self.dimensions.get(request.dimension.id)
            if dimension.format is not None and dimension.format.currency is not None:
                currencies.add(dimension.format.currency)
        return currencies
