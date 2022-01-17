import dataclasses
from typing import Dict, List

from dictum import schema
from dictum.model.calculations import Dimension, DimensionsUnion, Measure, Metric
from dictum.model.dicts import DimensionDict, MeasureDict, MetricDict
from dictum.model.table import RelatedTable, Table, TableFilter
from dictum.transforms.scalar import ScalarTransform
from dictum.transforms.scalar import transforms as scalar_transforms
from dictum.transforms.table import TableTransform
from dictum.transforms.table import transforms as table_transforms

# from toolz import compose_left


displayed_fields = {
    "id",
    "name",
    "description",
    "type",
    "format",
    "currency",
    "missing",
}

table_calc_fields = displayed_fields | {"str_expr"}


@dataclasses.dataclass
class ResolvedQueryDimensionRequest:
    dimension: Dimension
    transforms: List[ScalarTransform]
    name: str
    keep_name: bool = False


@dataclasses.dataclass
class ResolvedQueryMetricRequest:
    metric: Metric
    transforms: List[TableTransform]
    name: str
    keep_name: bool = False


@dataclasses.dataclass
class ResolvedQuery:
    """Same as Query, but everything is replaced with the actual model objects."""

    metrics: List[ResolvedQueryMetricRequest] = dataclasses.field(default_factory=list)
    dimensions: List[ResolvedQueryDimensionRequest] = dataclasses.field(
        default_factory=list
    )
    filters: List[ResolvedQueryDimensionRequest] = dataclasses.field(
        default_factory=list
    )
    limit: List[ResolvedQueryMetricRequest] = dataclasses.field(default_factory=list)


