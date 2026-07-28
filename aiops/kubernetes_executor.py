from datetime import UTC, datetime
from typing import Any

from aiops.models import AutomationDecision
from kubernetes import client, config


class KubernetesExecutor:
    """Executes a deliberately small, namespace-scoped set of reversible actions."""

    def __init__(
        self,
        *,
        namespace: str = "huawei-aiops",
        allowed_targets: set[str] | None = None,
        apps_api: Any | None = None,
    ) -> None:
        self.namespace = namespace
        self.allowed_targets = allowed_targets or {
            "catalog-api",
            "orders-api",
            "payments-api",
            "aiops-api",
        }
        if apps_api is None:
            config.load_incluster_config()
            apps_api = client.AppsV1Api()
        self.apps_api = apps_api

    def __call__(self, decision: AutomationDecision) -> str:
        if decision.target not in self.allowed_targets:
            raise ValueError("automation target is not allow-listed")
        if decision.action == "scale":
            return self._scale(decision.target)
        if decision.action == "enable-circuit-breaker":
            return self._set_runtime_flag(
                deployment="orders-api",
                flag="CATALOG_CIRCUIT_BREAKER",
            )
        if decision.action == "enable-degraded-mode":
            return self._set_runtime_flag(
                deployment="orders-api",
                flag="PAYMENTS_DEGRADED_MODE",
            )
        raise ValueError(f"unsupported active automation action: {decision.action}")

    def _scale(self, deployment: str) -> str:
        scale = self.apps_api.read_namespaced_deployment_scale(
            name=deployment,
            namespace=self.namespace,
        )
        current = int(scale.spec.replicas or 1)
        desired = min(current + 1, 12)
        if desired == current:
            return "at-max-capacity"
        self.apps_api.patch_namespaced_deployment_scale(
            name=deployment,
            namespace=self.namespace,
            body={"spec": {"replicas": desired}},
        )
        return f"scaled-{current}-to-{desired}"

    def _set_runtime_flag(self, *, deployment: str, flag: str) -> str:
        timestamp = datetime.now(UTC).isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "aiops.huawei.com/last-action": timestamp,
                            "aiops.huawei.com/runtime-flag": flag,
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": deployment,
                                "env": [{"name": flag, "value": "true"}],
                            }
                        ]
                    },
                }
            }
        }
        self.apps_api.patch_namespaced_deployment(
            name=deployment,
            namespace=self.namespace,
            body=body,
        )
        return f"enabled-{flag.lower()}"
