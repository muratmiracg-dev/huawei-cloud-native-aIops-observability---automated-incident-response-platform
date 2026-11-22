import math
from dataclasses import dataclass

from aiops.models import RootCauseHypothesis, Signal


@dataclass(frozen=True)
class Rule:
    cause: str
    service: str
    required_metrics: tuple[str, ...]
    runbook: str
    base_confidence: float


DEFAULT_RULES = (
    Rule(
        cause="CPU saturation and insufficient replica capacity",
        service="orders-api",
        required_metrics=("cpu_utilization", "request_latency_p95"),
        runbook="RB-001-capacity-saturation",
        base_confidence=0.72,
    ),
    Rule(
        cause="Catalog dependency degradation",
        service="catalog-api",
        required_metrics=("error_rate", "request_latency_p95"),
        runbook="RB-002-downstream-dependency",
        base_confidence=0.76,
    ),
    Rule(
        cause="Payment provider failure",
        service="payments-api",
        required_metrics=("error_rate", "dependency_failures"),
        runbook="RB-003-payment-degradation",
        base_confidence=0.79,
    ),
    Rule(
        cause="Crash-loop or unstable application release",
        service="orders-api",
        required_metrics=("container_restarts", "error_rate"),
        runbook="RB-004-crash-loop",
        base_confidence=0.82,
    ),
    Rule(
        cause="Database connection pool exhaustion",
        service="orders-api",
        required_metrics=("db_pool_utilization", "request_latency_p95"),
        runbook="RB-005-database-saturation",
        base_confidence=0.78,
    ),
)


# A metric only counts as evidence when it is itself anomalous. The default matches the
# detector's warning threshold, so a hypothesis needs every required signal to be at least
# a warning-level anomaly.
DEFAULT_MIN_EVIDENCE_SCORE = 0.55


class RootCauseEngine:
    def __init__(
        self,
        rules: tuple[Rule, ...] = DEFAULT_RULES,
        min_evidence_score: float = DEFAULT_MIN_EVIDENCE_SCORE,
    ) -> None:
        if (
            isinstance(min_evidence_score, bool)
            or not isinstance(min_evidence_score, int | float)
            or not math.isfinite(min_evidence_score)
            or not 0 < min_evidence_score <= 1
        ):
            raise ValueError("min_evidence_score must be a number in (0, 1]")
        self.rules = rules
        self.min_evidence_score = float(min_evidence_score)

    def rank(self, signals: list[Signal], limit: int = 3) -> list[RootCauseHypothesis]:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer")
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        by_service: dict[str, dict[str, Signal]] = {}
        for signal in signals:
            by_service.setdefault(signal.service, {})[signal.metric] = signal

        candidates: list[tuple[float, Rule, list[str]]] = []
        for rule in self.rules:
            available = by_service.get(rule.service, {})
            matching = [available[name] for name in rule.required_metrics if name in available]
            if len(matching) != len(rule.required_metrics):
                continue
            # Presence is not evidence: a healthy metric (score near 0) must not support a
            # cause, otherwise base confidence alone can clear an automation threshold.
            if any(item.anomaly_score < self.min_evidence_score for item in matching):
                continue
            mean_score = sum(item.anomaly_score for item in matching) / len(matching)
            confidence = min(rule.base_confidence + 0.2 * mean_score, 0.99)
            evidence = [
                f"{item.metric}={item.value:.3f}, anomaly={item.anomaly_score:.2f}"
                for item in matching
            ]
            candidates.append((confidence, rule, evidence))

        candidates.sort(key=lambda item: item[0], reverse=True)
        return [
            RootCauseHypothesis(
                rank=index,
                cause=rule.cause,
                affected_service=rule.service,
                confidence=round(confidence, 3),
                evidence=evidence,
                recommended_runbook=rule.runbook,
            )
            for index, (confidence, rule, evidence) in enumerate(
                candidates[:limit],
                start=1,
            )
        ]
