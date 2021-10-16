import os
from functools import cache
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from nestor.backends.base import Connection
from nestor.backends.profiles import ProfilesConfig
from nestor.server import schema, static
from nestor.server.proxy import StoreProxy
from nestor.store.schema.types import DimensionType

static_path = Path(static.__file__).parent


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
app.mount("/static", StaticFiles(directory=static_path), name="static")
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
            locale=schema.LocaleDefinition.from_locale_name("en-US"),
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


@api.get("/filter/{pk}/", response_model=schema.Filter)
def get_filter_info(
    pk: str,
    store: StoreProxy = Depends(get_store),
    connection: Connection = Depends(get_connection),
):
    try:
        dimension = store.get_dimension(pk)
    except ValueError:  # TODO: meaningful store exceptions
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    range_ = None
    values = None
    if dimension.type in (DimensionType.ordinal, DimensionType.nominal):
        computation = store.get_values_computation(dimension.id)
        df = connection.execute(computation)
        values = df["values"].unique().tolist()
        if dimension.type == "ordinal":
            range_ = [min(values), max(values)]
    if dimension.type == DimensionType.continuous:
        computation = store.get_range_computation(dimension.id)
        df = connection.execute(computation)
        range_ = next(df.itertuples(index=False))
    return schema.Filter(
        dimension=dimension, info=schema.FilterInfo(range=range_, values=values)
    )


app.include_router(api, prefix="/api")
