# Metrics and Alert Catalog

## Alert philosophy

Alerts should represent urgent user impact, sustained reliability risk, or a
specific operator action. Dashboard-only signals should not page operators.

| Alert | Condition | Severity | Runbook |
|---|---|---|---|
| ServiceUnavailable | Target down for 2 minutes | Critical | RB-006 |
| HighErrorRate | 5xx ratio above 5% for 5 minutes | Warning | RB-002 |
| CriticalLatency | p95 above 750 ms for 10 minutes | Critical | RB-001 |
| AvailabilitySLOBurnRateFast | Service availability budget burn above 14.4x (5m) | Critical | RB-001 |
| AvailabilitySLOBurnRateSlow | Service availability budget burn above 3x (1h) for 30 minutes | Warning | SRE handbook |
| CriticalAIOpsAnomaly | Combined score above 0.78 | Critical | Related hypothesis |
| AutomationRepeatedlyBlocked | More than 3 guardrail blocks in 15 minutes | Warning | Incident automation |

## Tuning

Review alert volume, actionable rate, acknowledged time, detection delay, and
false-positive rate monthly. Changes to thresholds require a documented reason,
comparison window, and owner.

Burn-rate alerts compare each service's 5xx ratio with its own availability error budget
(`slo:availability_error_budget:ratio` = 1 - target from
`observability/slos/service-level-objectives.yaml`): 0.1% for orders, catalog and AIOps, 0.5%
for payments. `observability/prometheus/alerts.test.yml` holds `promtool` unit tests for them.
