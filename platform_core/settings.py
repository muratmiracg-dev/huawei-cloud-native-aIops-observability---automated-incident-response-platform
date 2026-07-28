from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "local"
    log_level: str = "INFO"
    service_name: str = "unknown-service"
    service_version: str = "1.0.0"
    otel_service_namespace: str = "huawei-aiops"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    enable_tracing: bool = False
    enable_fault_injection: bool = False
    incident_automation_mode: Literal["disabled", "dry-run", "active"] = "dry-run"
    incident_cooldown_seconds: int = 300
    catalog_url: str = "http://localhost:8001"
    payments_url: str = "http://localhost:8003"


@lru_cache
def get_settings() -> Settings:
    return Settings()
