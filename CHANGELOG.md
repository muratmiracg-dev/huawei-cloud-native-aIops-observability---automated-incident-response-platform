# Changelog

All notable changes are documented in this file.

## [Unreleased]

### Fixed

- HTTP request and latency metrics used the raw URL path as the `route` label, creating one
  Prometheus series per id (`/products/SKU-1`, `/orders/<uuid>`) and per scanner probe
  (`/.env`, `/wp-login.php`). They now use the matched route template (`/products/{sku}`), and
  requests that match no route share `route="unmatched"`. Synthetic-fault 503s are labelled with
  their template too.

## [1.0.0] - 2026-07-27

### Added

- Four observable FastAPI services for catalog, orders, payments, and AIOps.
- OpenTelemetry, Prometheus, Grafana, AOM, and LTS integration assets.
- Hybrid statistical and Isolation Forest anomaly detection.
- Explainable root-cause ranking and policy-guarded incident automation.
- Docker Compose, Kubernetes, Helm, and Huawei Cloud Terraform delivery paths.
- SLOs, alert rules, runbooks, threat model, ADRs, tests, and CI security gates.
- Turkish and English executive presentations and a vector-HD portfolio report.
