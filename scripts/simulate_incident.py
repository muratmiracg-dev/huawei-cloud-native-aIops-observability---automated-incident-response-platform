#!/usr/bin/env python3
import json
from pathlib import Path

from aiops.anomaly_detection import HybridAnomalyDetector
from aiops.incident_response import AuditWriter, IncidentOrchestrator
from aiops.models import Incident, MetricSeries, Severity, Signal
from aiops.root_cause import RootCauseEngine


def main() -> None:
    series = [
        MetricSeries(
            service="orders-api",
            metric="cpu_utilization",
            values=[0.31, 0.34, 0.32, 0.33, 0.36, 0.35, 0.37, 0.34, 0.36, 0.38, 0.35, 0.96],
        ),
        MetricSeries(
            service="orders-api",
            metric="request_latency_p95",
            values=[0.18, 0.20, 0.19, 0.21, 0.20, 0.22, 0.21, 0.19, 0.23, 0.21, 0.22, 1.48],
        ),
    ]
    detector = HybridAnomalyDetector()
    anomalies = detector.detect_many(series)
    signals = [
        Signal(
            service=item.service,
            metric=item.metric,
            value=item.observed,
            anomaly_score=item.combined_score,
        )
        for item in anomalies
    ]
    hypotheses = RootCauseEngine().rank(signals)
    incident = Incident(
        incident_id="INC-DEMO-001",
        title="Orders API saturation detected",
        severity=Severity.CRITICAL,
        affected_services=["orders-api"],
        hypotheses=hypotheses,
    )
    audit_path = Path("artifacts/runtime/incident-audit.jsonl")
    decision, outcome = IncidentOrchestrator(
        mode="dry-run",
        cooldown_seconds=300,
        audit_writer=AuditWriter(audit_path),
    ).handle(incident)
    print(
        json.dumps(
            {
                "anomalies": [item.model_dump(mode="json") for item in anomalies],
                "incident": incident.model_dump(mode="json"),
                "decision": decision.model_dump(mode="json"),
                "outcome": outcome,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
