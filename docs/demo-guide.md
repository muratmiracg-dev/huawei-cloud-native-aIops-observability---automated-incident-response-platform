# Portfolio Demonstration Guide

## Five-minute story

1. Open the architecture diagram and explain the four planes.
2. Start Docker Compose and show all health endpoints.
3. Open the Executive Overview and SLO dashboards.
4. Run `python -m scripts.simulate_incident`.
5. Explain the combined anomaly score and ranked evidence.
6. Show that automation is dry-run by default.
7. Open the capacity runbook and Kubernetes RBAC.
8. Close with Terraform, Helm, CI, and Huawei Cloud mapping.

## Interview talking points

- Why robust statistics and Isolation Forest are combined.
- Why anomaly does not equal root cause.
- Why rollback is human approved.
- How error budgets improve alert quality.
- How AOM/LTS complement open observability components.
- How CCE RBAC and NetworkPolicy constrain blast radius.
- Which elements were locally validated and which require an authorized cloud
  account to deploy.

## Suggested screenshots

- `images/executive-overview.png`
- `images/slo-error-budget.png`
- `images/incident-intelligence.png`
- `images/architecture.png`
