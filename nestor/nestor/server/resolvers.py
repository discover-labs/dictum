from ariadne import InterfaceType, ObjectType, QueryType

from nestor.backends.base import Connection
from nestor.ql import parse_query
from nestor.store import Store, schema
from nestor.store.formatting import Formatter

Query = QueryType()
StoreType = ObjectType("Store")
MetricType = ObjectType("Metric")
DimensionType = ObjectType("Dimension")
CalculationInterface = InterfaceType("Calculation")

types = [StoreType, CalculationInterface, MetricType, DimensionType, Query]


@Query.field("store")
def resolve_store(_, info):
    store = info.context["store"]
    return {
        "metrics": store.metrics.values(),
        "dimensions": store.dimensions.values(),
    }


def _exec(info, query: schema.Query):
    store: Store = info.context["store"]
    connection: Connection = info.context["connection"]
    computation = store.get_computation(query)
    result = connection.compute(computation)
    metadata = store.get_metadata(query)
    formatter = Formatter(store.locale, fields=metadata, formatting=query.formatting)
    data = formatter.format(result.data)
    return {
        "data": data,
        "metadata": {
            "formatting": query.formatting,
            "locale": store.locale,
            "raw_query": result.raw_query,
            "columns": list(metadata.values()),
            "store": {
                "tables": store.tables.values(),
                "metrics": store.suggest_metrics(query),
                "dimensions": store.suggest_dimensions(query),
            },
        },
    }


@Query.field("query")
def resolve_store_query(obj, info, *, input: dict):
    query = schema.Query.parse_obj(input)
    return _exec(info, query)


@Query.field("qlQuery")
def resolve_ql_query(obj, info, *, input: str, formatting: bool = True):
    query = parse_query(input)
    query.formatting = formatting
    return _exec(info, query)


@MetricType.field("expr")
@DimensionType.field("expr")
def resolve_expr(obj, *_):
    return obj.str_expr


@CalculationInterface.type_resolver
def resolve_calculation_type(obj, *_):
    name = obj.__class__.__name__
    if name in {"Metric", "Dimension"}:
        return name
    return None
