from functools import cached_property
from typing import Dict, List

from nestor.store import schema
from nestor.store.calculations import Dimension, Measure
from nestor.store.computation import Computation, FactTable, JoinTree
from nestor.store.expr.parser import parse_expr
from nestor.store.table import RelatedTable, Table


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
        self.measures: Dict[str, Measure] = {}
        self.dimensions: Dict[str, Dimension] = {}
        for table_id, config_table in config.tables.items():
            table = self.ensure_table(config_table, table_id)
            for related_id, related in config_table.related.items():
                if related.table not in config.tables:
                    raise KeyError(
                        f"Table {related.table} is referenced as a foreign key target "
                        f"for table {table_id}, but it's not defined in the config."
                    )
                table.related[related_id] = RelatedTable(
                    table=self.ensure_table(
                        config.tables[related.table], related.table
                    ),
                    foreign_key=related.foreign_key,
                )
            for measure_id, measure in config_table.measures.items():
                _measure = Measure(
                    id=measure_id,
                    expr=parse_expr(measure.expr),
                    str_expr=measure.expr,
                    **measure.dict(include={"name", "description", "format"}),
                )
                self.measures[measure_id] = _measure
                table.measures[measure_id] = _measure
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

    def get_fact_tables(self, query: schema.Query) -> List[FactTable]:
        """Get a list of fact tables' join trees with relevant measures."""
        facts: Dict[str, FactTable] = {}
        for measure_id in query.measures:
            table = self.measures_tables.get(measure_id)
            if table is None:
                raise ValueError(f"Measure {measure_id} does not exist")

            # create a FactTable with all dimensions and joins once
            if table.id not in facts:
                facts[table.id] = FactTable(
                    join_tree=JoinTree(table=table, identity=table.id)
                )
                fact = facts[table.id]
                for dimension_id in query.dimensions:
                    expr, paths = table.get_dimension_expr_and_paths(dimension_id)
                    fact.dimensions[dimension_id] = expr
                    for path in paths:
                        fact.join_tree.add_path(path[1:])
                for filter in query.filters:
                    expr, paths = table.get_filter_expr_and_paths(parse_expr(filter))
                    fact.filters.append(expr)
                    for path in paths:
                        fact.join_tree.add_path(path[1:])
            else:
                fact = facts[table.id]

            # add current measure
            expr, paths = table.get_measure_expr_and_paths(measure_id)
            fact.measures[measure_id] = expr
            for path in paths:
                fact.join_tree.add_path(path[1:])

        return list(facts.values())

    def execute_query(self, query: schema.Query) -> Computation:
        """Returns an object that can then be executed on a backend."""
        facts = self.get_fact_tables(query)
        return Computation(facts=facts, groupby=query.dimensions)

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
        return result

    def suggest_dimensions(self, query: schema.Query) -> List[Dimension]:
        """Suggest a list of possible dimensions based on a query. Only dimensions
        shared by all measures that are already in the query.
        """
        dims = set(self.dimensions)
        dims = dims - set(query.dimensions)
        for measure_id in query.measures:
            table = self.measures_tables.get(measure_id)
            dims = dims & set(table.allowed_dimensions)
        return [self.dimensions[d] for d in dims]

    @cached_property
    def _all(self):
        return {**self.measures, **self.dimensions}
