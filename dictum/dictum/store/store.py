import dataclasses
from collections import defaultdict
from typing import Dict, List

import dictum.query
from dictum.store import schema
from dictum.store.calculations import (
    Calculation,
    Dimension,
    DimensionsUnion,
    Measure,
    Metric,
)
from dictum.store.computation import (
    AggregateQuery,
    Column,
    ColumnCalculation,
    Computation,
)
from dictum.store.dicts import DimensionDict, MeasureDict, MetricDict
from dictum.store.table import RelatedTable, Table, TableFilter
from dictum.store.transforms import IsInFilter, Transform

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


class Store:
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

    def __init__(self, config: schema.Config):
        self.name = config.name
        self.description = config.description
        self.locale = config.locale

        self.tables: Dict[str, Table] = {}
        self.measures = MeasureDict()
        self.dimensions = DimensionDict()
        self.metrics = MetricDict()
        self.filters: Dict[str, Transform] = {}
        self.transforms: Dict[str, Transform] = {}

        # add filters and transforms
        for filter in config.filters.values():
            self.filters[filter.id] = Transform(
                **filter.dict(include={"id", "name", "description", "str_expr", "args"})
            )
        self.filters["isin"] = IsInFilter()
        for transform in config.transforms.values():
            self.transforms[transform.id] = Transform(
                **transform.dict(
                    include={
                        "id",
                        "name",
                        "str_expr",
                        "args",
                        "description",
                        "return_type",
                        "format",
                    }
                ),
            )

        # add unions
        for union in config.unions.values():
            self.dimensions[union.id] = DimensionsUnion(
                **union.dict(include=displayed_fields)
            )

        # add all tables and their relationships
        for config_table in config.tables.values():
            table = self.ensure_table(config_table)
            for related in config_table.related.values():
                if related.table not in config.tables:
                    raise KeyError(
                        f"Table {related.table} is referenced as a foreign key target "
                        f"for table {table.id}, but it's not defined in the config."
                    )
                related_table = config.tables[related.table]
                if related_table.primary_key is None:
                    raise ValueError(
                        f"Table {related.table} is a related table for {table.id}, but "
                        "it doesn't have a primary key."
                    )
                table.related[related.alias] = RelatedTable(
                    table=self.ensure_table(related_table),
                    related_key=related_table.primary_key,
                    **related.dict(include={"foreign_key", "alias"}),
                )

        # add all dimensions
        for config_table in config.tables.values():
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
                        _dimension, id=dimension.union
                    )
                self.dimensions.add(_dimension)

        # add all measures
        for config_table in config.tables.values():
            table = self.tables.get(config_table.id)
            for measure in config_table.measures.values():
                _measure = self.build_measure(measure, table)
                table.measures[measure.id] = _measure
                self.measures.add(_measure)

        # add measure backlinks
        for table in self.tables.values():
            for measure in table.measures.values():
                for path in table.allowed_join_paths.values():
                    target = path[-1].table
                    target.measure_backlinks[measure.id] = table

        # add virtual related tables (subqueries)
        for dimension in self.dimensions.values():
            if isinstance(dimension, Dimension):
                dimension.table.related.update(dimension.related)

        # add metrics
        for metric in config.metrics.values():
            self.metrics[metric.id] = Metric(
                store=self,
                **metric.dict(include=table_calc_fields),
            )

    @classmethod
    def from_yaml(cls, path: str):
        config = schema.Config.from_yaml(path)
        return cls(config)

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
            t.filters = [TableFilter(expr=f, table=t) for f in table.filters]
            self.tables[table.id] = t
        return self.tables[table.id]

    def get_metadata(self, query: "dictum.query.Query") -> Dict[str, Calculation]:
        """Returns a dict of metadata relevant to the query (mostly having to do with
        updated formats).
        """
        result = {}
        for request in query.dimensions:
            dimension = self.dimensions.get(request.dimension)
            _type = dimension.type
            _format = dimension.format
            if request.transform is not None:
                transform = self.transforms[request.transform.id]
                _type = (
                    dimension.type
                    if transform.return_type is None
                    else transform.return_type
                )
                _format = (
                    transform.format
                    if transform.format is not None
                    else dimension.format
                )
            result[request.dimension] = dataclasses.replace(
                dimension, type=_type, format=_format
            )
        for request in query.metrics:
            result[request.metric] = self.metrics.get(request.metric)
        return result

    def suggest_metrics(self, query: "dictum.query.Query") -> List[Measure]:
        """Suggest a list of possible metrics based on a query.
        Only metrics that can be used with all the dimensions from the query
        """
        result = []
        query_dims = set(r.dimension for r in query.dimensions)
        for metric in self.metrics.values():
            if metric.id in query.metrics:
                continue
            allowed_dims = set(d.id for d in metric.dimensions)
            if query_dims < allowed_dims:
                result.append(metric)
        return sorted(result, key=lambda x: (x.name))

    def suggest_dimensions(self, query: "dictum.query.Query") -> List[Dimension]:
        """Suggest a list of possible dimensions based on a query. Only dimensions
        shared by all measures that are already in the query.
        """
        dims = set(self.dimensions) - set(r.dimension for r in query.dimensions)
        for request in query.metrics:
            metric = self.metrics.get(request.metric)
            for measure in metric.measures:
                dims = dims & set(measure.table.allowed_dimensions)
        return sorted([self.dimensions[d] for d in dims], key=lambda x: x.name)

    def get_range_computation(self, dimension_id: str) -> Computation:
        """Get a computation that will compute a range of values for a given dimension.
        This is seriously out of line with what different parts of computation mean, so
        maybe we need to give them more abstract names.
        """
        dimension = self.dimensions.get(dimension_id)
        table = dimension.table
        min_, max_ = dimension.prepare_range_expr([table.id])
        return Computation(
            queries=[
                AggregateQuery(
                    join_tree=AggregateQuery(table=table, identity=table.id),
                    aggregate={"min": min_, "max": max_},
                )
            ]
        )

    def get_values_computation(self, dimension_id: str) -> Computation:
        """Get a computation that will compute a list of unique possible values for this
        dimension.
        """
        dimension = self.dimensions.get(dimension_id)
        table = dimension.table
        return Computation(
            queries=[
                AggregateQuery(
                    join_tree=AggregateQuery(table=table, identity=table.id),
                    groupby={"values": dimension.prepare_expr([table.id])},
                )
            ]
        )

    def get_aggregate_query(
        self,
        measures: List[str],
        dimensions: List["dictum.query.QueryDimensionRequest"] = [],
        filters: List["dictum.query.QueryDimensionFilter"] = [],
    ) -> AggregateQuery:
        measure_id, *measures = measures

        # get the first measure to figure out the anchor table
        measure = self.measures.get(measure_id)
        anchor = measure.table
        query = AggregateQuery(table=anchor)
        query.add_measure(measure_id)

        for measure_id in measures:
            query.add_measure(measure_id)

        for request in dimensions:
            if request.dimension not in self.dimensions:
                raise KeyError(f"Dimension '{request.dimension}' does not exist")
            dimension = self.dimensions.get(request.dimension)
            compiler, type_ = None, dimension.type
            if request.transform is not None:
                transform = self.transforms[request.transform.id]
                compiler = transform.get_compiler(request.transform.args)
                type_ = transform.return_type
            query.add_dimension(dimension.id, request.name, type_, compiler=compiler)

        for request in filters:
            filter = self.filters.get(request.filter.id)
            if filter is None:
                raise KeyError(f"Filter function {request.filter.id} doesn't exist")
            query.add_filter(
                request.dimension, filter.get_compiler(request.filter.args)
            )
        # add anchor's table-level filters
        for f in anchor.filters:
            query.add_literal_filter(f.expr)

        return query

    def get_computation(self, query: "dictum.query.Query") -> Computation:
        """Returns an object that can then be executed on a backend."""

        metrics = {m.metric: self.metrics.get(m.metric) for m in query.metrics}
        tables = defaultdict(lambda: [])

        # group measures by anchor
        for metric in metrics.values():
            for measure in metric.measures:
                tables[measure.table.id].append(measure.id)

        # get a query for each anchor
        queries = []
        for measures in tables.values():
            queries.append(
                self.get_aggregate_query(
                    measures=measures,
                    dimensions=query.dimensions,
                    filters=query.filters,
                )
            )

        # get dimensions for the top level
        dimensions = []
        for request in query.dimensions:
            dimension = self.dimensions.get(request.dimension)
            type_ = dimension.type
            if request.transform is not None:
                transform = self.transforms[request.transform.id]
                type_ = transform.return_type or type_
            column = Column(name=request.name, type=type_)
            dimensions.append(column)

        metrics = [
            ColumnCalculation(expr=m.expr, name=id, type=m.type)
            for id, m in metrics.items()
        ]
        return Computation(
            metrics=metrics,
            queries=queries,
            dimensions=dimensions,
        )
