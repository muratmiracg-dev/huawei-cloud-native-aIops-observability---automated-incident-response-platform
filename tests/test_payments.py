import hashlib

from fastapi.testclient import TestClient

from services.payments.main import app


def find_declined_token() -> str:
    for index in range(10_000):
        token = f"payment-token-{index}"
        if hashlib.sha256(token.encode()).hexdigest().endswith(("0", "1")):
            return token
    raise AssertionError("unable to find deterministic decline token")


def test_payment_approval_and_decline() -> None:
    with TestClient(app) as client:
        approved = client.post(
            "/payments",
            json={
                "order_id": "order-1",
                "amount": 149.0,
                "payment_token": "known-good-token-77",
            },
        )
        if approved.status_code == 402:
            approved = client.post(
                "/payments",
                json={
                    "order_id": "order-1",
                    "amount": 149.0,
                    "payment_token": "known-good-token-88",
                },
            )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"

        declined = client.post(
            "/payments",
            json={
                "order_id": "order-2",
                "amount": 149.0,
                "payment_token": find_declined_token(),
            },
        )
        assert declined.status_code == 402
