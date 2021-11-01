import json

from ariadne import ObjectType, QueryType, UnionType

from nestor.ql import parse_query
from nestor.server.schema import LocaleDefinition
from nestor.store import calculations, schema

Query = QueryType()
Store = ObjectType("Store")
Metric = ObjectType("Metric")
Dimension = ObjectType("Dimension")
ResultColumn = UnionType("ResultColumn")

types = [Store, Metric, Dimension, Query, ResultColumn]


@Query.field("store")
def resolve_store(_, info):
    store = info.context["store"]
    return {
        "metrics": store.metrics.values(),
        "dimensions": store.dimensions.values(),
    }


def _exec(info, query: Query):
    store = info.context["store"]
    connection = info.context["connection"]
    computation = store.get_computation(query)
    result = connection.compute(computation)
    df = result.data
    return {
        "data": json.loads(df.to_json(orient="records")),
        "metadata": {
            "raw_query": result.raw_query,
            "locale": LocaleDefinition.from_locale_name("en-US").dict(),
            "columns": [c for c in store._all.values() if c.id in df.columns],
            # id, name, format spec,
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
def resolve_ql_query(obj, info, *, input: str):
    query = parse_query(input)
    return _exec(info, query)


@Metric.field("expr")
@Dimension.field("expr")
def resolve_expr(obj, *_):
    return obj.str_expr


@ResultColumn.type_resolver
def resolve_column_type(obj, *_):
    if isinstance(obj, calculations.Metric):
        return "Metric"
    if isinstance(obj, calculations.Dimension):
        return "Dimension"
    raise TypeError(f"Unknown type of object {obj}")  # this shouldn't ever happen
