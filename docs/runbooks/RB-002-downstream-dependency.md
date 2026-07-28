# RB-002 - Downstream Dependency Degradation

**Owner:** Application SRE
**Default automation:** Enable catalog circuit breaker
**Risk:** Low

## Trigger

- Catalog error rate exceeds 5% for five minutes.
- Catalog p95 latency and error-rate anomaly scores are simultaneously elevated.
- Orders API dependency failures rise while local CPU remains healthy.

## Diagnosis

1. Compare Orders API and Catalog API traces for the same request IDs.
2. Check catalog pod health, recent releases, HPA state, and CCE node events.
3. Validate whether the failure is isolated to a product, route, or all traffic.
4. Confirm that retries are not amplifying load.

## Automated action

When policy confidence is at least 0.76, the active executor may set
`CATALOG_CIRCUIT_BREAKER=true` on Orders API. This triggers a controlled rollout
and prevents retry amplification. Dry-run remains the default repository mode.

## Verification

- Orders API thread and connection utilization stabilize.
- Dependency failure rate decreases.
- Graceful errors replace timeouts.
- Trace duration falls and no retry storm is visible.

## Rollback

Remove `CATALOG_CIRCUIT_BREAKER` after catalog health has remained stable for 15
minutes. Monitor the first 10 minutes after the rollout for renewed saturation.

## Escalation

Escalate when catalog availability remains below its SLO, circuit-breaker rollout
fails, or a customer-impacting product integrity issue is suspected.
