"""HTTP metrics must be labelled by route template, not by raw URL path."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from platform_core.app_factory import create_service_app
from platform_core.middleware import UNMATCHED_ROUTE
from platform_core.settings import Settings

SERVICE = "cardinality-test-api"


def build_app() -> FastAPI:
    app = create_service_app(
        title="Cardinality test",
        description="Route label test app",
        settings=Settings(service_name=SERVICE, enable_tracing=False, enable_fault_injection=True),
    )

    @app.get("/items/{item_id}")
    async def item(item_id: str) -> dict[str, str]:
        return {"item_id": item_id}

    return app


def request_samples() -> dict[tuple[str, str], float]:
    samples: dict[tuple[str, str], float] = {}
    for metric in REGISTRY.collect():
        if metric.name != "http_server_requests":
            continue
        for sample in metric.samples:
            if sample.name.endswith("_total") and sample.labels["service"] == SERVICE:
                key = (sample.labels["route"], sample.labels["status"])
                samples[key] = samples.get(key, 0.0) + sample.value
    return samples


def duration_routes() -> set[str]:
    return {
        sample.labels["route"]
        for metric in REGISTRY.collect()
        if metric.name == "http_server_request_duration_seconds"
        for sample in metric.samples
        if sample.labels.get("service") == SERVICE
    }


def test_path_parameters_and_unknown_paths_do_not_create_new_series() -> None:
    before = request_samples()
    with TestClient(build_app()) as client:
        for item_id in ("1", "2", "abc", "f47ac10b-58cc-4372-a567-0e02b2c3d479"):
            assert client.get(f"/items/{item_id}").status_code == 200
        for probe in ("/wp-login.php", "/.env", "/items/1/extra"):
            assert client.get(probe).status_code == 404
    after = request_samples()

    new_routes = {route for route, _ in after} - {route for route, _ in before}
    assert new_routes <= {"/items/{item_id}", UNMATCHED_ROUTE}
    assert not any(route.startswith(("/wp-", "/.env", "/items/1")) for route, _ in after)
    assert after[("/items/{item_id}", "200")] - before.get(("/items/{item_id}", "200"), 0) == 4
    assert after[(UNMATCHED_ROUTE, "404")] - before.get((UNMATCHED_ROUTE, "404"), 0) == 3
    assert "/items/{item_id}" in duration_routes()
    assert not any(route.startswith("/items/") and "{" not in route for route in duration_routes())


def test_injected_faults_are_labelled_with_the_route_template() -> None:
    before = request_samples()
    with TestClient(build_app()) as client:
        assert (
            client.put("/internal/faults", json={"latency_ms": 0, "error_rate": 1}).status_code
            == 200
        )
        response = client.get("/items/42", headers={"x-request-id": "always-fail"})
        assert response.status_code == 503
        assert client.delete("/internal/faults").status_code == 200
    after = request_samples()
    assert after[("/items/{item_id}", "503")] - before.get(("/items/{item_id}", "503"), 0) == 1
    assert ("/items/42", "503") not in after
