# Observability Guide

## Golden signals

The platform instruments traffic, errors, duration, saturation proxies,
dependency outcomes, business outcomes, incidents, anomaly scores, and
automation actions.

### Core metrics

| Metric | Type | Key labels | Purpose |
|---|---|---|---|
| `http_server_requests_total` | Counter | service, method, route, status | Traffic and availability |
| `http_server_request_duration_seconds` | Histogram | service, method, route | Latency SLI |
| `dependency_requests_total` | Counter | service, dependency, operation, outcome | Dependency reliability |
| `business_events_total` | Counter | service, event, outcome | Business impact |
| `aiops_anomaly_score` | Gauge | service, metric | Detection intelligence |
| `aiops_active_incidents` | Gauge | severity | Incident load |
| `aiops_automation_actions_total` | Counter | action, mode, outcome | Automation governance |

## Logs

Application logs are structured JSON and include severity, logger, message, and
request ID. In Huawei Cloud:

1. install CCE Cloud Native Log Collection;
2. define collection rules for container standard output;
3. route application logs to LTS;
4. apply retention and access controls;
5. avoid sensitive payloads and payment tokens.

## Traces

FastAPI and outbound HTTP clients are instrumented with OpenTelemetry. Resource
attributes identify service, version, namespace, environment, and cloud
provider. Local traces flow to Tempo; Huawei Cloud deployments can route the
collector to an approved APM/AOM-compatible destination.

## Dashboards

- **Executive Overview:** availability, latency, incidents, risk, traffic,
  errors, and anomaly intelligence.
- **SLO & Error Budget:** burn rate, latency SLO, active alerts, and service
  error-budget behavior.
- **Incident Intelligence:** incident load, anomaly timeline, automation
  outcomes, dependency health, and business impact.

## Cardinality controls

Routes use normalized paths where possible. Never label metrics with customer
IDs, order IDs, request IDs, tokens, free text, or unbounded exception messages.