class Model:
    """The actual metrics store. Receives a query object, figures out which computations
    on the source tables are required to be performed in order to fulfil the query.

    The main purpose of this object is to take in the config and prepare all the data
    structures for the incoming queries.
    - It parses the expressions.
    - Resolves references to anchor tables (tables on which a calculation was declared)
      by adding the actual table id. E.g. sum(amount) -> sum(anchor_table.amount)
    - Resolves references to other calculations by replacing the reference with the
      referenced calculation's parse tree.
    - If the referenced calculation uses any columns of it's related tables, prepends
      references to these columns with the anchor table of the referenced calculation,
      e.g. if the calculation on table `orders` is `users.channel`, and
      `channel` dimension on `users` is `attributions.channel`, the resolved reference
      on orders will be `users.attributions.channel`.

    `execute_query` method returns an object that can then be executed on a backend.

    Query processing consists of figuring out which joins need to be performed,
    deduplicating the joins, arranging them in a tree and returning a Calculation object.
    """

    def __init__(self, model: schema.Model):
        self.name = model.name
        self.description = model.description
        self.locale = model.locale

        self.tables: Dict[str, Table] = {}
        self.measures = MeasureDict()
        self.dimensions = DimensionDict()
        self.metrics = MetricDict()
        self.scalar_transforms = scalar_transforms
        self.table_transforms = table_transforms

        self.theme = model.theme

        # add unions
        for union in model.unions.values():
            self.dimensions[union.id] = DimensionsUnion(
                **union.dict(include=displayed_fields)
            )

        # add all tables and their relationships
        for config_table in model.tables.values():
            table = self.ensure_table(config_table)
            for related in config_table.related.values():
                if related.table not in model.tables:
                    raise KeyError(
                        f"Table {related.table} is referenced as a foreign key target "
                        f"for table {table.id}, but it's not defined in the config."
                    )
                related_table = model.tables[related.table]
                if related_table.primary_key is None and related.related_key is None:
                    raise ValueError(
                        f"Table {related.table} is a related table for {table.id}, but "
                        "it doesn't have a primary key. You have to set related_key for "
                        "the relation or primary_key on the related table itself."
                    )
                related_key = (
                    related_table.primary_key
                    if related.related_key is None
                    else related.related_key
                )
                table.related[related.alias] = RelatedTable.create(
                    parent=table,
                    table=self.ensure_table(related_table),
                    related_key=related_key,
                    **related.dict(include={"foreign_key", "alias"}),
                )

        # add all dimensions
        for config_table in model.tables.values():
            table = self.tables.get(config_table.id)
            for dimension in config_table.dimensions.values():
                _dimension = Dimension(
                    table=table,
                    **dimension.dict(include=table_calc_fields),
                )
                table.dimensions[dimension.id] = _dimension
                if dimension.union is not None:
                    if dimension.union in table.dimensions:
                        raise KeyError(
                            f"Duplicate union dimension {dimension.union} "
                            f"on table {table.id}"
                        )
                    table.dimensions[dimension.union] = dataclasses.replace(
                        _dimension, id=dimension.union, is_union=True
                    )
                self.dimensions.add(_dimension)

        # add all measures
        for config_table in model.tables.values():
            table = self.tables.get(config_table.id)
            for measure in config_table.measures.values():
                _measure = self.build_measure(measure, table)
                table.measures[measure.id] = _measure
                self.measures.add(_measure)

        # add measure backlinks
        for table in self.tables.values():
            for measure in table.measures.values():
                for target in table.allowed_join_paths:
                    target.measure_backlinks[measure.id] = table

        # add metrics
        for metric in model.metrics.values():
            self.metrics[metric.id] = Metric(
                store=self,
                **metric.dict(include=table_calc_fields),
            )

    @classmethod
    def from_yaml(cls, path: str):
        return cls(schema.Model.from_yaml(path))

    def build_measure(self, measure: schema.Measure, table: Table) -> Measure:
        _measure = Measure(
            table=table,
            **measure.dict(
                include={
                    "id",
                    "name",
                    "description",
                    "str_expr",
                    "type",
                    "format",
                    "currency",
                    "missing",
                }
            ),
        )
        if measure.metric:
            self.metrics.add(Metric.from_measure(measure, self))
        return _measure

    def ensure_table(self, table: schema.Table) -> Table:
        if table.id not in self.tables:
            t = Table(
                **table.dict(include={"id", "source", "description", "primary_key"}),
            )
            t.filters = [TableFilter(str_expr=f, table=t) for f in table.filters]
            self.tables[table.id] = t
        return self.tables[table.id]

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
    #     """Get a computation that will compute a range of values for a given dimension.
    #     This is seriously out of line with what different parts of computation mean, so
    #     maybe we need to give them more abstract names.
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
    #     """Get a computation that will compute a list of unique possible values for this
    #     dimension.
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

    def get_resolved_dimension(
        self, query_dimension: schema.QueryDimension
    ) -> ResolvedQueryDimensionRequest:
        dimension = self.dimensions.get(query_dimension.id)
        transforms = []
        for transform in query_dimension.transforms:
            tr = self.scalar_transforms.get(transform.id)(*transform.args)
            transforms.append(tr)
        return ResolvedQueryDimensionRequest(
            dimension=dimension, transforms=transforms, name=query_dimension.name
        )

    def get_resolved_dimension_request(
        self, request: schema.QueryDimensionRequest
    ) -> ResolvedQueryDimensionRequest:
        resolved = self.get_resolved_dimension(request.dimension)
        return ResolvedQueryDimensionRequest(
            dimension=resolved.dimension,
            transforms=resolved.transforms,
            name=request.name,
            keep_name=request.alias is not None,
        )

    def get_resolved_metric(
        self,
        query_metric: schema.QueryMetric,
        dimensions: List[ResolvedQueryDimensionRequest],
    ) -> ResolvedQueryMetricRequest:
        metric = self.metrics.get(query_metric.id)

        transforms = []
        for transform in query_metric.transforms:
            of = [self.get_resolved_dimension(d) for d in transform.of]
            within = [self.get_resolved_dimension(d) for d in transform.within]

            # for top and bottom, of is everything that's not within (if not specified otherwise)
            if len(of) == 0 and transform.id in {"top", "bottom"}:
                within_names = set(d.name for d in within)
                of = [d for d in dimensions if d.name not in (within_names)]

            resolved = ResolvedQuery(
                metrics=[
                    ResolvedQueryMetricRequest(
                        metric=metric, transforms=[], name=query_metric.name
                    )
                ],
                dimensions=[*of, *within],
            )
            tr = self.table_transforms.get(transform.id)(
                *transform.args,
                metric_id=metric.id,
                query=resolved,
                of=of,
                within=within,
            )
            transforms.append(tr)

        return ResolvedQueryMetricRequest(
            metric=metric, transforms=transforms, name=query_metric.name
        )

    def get_resolved_metric_request(
        self,
        request: schema.QueryMetricRequest,
        dimensions: List[ResolvedQueryDimensionRequest],
    ) -> ResolvedQueryMetricRequest:
        resolved = self.get_resolved_metric(request.metric, dimensions)
        return ResolvedQueryMetricRequest(
            metric=resolved.metric,
            transforms=resolved.transforms,
            name=request.name,
            keep_name=request.alias is not None,
        )

    def get_resolved_query(self, query: schema.Query) -> ResolvedQuery:
        result = ResolvedQuery()
        for request in query.dimensions:
            result.dimensions.append(self.get_resolved_dimension_request(request))
        for request in query.metrics:
            resolved = self.get_resolved_metric_request(request, result.dimensions)
            for transform in resolved.transforms:
                if transform.id in {"top", "bottom"}:
                    raise ValueError(
                        "Top and Bottom transforms are only allowed inside limit clause"
                    )
            result.metrics.append(resolved)
        for filter in query.filters:
            result.filters.append(self.get_resolved_dimension(filter))
        for limit in query.limit:
            result.limit.append(self.get_resolved_metric(limit, result.dimensions))
        return result

    def get_names(self, ids: List[str]) -> Dict[str, str]:
        result = {}
        for item in ids:
            if item in self.metrics:
                result[item] = self.metrics[item].name
            if item in self.dimensions:
                result[item] = self.dimensions[item].name
        return result

    def get_formats(self, ids: List[str]) -> Dict[str, schema.FormatConfig]:
        result = {}
        for item in ids:
            if item in self.metrics:
                result[item] = self.metrics[item].format
            if item in self.dimensions:
                result[item] = self.dimensions[item].format
        return result
