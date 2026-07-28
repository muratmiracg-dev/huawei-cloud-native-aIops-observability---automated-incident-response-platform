import pytest

from aiops.slo import calculate_error_budget


def test_error_budget_calculation() -> None:
    budget = calculate_error_budget(
        objective=0.999,
        total_events=1_000_000,
        bad_events=250,
    )
    assert budget.allowed_bad_events == pytest.approx(1000)
    assert budget.remaining_bad_events == pytest.approx(750)
    assert budget.remaining_percent == pytest.approx(75)
    assert budget.burn_rate == pytest.approx(0.25)


@pytest.mark.parametrize(
    ("objective", "total", "bad"),
    [(1.0, 100, 0), (0.0, 100, 0), (0.99, 0, 0), (0.99, 10, 11), (0.99, 10, -1)],
)
def test_error_budget_validation(objective: float, total: int, bad: int) -> None:
    with pytest.raises(ValueError):
        calculate_error_budget(objective=objective, total_events=total, bad_events=bad)
