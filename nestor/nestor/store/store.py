import dataclasses
from collections import UserDict, defaultdict
from functools import cached_property
from typing import Dict, List

from lark import Tree

from nestor.store import schema
from nestor.store.calculations import (
    Calculation,
    Dimension,
    DimensionQueryDefaults,
    Measure,
    Metric,
)
from nestor.store.computation import AggregateQuery, Computation
from nestor.store.expr.parser import parse_expr
from nestor.store.table import (
    CalculationResolver,
    CircularReferenceError,
    InvalidReferenceTypeError,
    ReferenceNotFoundError,
    ReferenceResolutionError,
    RelatedTable,
    Table,
)
from nestor.store.transforms import InFilter, Transform


class CalculationDict(UserDict):
    def __getitem__(self, key: str):
        result = self.data.get(key)
        if result is None:
            raise KeyError(f"{self.T.__name__} {key} does not exist")
        return result

    def __setitem__(self, name: str, value):
        if name in self.data:
            raise KeyError(
                f"Duplicate {self.T.__name__.lower()}: {name} on tables "
                f"{self.get(name).table.id} and {value.table.id}"
            )
        return super().__setitem__(name, value)

    def get(self, key: str):
        return self[key]

    def add(self, calc: "Calculation"):
        self[calc.id] = calc


class MeasureDict(CalculationDict):
    T = Measure

    def get(self, key: str) -> Measure:
        return super().get(key)


class DimensionDict(CalculationDict):
    T = Dimension

    def get(self, key: str) -> Dimension:
        return super().get(key)


class MetricDict(CalculationDict):
    T = Metric

    def get(self, key: str) -> Metric:
        return super().get(key)


