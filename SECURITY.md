# Security Policy

## Reporting

Do not open a public issue for a suspected vulnerability. Contact the repository
owner privately with the affected component, reproduction steps, impact, and any
suggested mitigation.

## Security posture

- Workloads run as non-root with read-only root filesystems.
- Secrets are referenced externally and are never committed.
- NetworkPolicy limits east-west traffic.
- Incident automation defaults to `dry-run` and applies policy guardrails.
- CI performs dependency, secret, filesystem, IaC, and static-code analysis.
- GitHub workflow permissions follow least privilege.

This repository is a portfolio reference implementation. Review all settings,
regional service availability, quotas, and organizational controls before a
production deployment.
