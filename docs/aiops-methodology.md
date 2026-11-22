# AIOps Methodology

## Detection model

The detector combines two complementary signals:

- **Robust deviation:** historical median and median absolute deviation provide
  an explainable baseline that is resistant to outliers.
- **Isolation Forest:** value and first-difference features capture unusual
  level and rate-of-change behavior without requiring labeled incidents.

The normalized score is:

```text
combined_score = 0.65 * robust_score + 0.35 * isolation_score
```

Default severity thresholds are 0.55 for warning and 0.78 for critical. These
values are reference defaults, not universal production thresholds.

## Root-cause ranking

An anomaly is not treated as proof of cause. The root-cause engine requires
multiple correlated signals for each hypothesis. Examples:

| Hypothesis | Required evidence |
|---|---|
| Capacity saturation | CPU utilization + p95 latency |
| Catalog degradation | Catalog error rate + catalog p95 latency |
| Payment failure | Payment error rate + dependency failures |
| Crash loop | Container restarts + error rate |
| Database pool exhaustion | Pool utilization + p95 latency |

Every required signal must itself be anomalous: its anomaly score must reach the
evidence threshold (default 0.55, the detector's warning threshold). A metric that is
merely present but healthy does not support a cause. Without this, the prior alone
can clear an automation threshold: two healthy catalog metrics (scores 0) used to
give "Catalog dependency degradation" a confidence of 0.76, exactly the
circuit-breaker threshold.

Confidence combines a rule-specific prior with the mean anomaly score of the
required evidence. The API returns ranked evidence so a human can challenge the
recommendation.

## Model-risk controls

- deterministic random state;
- finite-value validation;
- minimum historical window;
- explainable baseline and evidence;
- dry-run default;
- confidence thresholds per action;
- action cooldown;
- target allow-list;
- high-risk rollback approval;
- audit record for every decision.

## Evaluation strategy

Production adoption should add:

- incident-labeled replay data;
- precision, recall, detection delay, and false-alert rate;
- threshold calibration by service and traffic regime;
- shadow-mode comparison against existing alerts;
- drift monitoring for features and incident mix;
- quarterly rule and runbook review.

The included synthetic scenario demonstrates behavior; it is not evidence of
performance on a real Huawei Cloud production workload.
