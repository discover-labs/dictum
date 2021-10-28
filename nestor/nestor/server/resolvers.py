from ariadne import ObjectType, QueryType, UnionType

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


@Query.field("query")
def resolve_store_query(obj, info, *, input: dict):
    store = info.context["store"]
    connection = info.context["connection"]
    query = schema.Query.parse_obj(input)
    computation = store.get_computation(query)
    df = connection.compute(computation)
    return {
        "data": df.to_dict(orient="records"),
        "metadata": {
            "locale": LocaleDefinition.from_locale_name("en-US").dict(),
            "columns": [c for c in store._all.values() if c.id in df.columns],
            "store": {
                "tables": store.tables.values(),
                "metrics": store.suggest_metrics(query),
                "dimensions": store.suggest_dimensions(query),
            },
        },
    }


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
    raise TypeError("TEST")
