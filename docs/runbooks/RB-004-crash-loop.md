# RB-004 - Crash Loop or Unstable Release

**Owner:** Platform SRE
**Default automation:** Recommendation only; rollback requires approval
**Risk:** High

## Trigger

- Container restart count rises with application error rate.
- Readiness repeatedly fails after a deployment.
- A new release correlates with availability loss.

## Diagnosis

1. Review Kubernetes events and previous container logs in LTS.
2. Compare image digest, ConfigMap revision, and deployment history.
3. Check memory limits, OOM events, startup dependencies, and probe timing.
4. Reproduce the failure with the same immutable image digest.

## Automated action

The policy engine can recommend `rollback`, but active automation blocks this
high-risk action. A human must confirm the affected deployment, known-good
revision, data compatibility, and rollback plan.

## Verification

- Desired and ready replicas match.
- Restarts remain flat for 15 minutes.
- Availability and latency recover.
- No migration or schema inconsistency is present.

## Rollback

Use an atomic Helm rollback to the last verified release. Confirm configuration
and image digests, then document the failed revision and evidence.

## Escalation

Escalate immediately when the failure affects persistent data, multiple services,
or all replicas, or when no verified rollback revision exists.
