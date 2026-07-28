# RB-006 - Service Unavailable

**Owner:** Platform SRE
**Default automation:** Notify and diagnose
**Risk:** High

## Trigger

- Prometheus `up` equals zero for two minutes.
- All replicas are unready.
- CCE reports scheduling, image-pull, or node failure events.

## Diagnosis

1. Confirm whether the problem affects one service, namespace, node pool, or CCE.
2. Inspect deployment conditions, pods, events, SWR image access, and DNS.
3. Review AOM metrics, LTS logs, and recent releases.
4. Validate network policies and upstream/downstream health.

## Automated action

No destructive recovery is executed automatically. The platform creates an
incident, ranks available evidence, links this runbook, and notifies operators.

## Verification

- At least the minimum healthy replica count is ready.
- Health probes and Prometheus targets succeed.
- Business transactions complete end to end.
- SLO burn rate has returned below threshold.

## Rollback

Use the service-specific last known-good Helm revision if the outage correlates
with a deployment. Do not bypass security controls to restore availability.

## Escalation

Declare a major incident when multiple services or the CCE control plane are
affected, customer impact exceeds 15 minutes, or recovery needs elevated access.
