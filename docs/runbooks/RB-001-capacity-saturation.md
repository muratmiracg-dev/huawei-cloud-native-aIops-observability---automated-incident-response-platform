# RB-001 - Capacity Saturation

**Owner:** Platform SRE
**Default automation:** Scale one replica, maximum 12
**Risk:** Medium

## Trigger

- p95 request latency exceeds 750 ms for 10 minutes.
- CPU utilization and latency anomaly scores both exceed 0.78.
- Availability error-budget burn rate is above the fast-burn threshold.

## Diagnosis

1. Confirm the affected deployment and compare request rate, CPU, throttling, and
   replica availability.
2. Inspect recent deployments and configuration changes.
3. Check downstream latency before attributing the incident to local capacity.
4. Verify HPA status, pending pods, CCE node pressure, and quota availability.

## Automated action

The AIOps policy may increase the affected deployment by one replica when:

- root-cause confidence is at least 0.78;
- automation mode is `active`;
- the target is allow-listed;
- the cooldown has expired;
- the action remains below the 12-replica hard limit.

Every decision is recorded in the automation audit stream.

## Verification

- Replica readiness reaches 100%.
- p95 latency returns below 750 ms.
- Error rate remains below 1%.
- The 5-minute SLO burn rate falls below 1.

## Rollback

Return to the previous replica count only after traffic and latency are stable
for at least 15 minutes. If scaling does not improve latency, investigate
downstream or database saturation and stop further automated scale actions.

## Escalation

Escalate to the platform owner if CCE has insufficient node capacity, scale-out
fails twice, or the error budget continues to burn for more than 15 minutes.
