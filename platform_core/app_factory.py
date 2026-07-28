from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from platform_core.faults import FaultController, FaultProfile
from platform_core.logging import configure_logging
from platform_core.middleware import ObservabilityMiddleware
from platform_core.settings import Settings
from platform_core.telemetry import configure_tracing


class FaultRequest(BaseModel):
    latency_ms: int = Field(default=0, ge=0, le=30_000)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)


def create_service_app(
    *,
    title: str,
    description: str,
    settings: Settings,
    lifespan: Any | None = None,
) -> FastAPI:
    configure_logging(settings.log_level)
    controller = FaultController()

    if lifespan is None:

        @asynccontextmanager
        async def default_lifespan(_: FastAPI) -> AsyncIterator[None]:
            yield

        lifespan = default_lifespan

    app = FastAPI(
        title=title,
        description=description,
        version=settings.service_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.state.fault_controller = controller
    app.add_middleware(
        ObservabilityMiddleware,
        service_name=settings.service_name,
        fault_controller=controller,
    )

    @app.get("/health/live", tags=["platform"])
    async def liveness() -> dict[str, str]:
        return {"status": "alive", "service": settings.service_name}

    @app.get("/health/ready", tags=["platform"])
    async def readiness() -> dict[str, str]:
        return {"status": "ready", "service": settings.service_name}

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/internal/faults", tags=["resilience"])
    async def current_fault() -> FaultProfile:
        return controller.current()

    @app.put("/internal/faults", tags=["resilience"])
    async def set_fault(payload: FaultRequest) -> FaultProfile:
        if not settings.enable_fault_injection:
            raise HTTPException(status_code=403, detail="fault injection is disabled")
        return controller.set(FaultProfile(**payload.model_dump()))

    @app.delete("/internal/faults", tags=["resilience"])
    async def reset_fault() -> FaultProfile:
        if not settings.enable_fault_injection:
            raise HTTPException(status_code=403, detail="fault injection is disabled")
        return controller.reset()

    configure_tracing(
        app,
        service_name=settings.service_name,
        service_version=settings.service_version,
        namespace=settings.otel_service_namespace,
        endpoint=settings.otel_exporter_otlp_endpoint,
        enabled=settings.enable_tracing,
    )
    return app
