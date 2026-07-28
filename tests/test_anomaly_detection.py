import math

import pytest

from aiops.anomaly_detection import DetectorConfig, HybridAnomalyDetector
from aiops.models import MetricSeries, Severity


def test_stable_series_is_not_anomalous() -> None:
    detector = HybridAnomalyDetector()
    result = detector.detect(
        MetricSeries(
            service="orders-api",
            metric="error_rate",
            values=[0.01] * 12,
        )
    )
    assert result.severity is Severity.INFO
    assert result.anomalous is False
    assert result.combined_score < 0.55


def test_extreme_value_is_critical_and_explainable() -> None:
    detector = HybridAnomalyDetector()
    result = detector.detect(
        MetricSeries(
            service="orders-api",
            metric="request_latency_p95",
            values=[0.19, 0.2, 0.18, 0.21, 0.2, 0.22, 0.19, 0.2, 0.21, 0.2, 0.19, 2.4],
        )
    )
    assert result.severity is Severity.CRITICAL
    assert result.anomalous is True
    assert result.combined_score >= 0.78
    assert "robust deviations" in result.explanation


def test_detector_rejects_non_finite_values() -> None:
    detector = HybridAnomalyDetector()
    with pytest.raises(ValueError, match="finite"):
        detector.detect(
            MetricSeries(
                service="orders-api",
                metric="cpu",
                values=[0.1] * 11 + [math.inf],
            )
        )


def test_custom_threshold_changes_severity() -> None:
    detector = HybridAnomalyDetector(
        DetectorConfig(warning_threshold=0.05, critical_threshold=0.99)
    )
    result = detector.detect(
        MetricSeries(
            service="catalog-api",
            metric="latency",
            values=[1.0, 1.1, 0.9, 1.0, 1.05, 0.95, 1.0, 1.02, 0.98, 1.0, 1.0, 1.2],
        )
    )
    assert result.severity in {Severity.WARNING, Severity.CRITICAL}
