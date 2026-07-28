# Security Threat Model

## Assets

- service availability and integrity;
- incident and telemetry data;
- CCE control-plane access;
- SWR image integrity;
- automation service-account token;
- configuration and deployment history.

## Trust boundaries

1. client to workload APIs;
2. workload to workload;
3. workload to telemetry plane;
4. AIOps control plane to CCE API;
5. CI to SWR and deployment environment;
6. operators to dashboards and cloud consoles.

## Key threats and controls

| Threat | Control |
|---|---|
| Malicious image | Private SWR, immutable tags/digests, Trivy, CodeQL, SBOM |
| Secret leakage | No committed secrets, external injection, restricted logs |
| Lateral movement | Default-deny NetworkPolicy, non-root, no privilege escalation |
| Automation abuse | Namespace RBAC, action allow-list, confidence/risk gates, cooldown |
| Destructive rollback | High-risk action blocked pending human approval |
| Alert poisoning | Multi-signal evidence, bounded labels, audit trail |
| Supply-chain compromise | Pinned dependencies, Dependabot, least-privilege workflows |
| Telemetry data exposure | Private transport, retention, access control, no payload logging |

## Residual risk

This reference implementation does not provide an identity-aware external API
gateway, production secrets manager, managed database, cross-region disaster
recovery, or organizational SOC integration. Those controls belong to the
target environment and must be designed before production use.
