from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorBudget:
    objective: float
    total_events: int
    bad_events: int
    allowed_bad_events: float
    remaining_bad_events: float
    remaining_percent: float
    burn_rate: float


def calculate_error_budget(
    *,
    objective: float,
    total_events: int,
    bad_events: int,
) -> ErrorBudget:
    if not 0 < objective < 1:
        raise ValueError("objective must be between 0 and 1")
    if total_events <= 0:
        raise ValueError("total_events must be positive")
    if not 0 <= bad_events <= total_events:
        raise ValueError("bad_events must be between 0 and total_events")

    allowed = total_events * (1 - objective)
    remaining = allowed - bad_events
    remaining_percent = 100 * remaining / allowed
    burn_rate = bad_events / allowed
    return ErrorBudget(
        objective=objective,
        total_events=total_events,
        bad_events=bad_events,
        allowed_bad_events=round(allowed, 3),
        remaining_bad_events=round(remaining, 3),
        remaining_percent=round(remaining_percent, 3),
        burn_rate=round(burn_rate, 3),
    )
