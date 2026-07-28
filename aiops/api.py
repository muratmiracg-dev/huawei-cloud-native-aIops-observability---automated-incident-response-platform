import uuid
from threading import Lock

from fastapi import HTTPException
from pydantic import BaseModel, Field

from aiops.anomaly_detection import HybridAnomalyDetector
from aiops.incident_response import IncidentOrchestrator
from aiops.kubernetes_executor import KubernetesExecutor
from aiops.models import (
    Anomaly,
    AutomationDecision,
    Incident,
    MetricSeries,
    Severity,
    Signal,
)
from aiops.root_cause import RootCauseEngine
from platform_core.app_factory import create_service_app
from platform_core.metrics import ACTIVE_INCIDENTS
from platform_core.settings import Settings


class AnalyzeRequest(BaseModel):
    series: list[MetricSeries] = Field(min_length=1)
    signals: list[Signal] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    anomalies: list[Anomaly]
    incident: Incident | None
    automation: AutomationDecision | None
    automation_outcome: str | None


class IncidentStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._incidents: dict[str, Incident] = {}

    def add(self, incident: Incident) -> Incident:
        with self._lock:
            self._incidents[incident.incident_id] = incident
            return incident

    def list(self) -> list[Incident]:
        with self._lock:
            return list(self._incidents.values())

    def close(self, incident_id: str) -> Incident | None:
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident:
                incident.status = "closed"
            return incident


settings = Settings(service_name="aiops-api")
detector = HybridAnomalyDetector()
root_cause_engine = RootCauseEngine()
active_executor = KubernetesExecutor() if settings.incident_automation_mode == "active" else None
orchestrator = IncidentOrchestrator(
    mode=settings.incident_automation_mode,
    cooldown_seconds=settings.incident_cooldown_seconds,
    executor=active_executor,
)
incident_store = IncidentStore()
app = create_service_app(
    title="AIOps Control Plane API",
    description=(
        "Hybrid anomaly detection, explainable root-cause ranking, SLO analysis, "
        "and policy-guarded incident automation."
    ),
    settings=settings,
)


@app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["aiops"])
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    anomalies = detector.detect_many(payload.series)
    material = [item for item in anomalies if item.anomalous]
    if not material:
        return AnalyzeResponse(
            anomalies=anomalies,
            incident=None,
            automation=None,
            automation_outcome=None,
        )

    signals = payload.signals or [
        Signal(
            service=item.service,
            metric=item.metric,
            value=item.observed,
            anomaly_score=item.combined_score,
        )
        for item in material
    ]
    hypotheses = root_cause_engine.rank(signals)
    severity = (
        Severity.CRITICAL
        if any(item.severity is Severity.CRITICAL for item in material)
        else Severity.WARNING
    )
    incident = incident_store.add(
        Incident(
            incident_id=f"INC-{uuid.uuid4().hex[:10].upper()}",
            title=f"{severity.value.title()} anomaly across {len(material)} signal(s)",
            severity=severity,
            affected_services=sorted({item.service for item in material}),
            hypotheses=hypotheses,
        )
    )
    ACTIVE_INCIDENTS.labels(severity=severity.value).inc()
    decision, outcome = orchestrator.handle(incident)
    return AnalyzeResponse(
        anomalies=anomalies,
        incident=incident,
        automation=decision,
        automation_outcome=outcome,
    )


@app.get("/v1/incidents", response_model=list[Incident], tags=["incidents"])
async def list_incidents() -> list[Incident]:
    return incident_store.list()


@app.post("/v1/incidents/{incident_id}/close", response_model=Incident, tags=["incidents"])
async def close_incident(incident_id: str) -> Incident:
    incident = incident_store.close(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")
    ACTIVE_INCIDENTS.labels(severity=incident.severity.value).dec()
    return incident
