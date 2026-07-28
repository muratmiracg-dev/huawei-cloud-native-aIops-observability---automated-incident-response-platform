from fastapi import FastAPI
from fastapi.testclient import TestClient

from platform_core.app_factory import create_service_app
from platform_core.settings import Settings


def build_app(*, fault_injection: bool) -> FastAPI:
    app = create_service_app(
        title="Test",
        description="Test app",
        settings=Settings(
            service_name="test-api",
            enable_tracing=False,
            enable_fault_injection=fault_injection,
        ),
    )

    @app.get("/business")
    async def business() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_health_metrics_and_request_id() -> None:
    with TestClient(build_app(fault_injection=False)) as client:
        response = client.get("/health/live", headers={"x-request-id": "test-123"})
        assert response.status_code == 200
        assert response.headers["x-request-id"] == "test-123"
        assert response.json()["status"] == "alive"
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "http_server_requests_total" in metrics.text


def test_fault_configuration_is_protected() -> None:
    with TestClient(build_app(fault_injection=False)) as client:
        response = client.put(
            "/internal/faults",
            json={"latency_ms": 0, "error_rate": 1},
        )
        assert response.status_code == 403


def test_fault_injection_and_recovery() -> None:
    with TestClient(build_app(fault_injection=True)) as client:
        configured = client.put(
            "/internal/faults",
            json={"latency_ms": 0, "error_rate": 1},
        )
        assert configured.status_code == 200
        assert client.get("/business", headers={"x-request-id": "always-fail"}).status_code == 503
        assert client.get("/health/ready").status_code == 200
        assert client.delete("/internal/faults").status_code == 200
        assert client.get("/business").status_code == 200
