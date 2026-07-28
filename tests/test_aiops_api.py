from fastapi.testclient import TestClient

from aiops.api import app


def test_analyze_stable_series_returns_no_incident() -> None:
    payload = {
        "series": [
            {
                "service": "orders-api",
                "metric": "error_rate",
                "values": [0.01] * 12,
            }
        ]
    }
    with TestClient(app) as client:
        response = client.post("/v1/analyze", json=payload)
        assert response.status_code == 200
        assert response.json()["incident"] is None


def test_analyze_incident_and_close_lifecycle() -> None:
    payload = {
        "series": [
            {
                "service": "orders-api",
                "metric": "cpu_utilization",
                "values": [0.3, 0.32, 0.31, 0.33, 0.3, 0.34, 0.32, 0.31, 0.33, 0.3, 0.32, 0.98],
            },
            {
                "service": "orders-api",
                "metric": "request_latency_p95",
                "values": [0.2, 0.21, 0.19, 0.22, 0.2, 0.21, 0.2, 0.19, 0.22, 0.2, 0.21, 1.8],
            },
        ],
        "signals": [
            {
                "service": "orders-api",
                "metric": "cpu_utilization",
                "value": 0.98,
                "anomaly_score": 0.95,
            },
            {
                "service": "orders-api",
                "metric": "request_latency_p95",
                "value": 1.8,
                "anomaly_score": 0.94,
            },
        ],
    }
    with TestClient(app) as client:
        response = client.post("/v1/analyze", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["incident"]["severity"] == "critical"
        assert body["automation"]["action"] == "scale"
        incident_id = body["incident"]["incident_id"]
        listing = client.get("/v1/incidents")
        assert any(item["incident_id"] == incident_id for item in listing.json())
        closed = client.post(f"/v1/incidents/{incident_id}/close")
        assert closed.status_code == 200
        assert closed.json()["status"] == "closed"
        assert client.post("/v1/incidents/INC-NOT-FOUND/close").status_code == 404
