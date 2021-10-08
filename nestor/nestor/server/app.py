import os
from functools import cache
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from nestor.backends.base import Connection
from nestor.backends.profiles import ProfilesConfig
from nestor.server import schema, static
from nestor.server.proxy import StoreProxy


@cache
def get_store() -> StoreProxy:
    path = os.getenv("NESTOR_STORE_CONFIG_PATH")
    return StoreProxy(path, cache=False)


@cache
def get_connection() -> Connection:
    path = os.getenv("NESTOR_PROFILES_CONFIG_PATH")
    profiles = ProfilesConfig.from_yaml(path)
    profile = os.getenv("NESTOR_PROFILE", None)
    return profiles.get_connection(profile)


app = FastAPI()
app.mount("/static", StaticFiles(directory=Path(static.__file__).parent), name="static")
api = APIRouter()


@app.get("/")
def index(request: Request):
    return RedirectResponse(request.url_for("static", path="index.html"))


@api.post("/query/", response_model=schema.QueryResult)
def query(
    query: schema.Query,
    store: StoreProxy = Depends(get_store),
    connection: Connection = Depends(get_connection),
):
    comp = store.execute_query(query)
    df = connection.execute(comp)
    return schema.QueryResult(
        data=df.to_dict(orient="records"),
        query=query,
        metadata=schema.QueryResultMetadata(
            columns={c: store._all[c].metadata for c in df.columns},
            store=schema.Store(
                measures=store.suggest_measures(query),
                dimensions=store.suggest_dimensions(query),
            ),
        ),
    )


@api.get("/store/", response_model=schema.Store)
def store(store: StoreProxy = Depends(get_store)):
    return schema.Store(
        measures=list(store.measures.values()),
        dimensions=list(store.dimensions.values()),
    )


@api.get("/measures/", response_model=List[schema.Measure])
def list_measures(id: str):
    pass


@api.get("/dimensions/", response_model=List[schema.Dimension])
def list_dimensions(id: str):
    pass


@api.get("/table/<id>/", response_model=schema.Table)
def get_table(id: str):
    pass


app.include_router(api, prefix="/api")
