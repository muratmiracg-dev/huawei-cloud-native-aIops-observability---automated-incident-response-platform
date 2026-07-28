import asyncio
import uuid
from dataclasses import dataclass
from threading import Lock

import httpx
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

from platform_core.app_factory import create_service_app
from platform_core.metrics import BUSINESS_EVENTS, DEPENDENCY_REQUESTS
from platform_core.settings import Settings


class OrderRequest(BaseModel):
    sku: str
    quantity: int = Field(gt=0, le=25)
    payment_token: str = Field(min_length=8, max_length=128)


class Order(BaseModel):
    order_id: str
    sku: str
    quantity: int
    total: float
    status: str
    payment_id: str


class OrderStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._orders: dict[str, Order] = {}
        self._idempotency: dict[str, str] = {}

    def get_by_key(self, key: str) -> Order | None:
        with self._lock:
            order_id = self._idempotency.get(key)
            return self._orders.get(order_id) if order_id else None

    def save(self, key: str, order: Order) -> Order:
        with self._lock:
            existing_id = self._idempotency.get(key)
            if existing_id:
                return self._orders[existing_id]
            self._orders[order.order_id] = order
            self._idempotency[key] = order.order_id
            return order

    def get(self, order_id: str) -> Order | None:
        with self._lock:
            return self._orders.get(order_id)


@dataclass
class ServiceClient:
    catalog_url: str
    payments_url: str
    retries: int = 2

    async def _request(
        self,
        method: str,
        url: str,
        *,
        dependency: str,
        operation: str,
        json: dict[str, object] | None = None,
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.request(method, url, json=json)
                outcome = "success" if response.status_code < 500 else "server_error"
                DEPENDENCY_REQUESTS.labels("orders-api", dependency, operation, outcome).inc()
                return response
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = exc
                DEPENDENCY_REQUESTS.labels(
                    "orders-api", dependency, operation, "transport_error"
                ).inc()
                if attempt < self.retries:
                    await asyncio.sleep(0.05 * (2**attempt))
        raise RuntimeError(f"{dependency} unavailable") from last_error

    async def product(self, sku: str) -> dict[str, object]:
        response = await self._request(
            "GET",
            f"{self.catalog_url}/products/{sku}",
            dependency="catalog-api",
            operation="get_product",
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="product not found")
        if response.status_code >= 500:
            raise HTTPException(status_code=503, detail="catalog unavailable")
        return response.json()

    async def reserve(self, sku: str, quantity: int) -> None:
        response = await self._request(
            "POST",
            f"{self.catalog_url}/products/{sku}/reserve",
            dependency="catalog-api",
            operation="reserve_inventory",
            json={"quantity": quantity},
        )
        if response.status_code == 409:
            raise HTTPException(status_code=409, detail="insufficient stock")
        if response.status_code >= 400:
            raise HTTPException(status_code=503, detail="inventory reservation failed")

    async def pay(
        self,
        order_id: str,
        amount: float,
        payment_token: str,
    ) -> dict[str, object]:
        response = await self._request(
            "POST",
            f"{self.payments_url}/payments",
            dependency="payments-api",
            operation="create_payment",
            json={
                "order_id": order_id,
                "amount": amount,
                "payment_token": payment_token,
            },
        )
        if response.status_code == 402:
            raise HTTPException(status_code=402, detail="payment declined")
        if response.status_code >= 400:
            raise HTTPException(status_code=503, detail="payments unavailable")
        return response.json()


settings = Settings(service_name="orders-api")
store = OrderStore()
service_client = ServiceClient(settings.catalog_url, settings.payments_url)
app = create_service_app(
    title="Orders API",
    description="Observable order orchestration workload with retry and idempotency.",
    settings=settings,
)


@app.post("/orders", response_model=Order, status_code=201, tags=["orders"])
async def create_order(
    payload: OrderRequest,
    idempotency_key: str = Header(min_length=8, max_length=128),
) -> Order:
    existing = store.get_by_key(idempotency_key)
    if existing:
        BUSINESS_EVENTS.labels("orders-api", "order", "idempotent_replay").inc()
        return existing

    product = await service_client.product(payload.sku)
    total = round(float(product["price"]) * payload.quantity, 2)
    order_id = str(uuid.uuid4())
    await service_client.reserve(payload.sku, payload.quantity)
    payment = await service_client.pay(order_id, total, payload.payment_token)
    order = store.save(
        idempotency_key,
        Order(
            order_id=order_id,
            sku=payload.sku,
            quantity=payload.quantity,
            total=total,
            status="confirmed",
            payment_id=str(payment["payment_id"]),
        ),
    )
    BUSINESS_EVENTS.labels("orders-api", "order", "confirmed").inc()
    return order


@app.get("/orders/{order_id}", response_model=Order, tags=["orders"])
async def get_order(order_id: str) -> Order:
    order = store.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order
