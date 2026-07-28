from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from aiops.kubernetes_executor import KubernetesExecutor
from aiops.models import AutomationDecision


def decision(action: str, target: str = "orders-api") -> AutomationDecision:
    return AutomationDecision(
        incident_id="INC-TEST",
        action=action,
        target=target,
        mode="active",
        approved=True,
        reason="test",
        risk="medium",
    )


def test_scale_action_is_bounded() -> None:
    api = Mock()
    api.read_namespaced_deployment_scale.return_value = SimpleNamespace(
        spec=SimpleNamespace(replicas=3)
    )
    executor = KubernetesExecutor(apps_api=api)
    assert executor(decision("scale")) == "scaled-3-to-4"
    api.patch_namespaced_deployment_scale.assert_called_once_with(
        name="orders-api",
        namespace="huawei-aiops",
        body={"spec": {"replicas": 4}},
    )


def test_runtime_flag_patches_consumer() -> None:
    api = Mock()
    executor = KubernetesExecutor(apps_api=api)
    outcome = executor(decision("enable-circuit-breaker", "catalog-api"))
    assert outcome == "enabled-catalog_circuit_breaker"
    call = api.patch_namespaced_deployment.call_args
    assert call.kwargs["name"] == "orders-api"
    assert call.kwargs["namespace"] == "huawei-aiops"


def test_unknown_target_and_action_are_blocked() -> None:
    executor = KubernetesExecutor(apps_api=Mock())
    with pytest.raises(ValueError, match="allow-listed"):
        executor(decision("scale", "untrusted"))
    with pytest.raises(ValueError, match="unsupported"):
        executor(decision("delete", "orders-api"))
