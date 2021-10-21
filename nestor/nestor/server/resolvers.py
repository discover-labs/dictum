from ariadne import ObjectType, QueryType, UnionType

from nestor.server.schema import LocaleDefinition
from nestor.store import calculations, schema

Query = QueryType()
Store = ObjectType("Store")
Measure = ObjectType("Measure")
Dimension = ObjectType("Dimension")
Table = ObjectType("Table")
RelatedTable = ObjectType("RelatedTable")
ResultColumn = UnionType("ResultColumn")

types = [Query, Store, Measure, Dimension, Table, RelatedTable, ResultColumn]


@Query.field("store")
def resolve_store(_, info):
    store = info.context["store"]
    return {
        "tables": store.tables.values(),
        "measures": store.measures.values(),
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
                "measures": store.suggest_measures(query),
                "dimensions": store.suggest_dimensions(query),
            },
        },
    }


@Table.field("related")
def resolve_table_related(obj, info):
    return obj.related.values()


@ResultColumn.type_resolver
def resolve_column_type(obj, *_):
    if isinstance(obj, calculations.Measure):
        return "Measure"
    if isinstance(obj, calculations.Dimension):
        return "Dimension"
    raise TypeError("TEST")
