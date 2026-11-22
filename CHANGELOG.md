# Changelog

All notable changes are documented in this file.

## [Unreleased]

### Fixed

- Root-cause rules matched as soon as their metrics were present, whatever their anomaly
  scores, and confidence was the rule prior plus 0.2 x the mean score. Signals supplied to
  `POST /v1/analyze` with healthy catalog metrics (scores 0) therefore produced "Catalog
  dependency degradation" at 0.76, exactly the circuit-breaker threshold, and the low-risk
  action was approved, also in active mode. Every required signal must now reach an evidence
  threshold (default 0.55, the detector's warning threshold; `RootCauseEngine(min_evidence_score=...)`).
- Closing an incident that was already closed decremented `aiops_active_incidents` again, so a
  retried or duplicate `POST /v1/incidents/{id}/close` drove the gauge below the real number of
  open incidents (to negative values in the regression test) and the Grafana *Active incidents*
  panels undercounted. Closing is now idempotent and only the open-to-closed transition
  releases the gauge.
- `scripts/validate_repository.py` now verifies `CHECKSUMS.sha256`, which the README publishes but
  no check enforced.
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
