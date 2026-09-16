import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import ClassVar

from aiops.models import AutomationDecision, Incident
from platform_core.metrics import AUTOMATION_ACTIONS

LOGGER = logging.getLogger(__name__)


class IncidentPolicy:
    ACTIONS: ClassVar[dict[str, tuple[str, str, float]]] = {
        "CPU saturation and insufficient replica capacity": (
            "scale",
            "medium",
            0.78,
        ),
        "Catalog dependency degradation": (
            "enable-circuit-breaker",
            "low",
            0.76,
        ),
        "Payment provider failure": (
            "enable-degraded-mode",
            "medium",
            0.82,
        ),
        "Crash-loop or unstable application release": (
            "rollback",
            "high",
            0.90,
        ),
        "Database connection pool exhaustion": (
            "scale",
            "medium",
            0.82,
        ),
    }

    def evaluate(self, incident: Incident, mode: str) -> AutomationDecision:
        if not incident.hypotheses:
            return AutomationDecision(
                incident_id=incident.incident_id,
                action="none",
                target="unknown",
                mode=mode,
                approved=False,
                reason="No sufficiently supported root-cause hypothesis.",
                risk="none",
            )

        hypothesis = incident.hypotheses[0]
        action, risk, threshold = self.ACTIONS.get(
            hypothesis.cause,
            ("notify", "low", 0.65),
        )
        confidence_pass = hypothesis.confidence >= threshold
        safe_for_active = risk in {"low", "medium"}
        valid_mode = mode in {"disabled", "dry-run", "active"}
        approved = (
            valid_mode
            and confidence_pass
            and mode != "disabled"
            and (mode == "dry-run" or safe_for_active)
        )
        if not valid_mode:
            reason = "Unknown automation mode; action blocked by fail-closed guardrail."
        elif mode == "disabled":
            reason = "Automation is disabled by configuration."
        elif not confidence_pass:
            reason = f"Confidence {hypothesis.confidence:.2f} is below {threshold:.2f}."
        elif mode == "active" and not safe_for_active:
            reason = "High-risk actions require human approval."
        else:
            reason = "Policy, confidence, and risk guardrails passed."

        return AutomationDecision(
            incident_id=incident.incident_id,
            action=action,
            target=hypothesis.affected_service,
            mode=mode,
            approved=approved,
            reason=reason,
            risk=risk,
        )


class CooldownRegistry:
    def __init__(self, cooldown_seconds: int = 300) -> None:
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._last_action: dict[tuple[str, str], datetime] = {}

    def allow(self, target: str, action: str, now: datetime | None = None) -> bool:
        now = now or datetime.now(UTC)
        key = (target, action)
        previous = self._last_action.get(key)
        if previous and now - previous < self.cooldown:
            return False
        self._last_action[key] = now
        return True


class AuditWriter:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path

    def write(self, decision: AutomationDecision, outcome: str) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {**decision.model_dump(mode="json"), "outcome": outcome}
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")


class IncidentOrchestrator:
    def __init__(
        self,
        *,
        mode: str = "dry-run",
        cooldown_seconds: int = 300,
        executor: Callable[[AutomationDecision], str] | None = None,
        audit_writer: AuditWriter | None = None,
    ) -> None:
        self.mode = mode
        self.policy = IncidentPolicy()
        self.cooldowns = CooldownRegistry(cooldown_seconds)
        self.executor = executor or self._dry_run_executor
        self.audit = audit_writer or AuditWriter()

    @staticmethod
    def _dry_run_executor(decision: AutomationDecision) -> str:
        LOGGER.warning(
            "Dry-run automation decision",
            extra={
                "incident_id": decision.incident_id,
                "action": decision.action,
                "target": decision.target,
            },
        )
        return "simulated"

    def handle(self, incident: Incident) -> tuple[AutomationDecision, str]:
        decision = self.policy.evaluate(incident, self.mode)
        if not decision.approved:
            outcome = "blocked"
        elif not self.cooldowns.allow(decision.target, decision.action):
            decision.approved = False
            decision.reason = "Action blocked by cooldown guardrail."
            outcome = "cooldown"
        else:
            outcome = self.executor(decision)

        AUTOMATION_ACTIONS.labels(
            action=decision.action,
            mode=decision.mode,
            outcome=outcome,
        ).inc()
        self.audit.write(decision, outcome)
        return decision, outcome
