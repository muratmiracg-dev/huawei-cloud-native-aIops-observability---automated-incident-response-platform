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
