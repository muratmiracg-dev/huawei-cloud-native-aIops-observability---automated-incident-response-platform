import pytest

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


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_root_cause_rejects_out_of_range_limits(limit: int) -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        RootCauseEngine().rank([], limit=limit)


@pytest.mark.parametrize("limit", [True, 1.5, "3"])
def test_root_cause_rejects_non_integer_limits(limit) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        RootCauseEngine().rank([], limit=limit)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"service": " ", "metric": "error_rate", "value": 1, "anomaly_score": 0.5},
        {"service": "orders-api", "metric": " ", "value": 1, "anomaly_score": 0.5},
        {
            "service": "orders-api",
            "metric": "error_rate",
            "value": float("nan"),
            "anomaly_score": 0.5,
        },
        {
            "service": "orders-api",
            "metric": "error_rate",
            "value": 1,
            "anomaly_score": float("inf"),
        },
    ],
)
def test_signal_contract_rejects_blank_or_non_finite_values(kwargs) -> None:
    with pytest.raises(ValueError):
        Signal(**kwargs)


def _signals(service: str, metrics: tuple[str, ...], score: float) -> list[Signal]:
    return [
        Signal(service=service, metric=name, value=1.0, anomaly_score=score) for name in metrics
    ]


def test_healthy_metrics_do_not_support_a_cause() -> None:
    # All-zero anomaly scores used to yield "Catalog dependency degradation" at 0.76,
    # exactly the circuit-breaker threshold, so automation was approved on no evidence.
    healthy = _signals("catalog-api", ("error_rate", "request_latency_p95"), 0.0)
    assert RootCauseEngine().rank(healthy) == []


def test_every_required_metric_must_be_anomalous() -> None:
    signals = [
        Signal(service="catalog-api", metric="error_rate", value=0.2, anomaly_score=0.95),
        Signal(service="catalog-api", metric="request_latency_p95", value=0.3, anomaly_score=0.2),
    ]
    assert RootCauseEngine().rank(signals) == []
    assert RootCauseEngine(min_evidence_score=0.1).rank(signals)[0].cause == (
        "Catalog dependency degradation"
    )


def test_evidence_threshold_is_inclusive() -> None:
    signals = _signals("catalog-api", ("error_rate", "request_latency_p95"), 0.55)
    hypotheses = RootCauseEngine().rank(signals)
    assert [item.cause for item in hypotheses] == ["Catalog dependency degradation"]
    assert hypotheses[0].confidence == pytest.approx(0.76 + 0.2 * 0.55)


@pytest.mark.parametrize("value", [0, -0.1, 1.5, float("nan"), True, "0.5"])
def test_min_evidence_score_is_validated(value) -> None:
    with pytest.raises(ValueError, match="min_evidence_score"):
        RootCauseEngine(min_evidence_score=value)
