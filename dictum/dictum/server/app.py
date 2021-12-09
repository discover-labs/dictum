import os
from pathlib import Path

from ariadne import gql, make_executable_schema, snake_case_fallback_resolvers
from ariadne.asgi import GraphQL
from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles

from dictum.client import CachedClient
from dictum.server import static
from dictum.server.resolvers import types
from dictum.data_model import DataModel

schema_text = (Path(__file__).parent / "schema.graphql").read_text()
schema = make_executable_schema(gql(schema_text), *types, snake_case_fallback_resolvers)
static = StaticFiles(directory=Path(static.__file__).parent, html=True)


def get_ctx():
    store = os.environ["NESTOR_STORE_CONFIG_PATH"]
    profiles = os.getenv("NESTOR_PROFILES_CONFIG_PATH", None)
    profile = os.getenv("NESTOR_PROFILE", None)
    return {
        "client": CachedClient(path=store, profiles=profiles, profile=profile),
        "store": DataModel.from_yaml(store),
    }


def get_context_value(_):
    return get_ctx()


app = Starlette()
app.mount("/graphql", GraphQL(schema, context_value=get_context_value))
app.mount("/", static)
