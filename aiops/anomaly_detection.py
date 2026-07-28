from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

from aiops.models import Anomaly, MetricSeries, Severity
from platform_core.metrics import ANOMALY_SCORE


@dataclass(frozen=True)
class DetectorConfig:
    warning_threshold: float = 0.55
    critical_threshold: float = 0.78
    contamination: float = 0.1
    random_state: int = 42


class HybridAnomalyDetector:
    """Combines robust statistics with Isolation Forest for explainable detection."""

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.config = config or DetectorConfig()

    @staticmethod
    def _robust_score(values: np.ndarray) -> tuple[float, float, float]:
        history = values[:-1]
        observed = float(values[-1])
        baseline = float(np.median(history))
        mad = float(np.median(np.abs(history - baseline)))
        scale = max(1.4826 * mad, float(np.std(history)) * 0.25, 1e-9)
        robust_z = (observed - baseline) / scale
        normalized = min(abs(robust_z) / 6.0, 1.0)
        return baseline, robust_z, normalized

    def _isolation_score(self, values: np.ndarray) -> float:
        differences = np.diff(values, prepend=values[0])
        features = np.column_stack((values, differences))
        history = features[:-1]
        model = IsolationForest(
            n_estimators=150,
            contamination=self.config.contamination,
            random_state=self.config.random_state,
        )
        model.fit(history)
        history_raw = -model.score_samples(history)
        observed_raw = float(-model.score_samples(features[-1:])[0])
        low = float(np.percentile(history_raw, 10))
        high = float(np.percentile(history_raw, 95))
        return float(np.clip((observed_raw - low) / max(high - low, 1e-9), 0.0, 1.0))

    def detect(self, series: MetricSeries) -> Anomaly:
        values = np.asarray(series.values, dtype=float)
        if not np.all(np.isfinite(values)):
            raise ValueError("metric values must be finite")

        baseline, robust_z, robust_score = self._robust_score(values)
        isolation_score = self._isolation_score(values)
        combined = float(np.clip(0.65 * robust_score + 0.35 * isolation_score, 0, 1))

        if combined >= self.config.critical_threshold:
            severity = Severity.CRITICAL
        elif combined >= self.config.warning_threshold:
            severity = Severity.WARNING
        else:
            severity = Severity.INFO

        anomalous = severity is not Severity.INFO
        direction = "above" if values[-1] >= baseline else "below"
        explanation = (
            f"Latest value is {abs(robust_z):.2f} robust deviations {direction} "
            f"the historical median; isolation score={isolation_score:.2f}."
        )
        ANOMALY_SCORE.labels(service=series.service, metric=series.metric).set(combined)
        return Anomaly(
            service=series.service,
            metric=series.metric,
            observed=float(values[-1]),
            baseline=baseline,
            robust_z_score=round(float(robust_z), 4),
            isolation_score=round(isolation_score, 4),
            combined_score=round(combined, 4),
            severity=severity,
            anomalous=anomalous,
            explanation=explanation,
        )

    def detect_many(self, series: list[MetricSeries]) -> list[Anomaly]:
        return [self.detect(item) for item in series]
