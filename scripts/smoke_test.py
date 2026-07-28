#!/usr/bin/env python3
import json
import sys

import httpx


def require_ok(client: httpx.Client, url: str) -> dict[str, object]:
    response = client.get(url)
    response.raise_for_status()
    return response.json()


def main() -> int:
    endpoints = {
        "catalog-api": "http://localhost:8001",
        "orders-api": "http://localhost:8002",
        "payments-api": "http://localhost:8003",
        "aiops-api": "http://localhost:8004",
    }
    results: dict[str, object] = {}
    with httpx.Client(timeout=5.0) as client:
        for service, base_url in endpoints.items():
            results[service] = require_ok(client, f"{base_url}/health/ready")
        products = require_ok(client, f"{endpoints['catalog-api']}/products")
        results["catalog_count"] = len(products)
        metrics = client.get(f"{endpoints['aiops-api']}/metrics")
        metrics.raise_for_status()
        results["metrics_exposed"] = "http_server_requests_total" in metrics.text
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
