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


class RootCauseEngine:
    def __init__(self, rules: tuple[Rule, ...] = DEFAULT_RULES) -> None:
        self.rules = rules

    def rank(self, signals: list[Signal], limit: int = 3) -> list[RootCauseHypothesis]:
        by_service: dict[str, dict[str, Signal]] = {}
        for signal in signals:
            by_service.setdefault(signal.service, {})[signal.metric] = signal

        candidates: list[tuple[float, Rule, list[str]]] = []
        for rule in self.rules:
            available = by_service.get(rule.service, {})
            matching = [available[name] for name in rule.required_metrics if name in available]
            if len(matching) != len(rule.required_metrics):
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
