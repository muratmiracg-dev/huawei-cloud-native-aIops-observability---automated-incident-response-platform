# RB-003 - Payment Service Degradation

**Owner:** Payments SRE
**Default automation:** Enable degraded order mode
**Risk:** Medium

## Trigger

- Payment service error rate and dependency failures exceed anomaly thresholds.
- Payment-related order failures rise above 2%.
- Payment provider latency breaches 750 ms for 10 minutes.

## Diagnosis

1. Separate intentional payment declines from 5xx and transport failures.
2. Inspect traces between Orders API and Payments API.
3. Confirm token validation, provider reachability, TLS, DNS, and quotas.
4. Check whether retries are idempotent and bounded.

## Automated action

With confidence at or above 0.82, active mode may set
`PAYMENTS_DEGRADED_MODE=true` on Orders API. The expected business behavior is to
stop synchronous retry amplification and queue eligible orders for later review.

## Verification

- Payment transport failures stop increasing.
- Orders remain traceable and idempotent.
- No order is marked paid without a confirmed payment identifier.
- Alert severity and SLO burn rate decrease.

## Rollback

Remove degraded mode after payment success and latency remain within SLO for 20
minutes. Reconcile deferred orders before normal retry behavior resumes.

## Escalation

Immediately escalate suspected duplicate charges, inconsistent payment state,
credential exposure, or reconciliation mismatch to the incident commander.
