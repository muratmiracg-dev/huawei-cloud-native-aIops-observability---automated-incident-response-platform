# ADR-003 - Bounded Kubernetes RBAC

**Status:** Accepted
**Date:** 2026-07-27

## Context

The AIOps control plane needs limited deployment visibility and reversible
mutation capability but must not become a cluster administrator.

## Decision

Grant a namespace Role for get/list/watch and patch/update of deployments and
scale, plus read-only pods/events. Deny secrets, deletes, and cluster scope.

## Consequences

The blast radius is limited to the application namespace. Cross-namespace or
cluster remediation requires a separate reviewed mechanism.
