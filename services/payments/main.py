import hashlib
import uuid

from fastapi import HTTPException
from pydantic import BaseModel, Field

from platform_core.app_factory import create_service_app
from platform_core.metrics import BUSINESS_EVENTS
from platform_core.settings import Settings


class PaymentRequest(BaseModel):
    order_id: str
    amount: float = Field(gt=0, le=50_000)
    payment_token: str = Field(min_length=8, max_length=128)


class PaymentResult(BaseModel):
    payment_id: str
    order_id: str
    status: str
    amount: float


settings = Settings(service_name="payments-api")
app = create_service_app(
    title="Payments API",
    description="Deterministic payment simulator for telemetry and failure analysis.",
    settings=settings,
)


@app.post("/payments", response_model=PaymentResult, tags=["payments"])
async def create_payment(payload: PaymentRequest) -> PaymentResult:
    fingerprint = hashlib.sha256(payload.payment_token.encode()).hexdigest()
    if fingerprint.endswith(("0", "1")):
        BUSINESS_EVENTS.labels("payments-api", "payment", "declined").inc()
        raise HTTPException(status_code=402, detail="payment declined")
    BUSINESS_EVENTS.labels("payments-api", "payment", "approved").inc()
    return PaymentResult(
        payment_id=str(uuid.uuid4()),
        order_id=payload.order_id,
        status="approved",
        amount=payload.amount,
    )
