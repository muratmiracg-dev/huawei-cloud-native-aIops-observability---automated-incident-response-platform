#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def validate_required_paths() -> None:
    required = [
        "README.md",
        "LICENSE",
        "SECURITY.md",
        "docker-compose.yml",
        "helm/huawei-aiops/Chart.yaml",
        "terraform/versions.tf",
        "kubernetes/base/kustomization.yaml",
        "observability/slos/service-level-objectives.yaml",
        "docs/architecture.md",
        "docs/runbooks/RB-001-capacity-saturation.md",
        "presentations/Huawei_Cloud_AIOps_Executive_Deck_EN.pptx",
        "presentations/Huawei_Cloud_AIOps_Yonetici_Sunumu_TR.pptx",
        "reports/Huawei_Cloud_AIOps_Executive_Report.pdf",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    if missing:
        fail(f"required repository paths are missing: {missing}")


def validate_yaml() -> None:
    paths = [
        *ROOT.glob("kubernetes/**/*.yaml"),
        *ROOT.glob("observability/**/*.yaml"),
        *ROOT.glob("observability/**/*.yml"),
        ROOT / "docker-compose.yml",
    ]
    for path in paths:
        with path.open(encoding="utf-8") as stream:
            list(yaml.safe_load_all(stream))


def validate_json() -> None:
    dashboards = sorted((ROOT / "observability/grafana/dashboards").glob("*.json"))
    if len(dashboards) < 3:
        fail("at least three Grafana dashboards are required")
    uids: set[str] = set()
    panel_count = 0
    for path in dashboards:
        payload = json.loads(path.read_text(encoding="utf-8"))
        uid = payload.get("uid")
        if not uid or uid in uids:
            fail(f"Grafana dashboard UID is missing or duplicated: {path}")
        uids.add(uid)
        panels = payload.get("panels", [])
        panel_count += len(panels)
        if len(panels) < 6:
            fail(f"dashboard must contain at least six panels: {path}")
    if panel_count < 20:
        fail("Grafana dashboard suite must contain at least 20 panels")


def validate_kubernetes_security() -> None:
    deployments_path = ROOT / "kubernetes/base/deployments.yaml"
    docs = list(yaml.safe_load_all(deployments_path.read_text(encoding="utf-8")))
    deployments = [doc for doc in docs if doc and doc.get("kind") == "Deployment"]
    if len(deployments) != 4:
        fail("exactly four base Kubernetes deployments are expected")
    for deployment in deployments:
        name = deployment["metadata"]["name"]
        spec = deployment["spec"]["template"]["spec"]
        if not spec.get("securityContext", {}).get("runAsNonRoot"):
            fail(f"{name}: pod must run as non-root")
        for container in spec["containers"]:
            security = container.get("securityContext", {})
            if not security.get("readOnlyRootFilesystem"):
                fail(f"{name}: read-only root filesystem is required")
            if security.get("allowPrivilegeEscalation") is not False:
                fail(f"{name}: privilege escalation must be disabled")
            if not container.get("readinessProbe") or not container.get("livenessProbe"):
                fail(f"{name}: health probes are required")
            resources = container.get("resources", {})
            if not resources.get("requests") or not resources.get("limits"):
                fail(f"{name}: resource requests and limits are required")


def validate_runbooks() -> None:
    runbooks = sorted((ROOT / "docs/runbooks").glob("RB-*.md"))
    if len(runbooks) < 6:
        fail("at least six operational runbooks are required")
    for path in runbooks:
        text = path.read_text(encoding="utf-8")
        for section in (
            "## Trigger",
            "## Diagnosis",
            "## Automated action",
            "## Rollback",
            "## Escalation",
        ):
            if section not in text:
                fail(f"{path}: missing section {section}")


def validate_no_embedded_secrets() -> None:
    banned = (
        "AK" + "IA",
        "BEGIN PRIVATE" + " KEY",
        "password:" + " admin",
        "access_" + "key =",
    )
    text_paths = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and ".venv" not in path.parts
        and path.suffix in {".py", ".yaml", ".yml", ".tf", ".md", ".json", ".txt", ".example"}
    ]
    for path in text_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in banned:
            if token.lower() in text.lower():
                fail(f"potential embedded secret pattern {token!r} in {path}")


def main() -> int:
    checks = [
        validate_required_paths,
        validate_yaml,
        validate_json,
        validate_kubernetes_security,
        validate_runbooks,
        validate_no_embedded_secrets,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    print(f"Repository validation passed ({len(checks)} checks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
