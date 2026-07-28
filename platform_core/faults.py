from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class FaultProfile:
    latency_ms: int = 0
    error_rate: float = 0.0

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if not 0.0 <= self.error_rate <= 1.0:
            raise ValueError("error_rate must be between 0 and 1")


class FaultController:
    def __init__(self) -> None:
        self._profile = FaultProfile()
        self._lock = Lock()

    def current(self) -> FaultProfile:
        with self._lock:
            return self._profile

    def set(self, profile: FaultProfile) -> FaultProfile:
        with self._lock:
            self._profile = profile
            return self._profile

    def reset(self) -> FaultProfile:
        return self.set(FaultProfile())
