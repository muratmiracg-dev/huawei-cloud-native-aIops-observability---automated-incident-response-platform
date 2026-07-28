from aiops.models import Signal
from aiops.root_cause import RootCauseEngine


def test_root_cause_ranking_uses_correlated_signals() -> None:
    hypotheses = RootCauseEngine().rank(
        [
            Signal(
                service="orders-api",
                metric="cpu_utilization",
                value=0.97,
                anomaly_score=0.95,
            ),
            Signal(
                service="orders-api",
                metric="request_latency_p95",
                value=1.8,
                anomaly_score=0.91,
            ),
            Signal(
                service="orders-api",
                metric="container_restarts",
                value=0,
                anomaly_score=0.1,
            ),
        ]
    )
    assert hypotheses
    assert hypotheses[0].cause == "CPU saturation and insufficient replica capacity"
    assert hypotheses[0].rank == 1
    assert len(hypotheses[0].evidence) == 2


def test_root_cause_requires_complete_rule_evidence() -> None:
    hypotheses = RootCauseEngine().rank(
        [
            Signal(
                service="payments-api",
                metric="error_rate",
                value=0.3,
                anomaly_score=0.9,
            )
        ]
    )
    assert hypotheses == []
