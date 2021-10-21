from collections import UserDict
from functools import cached_property
from typing import Dict, List

from nestor.store import schema
from nestor.store.calculations import Calculation, Dimension, Measure, Metric
from nestor.store.computation import Computation, JoinTree, RelationalQuery
from nestor.store.expr.parser import parse_expr
from nestor.store.table import RelatedTable, Table


class CalculationDict(UserDict):

    T = Calculation

    def __getitem__(self, key: str) -> T:
        result = self.data.get(key)
        if result is None:
            raise KeyError(f"{self.T.__name__} {key} does not exist")
        return result

    def __setitem__(self, name: str, value):
        if name in self.data:
            raise KeyError(f"{self.T.__name__} {name} already exists")
        return super().__setitem__(name, value)

    def get(self, key: str) -> T:
        return self[key]


class MeasureDict(CalculationDict):
    T = Measure


class DimensionDict(CalculationDict):
    T = Dimension


class MetricDict(CalculationDict):
    T = Metric


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

    aggregate = {
        "sum",
        "avg",
        "max",
        "min",
        "distinct",
    }
    scalar = {
        "abs",
        "floor",
        "ceil",
        "round",
    }
    builtins = scalar | aggregate

    def __init__(self, config: schema.Config):
        self.tables: Dict[str, Table] = {}
        self.measures = MeasureDict()
        self.dimensions = DimensionDict()
        self.metrics = MetricDict()

        for metric_id, metric in config.metrics.items():
            self.metrics[metric_id] = Metric(
                id=metric_id,
                expr=parse_expr(metric.expr),
                str_expr=metric.expr,
                format=metric.format,
                **metric.dict(include={"name", "description"}),
            )
        for table_id, config_table in config.tables.items():
            table = self.ensure_table(config_table, table_id)
            for related_id, related in config_table.related.items():
                if related.table not in config.tables:
                    raise KeyError(
                        f"Table {related.table} is referenced as a foreign key target "
                        f"for table {table_id}, but it's not defined in the config."
                    )
                related_table = config.tables[related.table]
                if related_table.primary_key is None:
                    raise ValueError(
                        f"Table {related.table} is a related table for {table_id}, but "
                        "it doesn't have a primary key."
                    )
                table.related[related_id] = RelatedTable(
                    table=self.ensure_table(related_table, related.table),
                    foreign_key=related.foreign_key,
                )
            for measure_id, measure in config_table.measures.items():
                _measure = self.build_measure(measure_id, measure)
                self.measures[_measure.id] = _measure
                table.measures[_measure.id] = _measure
            for dimension_id, dimension in config_table.dimensions.items():
                _dimension = Dimension(
                    id=dimension_id,
                    expr=parse_expr(dimension.expr),
                    str_expr=dimension.expr,
                    type=dimension.type,
                    **dimension.dict(include={"name", "description", "format"}),
                )
                table.dimensions[dimension_id] = _dimension
                self.dimensions[dimension_id] = _dimension
        for table in self.tables.values():
            table.resolve_calculations()

    def build_measure(self, id: str, measure: schema.Measure) -> Measure:
        _measure = Measure(
            id=id,
            expr=parse_expr(measure.expr),
            str_expr=measure.expr,
            format=measure.format,
            **measure.dict(include={"name", "description"}),
        )
        if not measure.metric:
            return _measure
        self.metrics[id] = _measure.metric()
        return _measure

    @classmethod
    def from_yaml(cls, path: str):
        config = schema.Config.from_yaml(path)
        return cls(config)

    def ensure_table(self, table: schema.Table, table_id: str) -> Table:
        if table_id not in self.tables:
            self.tables[table_id] = Table(
                id=table_id,
                **table.dict(include={"source", "description", "primary_key"}),
            )
        return self.tables[table_id]

    @cached_property
    def measures_tables(self) -> Dict[str, Table]:
        """Find a table id by measure id."""
        result = {}
        for table in self.tables.values():
            for k in table.measures:
                result[k] = table
        return result

    @cached_property
    def dimensions_tables(self) -> Dict[str, Table]:
        result = {}
        for table in self.tables.values():
            for k in table.dimensions:
                result[k] = table
        return result

    def get_fact_tables(self, query: schema.Query) -> List[RelationalQuery]:
        """Get a list of fact tables' join trees with relevant measures.
        Extract measure references from each metric and
        """
        facts: Dict[str, RelationalQuery] = {}

        for metric_id in query.metrics:
            metric = self.metrics[metric_id]
            for measure_id in metric.measures:
                measure = (
                    self.measures.get(measure_id)
                    if measure_id in self.measures
                    else self.metrics.get(measure_id)
                )
                table = self.measures_tables[measure.id]

                # create a FactTable with all dimensions and joins once
                if table.id not in facts:
                    facts[table.id] = RelationalQuery(
                        join_tree=JoinTree(table=table, identity=table.id)
                    )
                    fact = facts[table.id]
                    for dimension_id in query.dimensions:
                        expr, paths = table.get_dimension_expr_and_paths(dimension_id)
                        fact.groupby[dimension_id] = expr
                        for path in paths:
                            fact.join_tree.add_path(path[1:])
                    for filter in query.filters:
                        expr, paths = table.get_filter_expr_and_paths(
                            parse_expr(filter)
                        )
                        fact.filters.append(expr)
                        for path in paths:
                            fact.join_tree.add_path(path[1:])
                else:
                    fact = facts[table.id]

                # add current measure
                expr, paths = table.get_measure_expr_and_paths(measure_id)
                fact.aggregate[measure_id] = expr
                for path in paths:
                    fact.join_tree.add_path(path[1:])

        return list(facts.values())

    def get_computation(self, query: schema.Query) -> Computation:
        """Returns an object that can then be executed on a backend."""
        metrics = {m: self.metrics.get(m).expr for m in query.metrics}
        facts = self.get_fact_tables(query)
        return Computation(metrics=metrics, queries=facts, merge=query.dimensions)

    def suggest_measures(self, query: schema.Query) -> List[Measure]:
        """Suggest a list of possible measures based on a query.
        Only measures that can be used with all the dimensions from the query
        """
        result = []
        query_dims = set(query.dimensions)
        for measure in self.measures.values():
            if measure.id in query.measures:
                continue
            table = self.measures_tables.get(measure.id)
            allowed_dims = set(table.allowed_dimensions)
            if query_dims & allowed_dims == query_dims:
                result.append(measure)
        return sorted(result, key=lambda x: (x.name))

    def suggest_dimensions(self, query: schema.Query) -> List[Dimension]:
        """Suggest a list of possible dimensions based on a query. Only dimensions
        shared by all measures that are already in the query.
        """
        dims = set(self.dimensions)
        dims = dims - set(query.dimensions)
        for measure_id in query.measures:
            table = self.measures_tables.get(measure_id)
            dims = dims & set(table.allowed_dimensions)
        return sorted([self.dimensions[d] for d in dims], key=lambda x: x.name)

    def get_range_computation(self, dimension_id: str) -> Computation:
        """Get a computation that will compute a range of values for a given dimension.
        This is seriously out of line with what different parts of computation mean, so
        maybe we need to give them more abstract names.
        """
        dimension = self.dimensions.get(dimension_id)
        table = self.dimensions_tables.get(dimension_id)
        min_, max_ = dimension.prepare_range_expr([table.id])
        return Computation(
            queries=[
                RelationalQuery(
                    join_tree=JoinTree(table=table, identity=table.id),
                    aggregate={"min": min_, "max": max_},
                )
            ]
        )

    def get_values_computation(self, dimension_id: str) -> Computation:
        """Get a computation that will compute a list of unique possible values for this
        dimension.
        """
        dimension = self.dimensions.get(dimension_id)
        table = self.dimensions_tables.get(dimension_id)
        return Computation(
            queries=[
                RelationalQuery(
                    join_tree=JoinTree(table=table, identity=table.id),
                    groupby={"values": dimension.prepare_expr([table.id])},
                )
            ]
        )

    @cached_property
    def _all(self):
        return {**self.measures, **self.dimensions}
