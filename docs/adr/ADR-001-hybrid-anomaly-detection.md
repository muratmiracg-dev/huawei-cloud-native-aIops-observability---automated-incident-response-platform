# ADR-001 - Hybrid Anomaly Detection

**Status:** Accepted
**Date:** 2026-07-27

## Context

Single static thresholds are easy to explain but miss service-specific baselines.
Unsupervised models adapt better but can be difficult to justify operationally.

## Decision

Combine robust median-deviation scoring with Isolation Forest and return both
component scores plus a human-readable explanation.

## Consequences

The approach is deterministic, label-free, and explainable. It still requires
service-specific calibration and cannot prove causality.
