# RB-005 - Database Connection Pool Saturation

**Owner:** Data Platform SRE
**Default automation:** Scale application within limits
**Risk:** Medium

## Trigger

- Connection-pool utilization and request latency anomaly scores are elevated.
- Connection timeouts or queue depth increase.
- Database latency rises without equivalent CPU saturation in the API.

## Diagnosis

1. Inspect pool usage, wait time, query latency, transaction duration, and locks.
2. Check whether a traffic surge or release changed query volume.
3. Identify slow or unbounded queries.
4. Verify database connections are closed and retry behavior is bounded.

## Automated action

Policy may add one API replica when confidence exceeds 0.82 and cooldown permits.
This is a containment action, not a database fix; further scaling is blocked if
pool pressure or query latency does not improve.

## Verification

- Pool wait time and request latency decrease.
- Active connections stay within the database limit.
- Transaction errors and timeouts stop increasing.

## Rollback

Return replica count to baseline after query and pool behavior stabilize. Revert
any query or pool configuration change that introduced the incident.

## Escalation

Escalate when database limits are reached, lock contention affects writes, data
integrity is uncertain, or the issue persists after one containment action.
