# Changelog

All notable changes are documented in this file.

## [Unreleased]

### Fixed

- `AvailabilitySLOBurnRateFast` and `AvailabilitySLOBurnRateSlow` hard-coded a 0.1% (99.9%)
  error budget for every service. `payments-api` has a 99.5% target in the SLO catalog, so its
  alerts fired at one fifth of the intended burn rate (1.44% instead of 7.2% 5xx for fast burn).
  Each service now has a `slo:availability_error_budget:ratio` recording rule, and both alerts
  compare against it. `promtool` unit tests (`observability/prometheus/alerts.test.yml`) and a
  catalog-consistency test cover this, and CI now runs `promtool check rules` and `test rules`.
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
