# ADR-002 - Dry-Run Automation by Default

**Status:** Accepted
**Date:** 2026-07-27

## Context

Incorrect remediation can amplify an incident. Portfolio and non-production
environments may not have complete topology, quota, or rollback information.

## Decision

All environments default to `dry-run`. Active mode requires an explicit
configuration change after operational review.

## Consequences

Teams can measure recommendations before granting mutation rights. Activation
requires a deliberate change and evidence.
