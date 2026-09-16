from datetime import UTC, datetime, timedelta

from aiops.incident_response import (
    AuditWriter,
    CooldownRegistry,
    IncidentOrchestrator,
    IncidentPolicy,
)
from aiops.models import Incident, RootCauseHypothesis, Severity


def incident(*, cause: str, confidence: float = 0.95) -> Incident:
    return Incident(
        incident_id="INC-TEST",
        title="Test incident",
        severity=Severity.CRITICAL,
        affected_services=["orders-api"],
        hypotheses=[
            RootCauseHypothesis(
                rank=1,
                cause=cause,
                affected_service="orders-api",
                confidence=confidence,
                evidence=["test evidence"],
                recommended_runbook="RB-TEST",
            )
        ],
    )


def test_dry_run_approves_supported_action() -> None:
    decision = IncidentPolicy().evaluate(
        incident(cause="CPU saturation and insufficient replica capacity"),
        "dry-run",
    )
    assert decision.approved is True
    assert decision.action == "scale"


def test_active_mode_blocks_high_risk_rollback() -> None:
    decision = IncidentPolicy().evaluate(
        incident(cause="Crash-loop or unstable application release"),
        "active",
    )
    assert decision.approved is False
    assert decision.risk == "high"
    assert "human approval" in decision.reason


def test_low_confidence_is_blocked() -> None:
    decision = IncidentPolicy().evaluate(
        incident(
            cause="CPU saturation and insufficient replica capacity",
            confidence=0.2,
        ),
        "dry-run",
    )
    assert decision.approved is False


def test_disabled_and_empty_hypothesis_decisions() -> None:
    empty = Incident(
        incident_id="INC-EMPTY",
        title="No cause",
        severity=Severity.WARNING,
        affected_services=["orders-api"],
        hypotheses=[],
    )
    assert IncidentPolicy().evaluate(empty, "dry-run").action == "none"
    disabled = IncidentPolicy().evaluate(
        incident(cause="CPU saturation and insufficient replica capacity"),
        "disabled",
    )
    assert disabled.approved is False
    assert "disabled" in disabled.reason


def test_unknown_mode_fails_closed() -> None:
    decision = IncidentPolicy().evaluate(
        incident(cause="CPU saturation and insufficient replica capacity"),
        "actve",
    )
    assert decision.approved is False
    assert "fail-closed" in decision.reason


def test_unknown_mode_never_reaches_executor() -> None:
    calls: list[str] = []

    def executor(decision) -> str:
        calls.append(decision.action)
        return "executed"

    decision, outcome = IncidentOrchestrator(
        mode="actve",
        executor=executor,
    ).handle(incident(cause="CPU saturation and insufficient replica capacity"))
    assert decision.approved is False
    assert outcome == "blocked"
    assert calls == []


def test_cooldown_registry() -> None:
    registry = CooldownRegistry(cooldown_seconds=60)
    now = datetime.now(UTC)
    assert registry.allow("orders-api", "scale", now) is True
    assert registry.allow("orders-api", "scale", now + timedelta(seconds=30)) is False
    assert registry.allow("orders-api", "scale", now + timedelta(seconds=61)) is True


def test_orchestrator_executes_once_then_blocks_on_cooldown() -> None:
    calls: list[str] = []

    def executor(decision) -> str:
        calls.append(decision.action)
        return "executed"

    orchestrator = IncidentOrchestrator(
        mode="dry-run",
        cooldown_seconds=300,
        executor=executor,
    )
    first_decision, first_outcome = orchestrator.handle(
        incident(cause="CPU saturation and insufficient replica capacity")
    )
    second_decision, second_outcome = orchestrator.handle(
        incident(cause="CPU saturation and insufficient replica capacity")
    )
    assert first_decision.approved is True
    assert first_outcome == "executed"
    assert second_decision.approved is False
    assert second_outcome == "cooldown"
    assert calls == ["scale"]


def test_audit_writer_persists_decision(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    orchestrator = IncidentOrchestrator(
        mode="dry-run",
        audit_writer=AuditWriter(path),
    )
    decision, outcome = orchestrator.handle(
        incident(cause="CPU saturation and insufficient replica capacity")
    )
    assert decision.approved is True
    assert outcome == "simulated"
    text = path.read_text(encoding="utf-8")
    assert '"incident_id": "INC-TEST"' in text
    assert '"outcome": "simulated"' in text
