from threading import Lock

from fastapi import HTTPException
from pydantic import BaseModel, Field

from platform_core.app_factory import create_service_app
from platform_core.metrics import BUSINESS_EVENTS
from platform_core.settings import Settings


class Product(BaseModel):
    sku: str
    name: str
    price: float = Field(gt=0)
    available: int = Field(ge=0)


class ReservationRequest(BaseModel):
    quantity: int = Field(gt=0, le=100)


class CatalogStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._products = {
            "OBS-100": Product(
                sku="OBS-100",
                name="Observability Starter",
                price=149.0,
                available=120,
            ),
            "SRE-200": Product(
                sku="SRE-200",
                name="SRE Professional",
                price=299.0,
                available=75,
            ),
            "AIOPS-300": Product(
                sku="AIOPS-300",
                name="AIOps Enterprise",
                price=499.0,
                available=40,
            ),
        }

    def list(self) -> list[Product]:
        with self._lock:
            return [product.model_copy() for product in self._products.values()]

    def get(self, sku: str) -> Product | None:
        with self._lock:
            product = self._products.get(sku)
            return product.model_copy() if product else None

    def reserve(self, sku: str, quantity: int) -> Product:
        with self._lock:
            product = self._products.get(sku)
            if not product:
                raise KeyError(sku)
            if product.available < quantity:
                raise ValueError("insufficient stock")
            product.available -= quantity
            return product.model_copy()


settings = Settings(service_name="catalog-api")
store = CatalogStore()
app = create_service_app(
    title="Catalog API",
    description="Observable catalog and inventory workload for SRE demonstrations.",
    settings=settings,
)


@app.get("/products", response_model=list[Product], tags=["catalog"])
async def list_products() -> list[Product]:
    return store.list()


@app.get("/products/{sku}", response_model=Product, tags=["catalog"])
async def get_product(sku: str) -> Product:
    product = store.get(sku)
    if not product:
        BUSINESS_EVENTS.labels("catalog-api", "product_lookup", "not_found").inc()
        raise HTTPException(status_code=404, detail="product not found")
    BUSINESS_EVENTS.labels("catalog-api", "product_lookup", "success").inc()
    return product


@app.post("/products/{sku}/reserve", response_model=Product, tags=["catalog"])
async def reserve_product(sku: str, payload: ReservationRequest) -> Product:
    try:
        product = store.reserve(sku, payload.quantity)
    except KeyError as exc:
        BUSINESS_EVENTS.labels("catalog-api", "inventory_reservation", "not_found").inc()
        raise HTTPException(status_code=404, detail="product not found") from exc
    except ValueError as exc:
        BUSINESS_EVENTS.labels("catalog-api", "inventory_reservation", "rejected").inc()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    BUSINESS_EVENTS.labels("catalog-api", "inventory_reservation", "success").inc()
    return product
