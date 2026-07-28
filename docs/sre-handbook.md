# SRE Handbook

## Reliability principles

1. Define customer-facing SLIs before adding alerts.
2. Alert on sustained user impact or error-budget risk.
3. Prefer reversible, bounded automation.
4. Keep high-risk remediation human approved.
5. Connect every actionable alert to an owned runbook.
6. Record decisions, outcomes, and post-incident learning.

## Incident severity

| Severity | Definition | Initial response |
|---|---|---|
| SEV-1 | Multi-service outage, integrity risk, or severe customer impact | Immediate incident command |
| SEV-2 | Major degradation or fast SLO burn with workaround | Respond within 15 minutes |
| SEV-3 | Limited degradation or slow SLO burn | Respond within business SLA |
| SEV-4 | Informational anomaly without material impact | Review and tune |

## Incident roles

- **Incident commander:** owns priorities, decisions, and escalation.
- **Operations lead:** executes diagnosis and recovery.
- **Communications lead:** maintains stakeholder updates.
- **Scribe:** records timeline, evidence, and actions.

Small teams may combine roles but should preserve their responsibilities.

## Change policy

- immutable images in SWR;
- reviewed Helm values and Terraform plans;
- deployment health checks;
- atomic upgrade and rollback;
- change annotation in traces and dashboards;
- no active automation without dry-run evidence.

## Postmortem standard

A blameless postmortem includes impact, detection, timeline, contributing
factors, response effectiveness, root cause, corrective actions, owners, and
deadlines. “Human error” is not a sufficient root cause.
