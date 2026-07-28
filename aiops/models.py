from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricSeries(BaseModel):
    service: str
    metric: str
    values: list[float] = Field(min_length=12)
    timestamps: list[datetime] | None = None


class Anomaly(BaseModel):
    service: str
    metric: str
    observed: float
    baseline: float
    robust_z_score: float
    isolation_score: float
    combined_score: float = Field(ge=0.0, le=1.0)
    severity: Severity
    anomalous: bool
    explanation: str


class Signal(BaseModel):
    service: str
    metric: str
    value: float
    anomaly_score: float = Field(ge=0.0, le=1.0)


class RootCauseHypothesis(BaseModel):
    rank: int
    cause: str
    affected_service: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    recommended_runbook: str


class Incident(BaseModel):
    incident_id: str
    title: str
    severity: Severity
    affected_services: list[str]
    hypotheses: list[RootCauseHypothesis]
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = "open"


class AutomationDecision(BaseModel):
    incident_id: str
    action: str
    target: str
    mode: str
    approved: bool
    reason: str
    risk: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
