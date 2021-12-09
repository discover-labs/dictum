from ariadne import InterfaceType, ObjectType, QueryType

from dictum.client import CachedClient
from dictum.ql import compile_query
from dictum.data_model import DataModel, schema
from dictum.data_model.formatting import Formatter

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
    client: CachedClient = info.context["client"]
    store: DataModel = info.context["store"]
    result = client.execute(query)
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
    query = compile_query(input)
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
    if name == "DimensionsUnion":
        return "Dimension"
    return None
