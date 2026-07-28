# ADR-004 - OpenTelemetry for Portable Instrumentation

**Status:** Accepted
**Date:** 2026-07-27

## Context

The project needs local observability and a Huawei Cloud deployment path without
coupling application code to a single trace backend.

## Decision

Instrument FastAPI and HTTPX with OpenTelemetry and route OTLP through a
collector. Use Prometheus/Tempo locally and document AOM/LTS integration for
Huawei Cloud.

## Consequences

Telemetry remains portable and centrally enriched. Production exporters,
sampling, retention, and access control remain environment-specific.
