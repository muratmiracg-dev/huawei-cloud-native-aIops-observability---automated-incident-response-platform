import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from services.orders.main import (
    Order,
    OrderStore,
    ServiceClient,
    app,
    service_client,
)


def test_order_store_idempotency() -> None:
    store = OrderStore()
    first = Order(
        order_id="order-1",
        sku="OBS-100",
        quantity=1,
        total=149.0,
        status="confirmed",
        payment_id="payment-1",
    )
    replay = Order(
        order_id="order-2",
        sku="OBS-100",
        quantity=1,
        total=149.0,
        status="confirmed",
        payment_id="payment-2",
    )
    assert store.save("idem-key", first).order_id == "order-1"
    assert store.save("idem-key", replay).order_id == "order-1"
    assert store.get_by_key("idem-key") == first


def test_order_api_orchestration(monkeypatch) -> None:
    monkeypatch.setattr(
        service_client,
        "product",
        AsyncMock(return_value={"sku": "OBS-100", "price": 149.0}),
    )
    monkeypatch.setattr(service_client, "reserve", AsyncMock(return_value=None))
    monkeypatch.setattr(
        service_client,
        "pay",
        AsyncMock(return_value={"payment_id": "payment-test"}),
    )
    payload = {
        "sku": "OBS-100",
        "quantity": 2,
        "payment_token": "payment-token-good",
    }
    headers = {"Idempotency-Key": "order-api-test-key"}
    with TestClient(app) as client:
        created = client.post("/orders", json=payload, headers=headers)
        assert created.status_code == 201
        assert created.json()["total"] == 298.0
        replay = client.post("/orders", json=payload, headers=headers)
        assert replay.status_code == 201
        assert replay.json()["order_id"] == created.json()["order_id"]
        fetched = client.get(f"/orders/{created.json()['order_id']}")
        assert fetched.status_code == 200
        assert client.get("/orders/not-found").status_code == 404
    service_client.reserve.assert_awaited_once()
    service_client.pay.assert_awaited_once()


def response(status: int, payload: dict[str, object]) -> httpx.Response:
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("GET", "http://dependency"),
    )


def test_service_client_maps_dependency_responses(monkeypatch) -> None:
    client = ServiceClient("http://catalog", "http://payments")
    monkeypatch.setattr(
        client,
        "_request",
        AsyncMock(return_value=response(200, {"sku": "OBS-100", "price": 149.0})),
    )
    product = asyncio.run(client.product("OBS-100"))
    assert product["price"] == 149.0

    monkeypatch.setattr(client, "_request", AsyncMock(return_value=response(404, {})))
    with pytest.raises(HTTPException) as missing:
        asyncio.run(client.product("MISSING"))
    assert missing.value.status_code == 404

    monkeypatch.setattr(client, "_request", AsyncMock(return_value=response(503, {})))
    with pytest.raises(HTTPException) as unavailable:
        asyncio.run(client.product("OBS-100"))
    assert unavailable.value.status_code == 503

    monkeypatch.setattr(client, "_request", AsyncMock(return_value=response(409, {})))
    with pytest.raises(HTTPException) as stock:
        asyncio.run(client.reserve("OBS-100", 1))
    assert stock.value.status_code == 409

    monkeypatch.setattr(client, "_request", AsyncMock(return_value=response(500, {})))
    with pytest.raises(HTTPException) as reservation:
        asyncio.run(client.reserve("OBS-100", 1))
    assert reservation.value.status_code == 503

    monkeypatch.setattr(client, "_request", AsyncMock(return_value=response(402, {})))
    with pytest.raises(HTTPException) as declined:
        asyncio.run(client.pay("order", 10.0, "token-value"))
    assert declined.value.status_code == 402

    monkeypatch.setattr(
        client,
        "_request",
        AsyncMock(return_value=response(200, {"payment_id": "payment-1"})),
    )
    payment = asyncio.run(client.pay("order", 10.0, "token-value"))
    assert payment["payment_id"] == "payment-1"
