"""Burn-rate alerts must use each service's error budget from the SLO catalog."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RULES = yaml.safe_load((ROOT / "observability/prometheus/alerts.yml").read_text(encoding="utf-8"))
CATALOG = yaml.safe_load(
    (ROOT / "observability/slos/service-level-objectives.yaml").read_text(encoding="utf-8")
)
BUDGET_RECORD = "slo:availability_error_budget:ratio"


def all_rules() -> list[dict]:
    return [rule for group in RULES["groups"] for rule in group["rules"]]


def catalog_budgets() -> dict[str, float]:
    budgets = {}
    for service in CATALOG["spec"]["services"]:
        for objective in service["objectives"]:
            if objective["name"] == "availability":
                budgets[service["name"]] = round(1 - float(objective["target"]), 6)
    return budgets


def rule_budgets() -> dict[str, float]:
    budgets: dict[str, float] = {}
    for rule in all_rules():
        if rule.get("record") == BUDGET_RECORD:
            service = rule["labels"]["service"]
            assert service not in budgets, f"duplicate budget for {service}"
            expr = rule["expr"].strip()
            assert expr.startswith("vector(") and expr.endswith(")"), expr
            budgets[service] = float(expr[len("vector(") : -1])
    return budgets


def test_every_catalog_service_has_its_own_error_budget_rule() -> None:
    assert rule_budgets() == catalog_budgets()
    assert rule_budgets()["payments-api"] == pytest.approx(0.005)


@pytest.mark.parametrize(
    ("alert", "multiplier"),
    [("AvailabilitySLOBurnRateFast", "14.4"), ("AvailabilitySLOBurnRateSlow", "3")],
)
def test_burn_rate_alerts_use_the_per_service_budget(alert: str, multiplier: str) -> None:
    (rule,) = [r for r in all_rules() if r.get("alert") == alert]
    expr = " ".join(rule["expr"].split())
    assert f"> on (service) ({multiplier} * {BUDGET_RECORD})" in expr
    assert "0.001)" not in expr.replace(
        "clamp_min(service:http_requests:rate5m, 0.001)", ""
    ).replace("clamp_min(sum by (service) (rate(http_server_requests_total[1h])), 0.001)", ""), (
        "burn-rate threshold must not hard-code a 99.9% budget"
    )
    assert rule["labels"]["slo"] == "availability"
