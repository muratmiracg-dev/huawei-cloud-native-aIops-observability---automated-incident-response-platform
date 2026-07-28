import pytest
from fastapi.testclient import TestClient

from services.catalog.main import CatalogStore, app


def test_catalog_store_reservation() -> None:
    store = CatalogStore()
    before = store.get("OBS-100")
    assert before is not None
    after = store.reserve("OBS-100", 2)
    assert after.available == before.available - 2


def test_catalog_store_rejects_invalid_reservation() -> None:
    store = CatalogStore()
    with pytest.raises(KeyError):
        store.reserve("UNKNOWN", 1)
    with pytest.raises(ValueError, match="insufficient stock"):
        store.reserve("AIOPS-300", 10_000)


def test_catalog_api_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/products")
        assert response.status_code == 200
        assert len(response.json()) == 3
        product = client.get("/products/OBS-100")
        assert product.status_code == 200
        assert product.json()["price"] == 149.0
        missing = client.get("/products/MISSING")
        assert missing.status_code == 404
        reserved = client.post("/products/SRE-200/reserve", json={"quantity": 1})
        assert reserved.status_code == 200
        rejected = client.post("/products/SRE-200/reserve", json={"quantity": 100})
        assert rejected.status_code == 409
        missing_reservation = client.post("/products/MISSING/reserve", json={"quantity": 1})
        assert missing_reservation.status_code == 404