class MetricResolver(CalculationResolver):
    def __init__(
        self,
        dependencies: Dict[str, Tree],
        allowed_measures: set,
        visit_tokens: bool = True,
    ):
        self._measures = allowed_measures
        super().__init__(dependencies, visit_tokens=visit_tokens)

    def _check_circular_refs(self, expr: Tree, path=()):
        for ref in expr.find_data("measure"):
            key = ref.children[0]
            if key in self._measures:
                continue
            if key in path:
                path_str = " -> ".join(path + (key,))
                raise CircularReferenceError(
                    f"circular reference in calculation: {path_str}"
                )
            dep = self._deps.get(key)
            if dep is None and key not in (self._measures):
                raise ReferenceNotFoundError(
                    f"Measure {key} does not exist. "
                    f"Valid values: {', '.join(self._measures)}"
                )
            elif dep is None:
                return
            self._check_circular_refs(dep, path=path + (key,))

    def measure(self, children: list):
        (ref,) = children
        if ref in self._measures:
            return Tree("measure", children)
        dep = self._deps.get(ref)
        return self.resolve(dep)

    def dimension(self, children: list):
        (ref,) = children
        raise InvalidReferenceTypeError(
            f"Can't reference dimension {ref} from a metric"
        )


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
        self.unions = {}

        # add filters and transforms
        for filter in config.filters.values():
            self.filters[filter.id] = Transform(
                expr=parse_expr(filter.expr),
                **filter.dict(include={"id", "name", "description"}),
            )
        self.filters["in"] = InFilter()
        for transform in config.transforms.values():
            self.transforms[transform.id] = Transform(
                expr=parse_expr(transform.expr),
                **transform.dict(
                    include={
                        "id",
                        "name",
                        "args",
                        "description",
                        "return_type",
                        "format",
                    }
                ),
            )

        # add unions
        for union in config.unions.values():
            self.unions[union.id] = union

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
                    expr=parse_expr(dimension.expr, missing=dimension.missing),
                    str_expr=dimension.expr,
                    table=table,
                    query_defaults=DimensionQueryDefaults(
                        filter=schema.QueryDimensionTransform.parse(
                            dimension.query_defaults.filter
                        ),
                        transform=schema.QueryDimensionTransform.parse(
                            dimension.query_defaults.transform
                        ),
                    ),
                    **dimension.dict(
                        include={
                            "id",
                            "name",
                            "description",
                            "type",
                            "format",
                            "currency",
                            "missing",
                        }
                    ),
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
            dimension.table.related.update(dimension.related)

        # resolve calculations
        for table in self.tables.values():
            table.resolve_calculations()

        # add and resolve metrics
        for metric in config.metrics.values():
            self.metrics[metric.id] = Metric(
                expr=parse_expr(metric.expr, metric.missing),
                str_expr=metric.expr,
                **metric.dict(
                    include={
                        "id",
                        "name",
                        "description",
                        "type",
                        "format",
                        "currency",
                        "missing",
                    }
                ),
            )
        metric_resolver = MetricResolver(
            dependencies={k: v.expr for k, v in self.metrics.items()},
            allowed_measures=set(self.measures),
        )
        for metric in self.metrics.values():
            try:
                metric.expr = metric_resolver.resolve(metric.expr)
                metric.measures = [
                    self.measures.get(m.children[0])
                    for m in metric.expr.find_data("measure")
                ]
            except ReferenceResolutionError as e:
                raise e.__class__(f"Error resolving {metric}: {e}")

    def build_measure(self, measure: schema.Measure, table: Table) -> Measure:
        _measure = Measure(
            expr=parse_expr(measure.expr),
            str_expr=measure.expr,
            format=measure.format,
            table=table,
            **measure.dict(include={"id", "name", "description", "type", "currency", "missing"}),
        )
        if measure.metric:
            self.metrics.add(_measure.metric())
        return _measure

    @classmethod
    def from_yaml(cls, path: str):
        config = schema.Config.from_yaml(path)
        return cls(config)

    def ensure_table(self, table: schema.Table) -> Table:
        if table.id not in self.tables:
            self.tables[table.id] = Table(
                **table.dict(include={"id", "source", "description", "primary_key"}),
            )
        return self.tables[table.id]

    def get_computation(self, query: schema.Query) -> Computation:
        """Returns an object that can then be executed on a backend."""
        types = {}
        metrics = {m.metric: self.metrics.get(m.metric) for m in query.metrics}
        tables = defaultdict(lambda: [])

        # group measures by anchor
        for metric in metrics.values():
            types[metric.id] = metric.type
            for measure in metric.measures:
                tables[measure.table.id].append(measure.id)

        # process dimensions
        for request in query.dimensions:
            union = self.unions.get(request.dimension)
            if union is not None:
                types[request.dimension] = union.type
            else:
                types[request.dimension] = self.dimensions.get(request.dimension).type
            if request.transform is not None:
                transform = self.transforms[request.transform.id]
                if transform.return_type is not None:
                    types[request.dimension] = transform.return_type

        # get queries for each anchor
        queries = []
        for measures in tables.values():
            queries.append(
                self.get_relational_query(
                    measures=measures,
                    dimensions=query.dimensions,
                    filters=query.filters,
                )
            )

        return Computation(
            types=types,
            metrics={k: v.expr for k, v in metrics.items()},
            queries=queries,
            merge=[d.dimension for d in query.dimensions],
        )

    def get_metadata(self, query: schema.Query) -> Dict[str, Calculation]:
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

    def suggest_metrics(self, query: schema.Query) -> List[Measure]:
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

    def suggest_dimensions(self, query: schema.Query) -> List[Dimension]:
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

    @cached_property
    def metadata(self):
        return {**self.metrics, **self.dimensions, **self.unions}

    def resolve_metrics(self):
        resolver = MetricResolver(
            {k: v.expr for k, v in self.metrics.items()}, set(self.measures)
        )
        for m in self.metrics.values():
            resolver.resolve(m.expr)

    def get_relational_query(
        self,
        measures: List[str],
        dimensions: List[schema.QueryDimensionRequest] = [],
        filters: List[schema.QueryDimensionFilter] = {},
    ) -> AggregateQuery:
        measure_id, *measures = measures
        measure = self.measures.get(measure_id)
        anchor = measure.table
        query = AggregateQuery(table=anchor)
        query.add_measure(measure_id)

        transform_compilers = {}
        for request in dimensions:
            if request.transform is not None:
                transform = self.transforms.get(request.transform.id)
                if transform is None:
                    raise KeyError(
                        f"Transform function {request.transform.id} doesn't exist"
                    )
                transform_compilers[request.dimension] = transform.get_compiler(
                    request.transform.args
                )

        for measure_id in measures:
            query.add_measure(measure_id)
        for request in dimensions:
            query.add_dimension(
                request.dimension, transform=transform_compilers.get(request.dimension)
            )
        for request in filters:
            filter = self.filters.get(request.filter.id)
            if filter is None:
                raise KeyError(f"Filter function {request.id} doesn't exist")
            query.add_filter(
                request.dimension, filter.get_compiler(request.filter.args)
            )

        return query
