# Contributing

Thank you for improving the Huawei Cloud-Native AIOps platform.

## Development workflow

1. Create a focused branch from `main`.
2. Install development dependencies with `make install`.
3. Run `make format`, `make lint`, `make test-cov`, and `make validate`.
4. Keep incident automation in `dry-run` mode unless a reviewed runbook explicitly
   authorizes mutation.
5. Update relevant ADRs, runbooks, tests, and dashboards when behavior changes.

Commits should be small, descriptive, and free of credentials, customer data, or
generated runtime artifacts.

## Pull request checklist

- [ ] Tests cover the intended behavior and failure path.
- [ ] Coverage remains at or above the configured threshold.
- [ ] Kubernetes, Helm, Terraform, and dashboard files validate.
- [ ] Security scans contain no unresolved high or critical findings.
- [ ] Documentation describes operational and rollback impact.
