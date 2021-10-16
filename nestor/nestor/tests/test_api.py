from unittest import mock

import pytest
from fastapi.testclient import TestClient

from nestor.server import app
from nestor.tests.conftest import chinook_path


@pytest.fixture(scope="function")
def client(monkeypatch, connection):
    monkeypatch.setenv("NESTOR_STORE_CONFIG_PATH", str(chinook_path))
    profiles = mock.MagicMock()
    profiles.return_value.get_connection.return_value = connection
    with mock.patch("nestor.backends.profiles.ProfilesConfig.from_yaml", profiles):
        yield TestClient(app.app)


def test_query(client: TestClient):
    q = {"measures": ["track_count"]}
    res = client.post("/api/query/", json=q)
    res.raise_for_status()
    assert res.json()["data"][0]["track_count"] == 3503

    q = {"measures": ["track_count"], "filters": [":genre = 'Rock'"]}
    res = client.post("/api/query/", json=q)
    res.raise_for_status()
    assert res.json()["data"][0]["track_count"] == 1297


def test_store(client: TestClient):
    res = client.get("/api/store/")
    res.raise_for_status()
    store = res.json()
    assert len(store["measures"]) == 9
    assert len(store["dimensions"]) == 14


def test_dimension_info_nominal(client: TestClient):
    res = client.get("/api/dimensions/customer_country/")
    res.raise_for_status()
    data = res.json()
    assert data["range"] is None
    assert len(data["values"]) == 24


def test_dimension_info_ordinal(client: TestClient):
    res = client.get("/api/dimensions/track_length_10s_bins/")
    res.raise_for_status()
    data = res.json()
    assert data["range"] == [0, 5280]
    assert len(data["values"]) == 139


def test_dimension_info_continuous(client: TestClient):
    res = client.get("/api/dimensions/order_amount/")
    res.raise_for_status()
    data = res.json()
    assert data["range"] == [0.99, 25.86]
    assert data["values"] is None
