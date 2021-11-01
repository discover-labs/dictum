import os
from functools import cache
from pathlib import Path

from ariadne import gql, make_executable_schema, snake_case_fallback_resolvers
from ariadne.asgi import GraphQL
from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles

from nestor.backends.profiles import ProfilesConfig
from nestor.server import static
from nestor.server.resolvers import types
from nestor.store import Store

schema_text = (Path(__file__).parent / "schema.graphql").read_text()
schema = make_executable_schema(gql(schema_text), *types, snake_case_fallback_resolvers)
static = StaticFiles(directory=Path(static.__file__).parent)


@cache
def get_ctx():
    path = os.getenv("NESTOR_PROFILES_CONFIG_PATH")
    profiles = ProfilesConfig.from_yaml(path)
    profile = os.getenv("NESTOR_PROFILE", None)
    connection = profiles.get_connection(profile)
    store = Store.from_yaml(os.environ["NESTOR_STORE_CONFIG_PATH"])
    return {"store": store, "connection": connection}


def get_context_value(request):
    return get_ctx()


app = Starlette()
app.mount("/graphql", GraphQL(schema, context_value=get_context_value))
# app.mount("/", static)
