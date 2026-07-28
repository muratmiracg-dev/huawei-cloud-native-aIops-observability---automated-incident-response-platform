import pytest

from platform_core.faults import FaultController, FaultProfile


def test_fault_profile_validates_boundaries() -> None:
    assert FaultProfile(latency_ms=0, error_rate=0).error_rate == 0
    assert FaultProfile(latency_ms=100, error_rate=1).latency_ms == 100
    with pytest.raises(ValueError):
        FaultProfile(latency_ms=-1)
    with pytest.raises(ValueError):
        FaultProfile(error_rate=1.1)


def test_fault_controller_set_and_reset() -> None:
    controller = FaultController()
    assert controller.current() == FaultProfile()
    configured = controller.set(FaultProfile(latency_ms=25, error_rate=0.2))
    assert configured.latency_ms == 25
    assert controller.reset() == FaultProfile()
